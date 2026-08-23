"""End-to-end coverage of the brief's core user flow.

Dashboard -> create -> preview as a customer -> click a response -> the event
appears in analytics.
"""

from fastapi.testclient import TestClient

from src.core.security import DEV_USER_HEADER
from tests.conftest import OTHER_OWNER, OWNER

SESSION = "sess-abcdef123456"


class TestCoreFlow:
    def test_dashboard_starts_empty(self, owner_client: TestClient, api: str) -> None:
        body = owner_client.get(f"{api}/campaigns").json()

        assert body["items"] == []
        assert body["total"] == 0

    def test_full_journey(self, owner_client: TestClient, api: str, draft_payload: dict) -> None:
        # 1. Create.
        created = owner_client.post(f"{api}/campaigns", json=draft_payload)
        assert created.status_code == 201
        campaign = created.json()
        campaign_id = campaign["id"]

        assert campaign["status"] == "DRAFT"
        assert campaign["badge"] == "Draft"
        assert campaign["effective_status"] == "DRAFT"  # complete, so not INCOMPLETE
        assert campaign["publish_blockers"] == []

        # 2. It appears on the dashboard with the fields the brief mandates.
        row = owner_client.get(f"{api}/campaigns").json()["items"][0]
        assert row["name"] == "Investment Opportunity"
        assert row["badge"] == "Draft"
        assert row["metrics"]["views"] == 0
        assert row["metrics"]["interactions"] == 0
        assert row["created_at"]

        # 3. Publish.
        published = owner_client.post(
            f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"}
        )
        assert published.status_code == 200
        assert published.json()["status"] == "ACTIVE"
        assert published.json()["badge"] == "Published"
        assert published.json()["published_at"]

        # 4. A recipient opens it - no Clerk session involved.
        # The identity header is dropped rather than building a second client:
        # a second TestClient spins up its own event loop, and the engine pool
        # already holds connections bound to the first one.
        anon = owner_client
        del anon.headers[DEV_USER_HEADER]
        preview = anon.get(f"{api}/public/campaigns/{campaign_id}")
        assert preview.status_code == 200

        body = preview.json()
        assert body["customer_name"] == "Rahul"
        assert body["experience"]["personalised_message"] == (
            "Hi Rahul, we have identified an investment opportunity for you."
        )
        assert "{{customer_name}}" not in body["experience"]["personalised_message"]
        assert len(body["experience"]["options"]) == 2

        # 5. Record the view.
        view = anon.post(
            f"{api}/public/campaigns/{campaign_id}/views", json={"session_id": SESSION}
        )
        assert view.status_code == 201
        assert view.json()["deduplicated"] is False

        # 6. Click a response and get the follow-up.
        option_id = body["experience"]["options"][0]["id"]
        clicked = anon.post(
            f"{api}/public/campaigns/{campaign_id}/responses",
            json={"session_id": SESSION, "option_id": option_id},
        )
        assert clicked.status_code == 201
        assert clicked.json()["follow_up_message"] == ("Great, Rahul - an advisor will call.")

        # 7. The owner sees it in analytics.
        owner_client.headers[DEV_USER_HEADER] = OWNER
        analytics = owner_client.get(f"{api}/campaigns/{campaign_id}/analytics").json()
        assert analytics["views"] == 1
        assert analytics["interactions"] == 1
        assert analytics["interaction_rate"] == 1.0

        clicked_row = next(r for r in analytics["by_option"] if r["option_id"] == option_id)
        assert clicked_row["clicks"] == 1
        assert clicked_row["share"] == 1.0

        # A row exists for the option nobody chose.
        other_row = next(r for r in analytics["by_option"] if r["option_id"] != option_id)
        assert other_row["clicks"] == 0
        assert other_row["share"] == 0.0

        # 8. And on the dashboard row.
        row = owner_client.get(f"{api}/campaigns").json()["items"][0]
        assert row["metrics"]["views"] == 1
        assert row["metrics"]["interactions"] == 1


class TestPersonalisation:
    def test_missing_recipient_falls_back_rather_than_breaking(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        payload = {**draft_payload, "recipients": []}
        campaign_id = owner_client.post(f"{api}/campaigns", json=payload).json()["id"]

        preview = owner_client.get(f"{api}/campaigns/{campaign_id}/preview")

        assert preview.status_code == 200
        assert preview.json()["experience"]["personalised_message"].startswith("Hi there,")

    def test_unknown_variable_is_left_literal_and_reported(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        payload = {**draft_payload}
        payload["experience"] = {
            **draft_payload["experience"],
            "personalised_message": "Hi {{customer_name}}, ref {{account_number}}.",
        }
        campaign_id = owner_client.post(f"{api}/campaigns", json=payload).json()["id"]

        body = owner_client.get(f"{api}/campaigns/{campaign_id}/preview").json()

        assert body["experience"]["personalised_message"] == ("Hi Rahul, ref {{account_number}}.")
        assert body["unresolved_variables"] == ["account_number"]


class TestDeduplication:
    def test_repeat_view_returns_the_original_event(
        self, client: TestClient, api: str, published_campaign: dict
    ) -> None:
        campaign_id = published_campaign["id"]
        url = f"{api}/public/campaigns/{campaign_id}/views"

        first = client.post(url, json={"session_id": SESSION})
        second = client.post(url, json={"session_id": SESSION})

        assert first.status_code == 201
        assert second.status_code == 200
        assert second.json()["deduplicated"] is True
        assert second.json()["id"] == first.json()["id"]

    def test_repeat_response_cannot_switch_the_outcome(
        self, client: TestClient, api: str, published_campaign: dict
    ) -> None:
        campaign_id = published_campaign["id"]
        options = published_campaign["experience"]["options"]
        url = f"{api}/public/campaigns/{campaign_id}/responses"

        first = client.post(url, json={"session_id": SESSION, "option_id": options[0]["id"]})
        # Same session, deliberately clicking the *other* option.
        second = client.post(url, json={"session_id": SESSION, "option_id": options[1]["id"]})

        assert first.status_code == 201
        assert second.status_code == 200
        assert second.json()["event"]["deduplicated"] is True
        # The follow-up is the one for the option originally chosen.
        assert second.json()["follow_up_message"] == first.json()["follow_up_message"]

    def test_analytics_counts_a_deduplicated_session_once(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        campaign_id = published_campaign["id"]
        for _ in range(4):
            owner_client.post(
                f"{api}/public/campaigns/{campaign_id}/views",
                json={"session_id": SESSION},
            )

        analytics = owner_client.get(f"{api}/campaigns/{campaign_id}/analytics").json()
        assert analytics["views"] == 1

    def test_separate_sessions_count_separately(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        campaign_id = published_campaign["id"]
        for suffix in ("aaa11111", "bbb22222", "ccc33333"):
            owner_client.post(
                f"{api}/public/campaigns/{campaign_id}/views",
                json={"session_id": f"sess-{suffix}"},
            )

        analytics = owner_client.get(f"{api}/campaigns/{campaign_id}/analytics").json()
        assert analytics["views"] == 3
        assert analytics["unique_viewers"] == 3


class TestOwnership:
    def test_another_user_cannot_see_the_campaign(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        owner_client.headers[DEV_USER_HEADER] = OTHER_OWNER

        response = owner_client.get(f"{api}/campaigns/{published_campaign['id']}")

        # 404 rather than 403, so ids cannot be probed for existence.
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CAMPAIGN_NOT_FOUND"

    def test_another_user_sees_an_empty_dashboard(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        owner_client.headers[DEV_USER_HEADER] = OTHER_OWNER

        assert owner_client.get(f"{api}/campaigns").json()["total"] == 0

    def test_owned_routes_require_an_identity(self, client: TestClient, api: str) -> None:
        response = client.get(f"{api}/campaigns")

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"

    def test_the_recipient_route_does_not(
        self, client: TestClient, api: str, published_campaign: dict
    ) -> None:
        response = client.get(f"{api}/public/campaigns/{published_campaign['id']}")

        assert response.status_code == 200
