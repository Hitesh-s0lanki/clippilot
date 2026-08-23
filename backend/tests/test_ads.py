"""Ads as a first-class child of the campaign.

Covers what promoting the single "experience" to a one-to-many ``ads``
collection actually changed: per-ad names and statuses, the two-level delivery
rule, the CTA's default label, and what a viewer is allowed to open.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.core.security import DEV_USER_HEADER
from src.schemas.ad import MAX_ADS_PER_CAMPAIGN
from tests.conftest import OTHER_OWNER

SESSION = "session-ads-0001"


def _second_ad(name: str = "Cost of waiting") -> dict:
    return {
        "name": name,
        "video_url": "https://cdn.example.com/waiting.mp4",
        "headline": "Every month costs you",
        "description": "A paused SIP is a decision, even when it feels like a pause.",
        "cta": "BOOK_NOW",
        "personalised_message": "Hi {{customer_name}}, here is what the gap has cost.",
        "options": [
            {
                "position": 1,
                "label": "Book a call",
                "intent": "POSITIVE",
                "follow_up_type": "MESSAGE",
                "follow_up_message": "Booked - an advisor will confirm.",
            },
            {
                "position": 2,
                "label": "Not right now",
                "intent": "NEGATIVE",
                "follow_up_type": "MESSAGE",
                "follow_up_message": "Understood.",
            },
        ],
    }


class TestAdCrud:
    def test_a_campaign_is_created_with_its_ads(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        body = owner_client.post(f"{api}/campaigns", json=draft_payload).json()

        assert len(body["ads"]) == 1
        assert body["ads"][0]["name"] == "Investment Opportunity - advisor call"
        assert body["ads"][0]["status"] == "DRAFT"

    def test_a_second_ad_is_added_to_a_campaign(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]

        created = owner_client.post(f"{api}/campaigns/{campaign_id}/ads", json=_second_ad())

        assert created.status_code == 201
        assert created.json()["cta"] == "BOOK_NOW"
        assert owner_client.get(f"{api}/campaigns/{campaign_id}/ads").json()["total"] == 2

    def test_ad_names_are_unique_within_a_campaign(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        owner_client.post(f"{api}/campaigns/{campaign_id}/ads", json=_second_ad())

        clash = owner_client.post(
            f"{api}/campaigns/{campaign_id}/ads", json=_second_ad("cost of WAITING")
        )

        assert clash.status_code == 409
        assert clash.json()["error"]["code"] == "AD_NAME_TAKEN"

    def test_the_same_ad_name_is_free_in_another_campaign(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        first = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        second = owner_client.post(
            f"{api}/campaigns", json={**draft_payload, "name": "Another campaign", "ads": []}
        ).json()["id"]
        owner_client.post(f"{api}/campaigns/{first}/ads", json=_second_ad())

        response = owner_client.post(f"{api}/campaigns/{second}/ads", json=_second_ad())

        assert response.status_code == 201

    def test_a_partial_update_leaves_the_rest_of_the_ad_alone(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        ad_id = owner_client.get(f"{api}/campaigns/{campaign_id}").json()["ads"][0]["id"]

        updated = owner_client.patch(
            f"{api}/campaigns/{campaign_id}/ads/{ad_id}", json={"headline": "Reworked"}
        ).json()

        assert updated["headline"] == "Reworked"
        assert updated["video_url"] == "https://cdn.example.com/investment.mp4"
        assert len(updated["options"]) == 2

    def test_another_users_campaign_is_a_404_not_a_403(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        owner_client.headers[DEV_USER_HEADER] = OTHER_OWNER

        response = owner_client.get(f"{api}/campaigns/{campaign_id}/ads")

        assert response.status_code == 404

    def test_an_unknown_ad_is_a_404(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]

        response = owner_client.get(f"{api}/campaigns/{campaign_id}/ads/nope")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "AD_NOT_FOUND"


class TestCallToAction:
    def test_the_cta_supplies_the_positive_buttons_label(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        """Choosing a CTA should not also be a copywriting task."""
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]

        ad = owner_client.post(
            f"{api}/campaigns/{campaign_id}/ads",
            json={
                "name": "Unlabelled buttons",
                "cta": "BOOK_NOW",
                "options": [
                    {"position": 1, "intent": "POSITIVE"},
                    {"position": 2, "intent": "NEGATIVE"},
                ],
            },
        ).json()

        assert [option["label"] for option in ad["options"]] == ["Book now", "Not right now"]

    def test_an_explicit_label_wins_over_the_cta(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]

        ad = owner_client.post(
            f"{api}/campaigns/{campaign_id}/ads",
            json={
                "name": "Explicit labels",
                "cta": "BOOK_NOW",
                "options": [{"position": 1, "intent": "POSITIVE", "label": "Grab a slot"}],
            },
        ).json()

        assert ad["options"][0]["label"] == "Grab a slot"


class TestAdLifecycle:
    def test_an_incomplete_ad_cannot_be_switched_on(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        ad_id = owner_client.post(
            f"{api}/campaigns/{campaign_id}/ads", json={"name": "Half built"}
        ).json()["id"]

        response = owner_client.post(
            f"{api}/campaigns/{campaign_id}/ads/{ad_id}/status", json={"status": "ACTIVE"}
        )

        assert response.status_code == 422
        fields = {d["field"] for d in response.json()["error"]["details"]}
        assert "video_url" in fields
        assert "personalised_message" in fields

    def test_an_incomplete_ad_reports_its_own_blockers_on_read(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        ad = owner_client.post(
            f"{api}/campaigns/{campaign_id}/ads", json={"name": "Half built"}
        ).json()

        assert "video_url" in ad["blockers"]
        assert ad["effective_status"] == "INCOMPLETE"

    def test_publishing_switches_on_the_ads_that_are_ready(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        """Otherwise the common path - one campaign, one ad, Publish - 403s everyone."""
        assert published_campaign["ads"][0]["status"] == "ACTIVE"
        assert published_campaign["ads"][0]["effective_status"] == "ACTIVE"

    def test_publishing_does_not_resurrect_a_paused_ad(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        """Pausing one creative is a decision about that creative."""
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        second = owner_client.post(f"{api}/campaigns/{campaign_id}/ads", json=_second_ad()).json()
        owner_client.post(
            f"{api}/campaigns/{campaign_id}/ads/{second['id']}/status", json={"status": "ACTIVE"}
        )
        owner_client.post(
            f"{api}/campaigns/{campaign_id}/ads/{second['id']}/status", json={"status": "PAUSED"}
        )

        body = owner_client.post(
            f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"}
        ).json()

        by_name = {ad["name"]: ad["status"] for ad in body["ads"]}
        assert by_name["Investment Opportunity - advisor call"] == "ACTIVE"
        assert by_name["Cost of waiting"] == "PAUSED"

    def test_an_active_ad_under_a_paused_campaign_reports_campaign_paused(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        """The ad is faultless and still shows nothing. Say which level is at fault."""
        campaign_id = published_campaign["id"]

        owner_client.post(f"{api}/campaigns/{campaign_id}/status", json={"status": "PAUSED"})
        body = owner_client.get(f"{api}/campaigns/{campaign_id}").json()

        assert body["ads"][0]["status"] == "ACTIVE"
        assert body["ads"][0]["effective_status"] == "CAMPAIGN_PAUSED"

    def test_an_illegal_ad_transition_is_a_409(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        ad_id = owner_client.get(f"{api}/campaigns/{campaign_id}").json()["ads"][0]["id"]
        owner_client.post(
            f"{api}/campaigns/{campaign_id}/ads/{ad_id}/status", json={"status": "ARCHIVED"}
        )

        response = owner_client.post(
            f"{api}/campaigns/{campaign_id}/ads/{ad_id}/status", json={"status": "ACTIVE"}
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "AD_INVALID_TRANSITION"

    def test_a_campaign_with_no_complete_ad_cannot_publish(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        payload = {**draft_payload, "ads": [{"name": "Half built"}]}
        campaign_id = owner_client.post(f"{api}/campaigns", json=payload).json()["id"]

        response = owner_client.post(
            f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"}
        )

        assert response.status_code == 422
        fields = {d["field"] for d in response.json()["error"]["details"]}
        # The campaign-level blocker, plus the offending ad's own fields.
        assert "ads" in fields
        assert "ads.0.video_url" in fields

    def test_one_finished_ad_is_enough_to_publish(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        """A half-written second creative must not block the first from running."""
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        owner_client.post(f"{api}/campaigns/{campaign_id}/ads", json={"name": "Work in progress"})

        response = owner_client.post(
            f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"}
        )

        assert response.status_code == 200


class TestAdDeletion:
    def test_an_untouched_ad_can_be_deleted(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        ad_id = owner_client.post(f"{api}/campaigns/{campaign_id}/ads", json=_second_ad()).json()[
            "id"
        ]

        assert owner_client.delete(f"{api}/campaigns/{campaign_id}/ads/{ad_id}").status_code == 204
        assert owner_client.get(f"{api}/campaigns/{campaign_id}/ads").json()["total"] == 1

    def test_an_ad_with_recorded_activity_cannot_be_deleted(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        """Its events carry the campaign's history."""
        campaign_id = published_campaign["id"]
        ad_id = published_campaign["ads"][0]["id"]

        anon = owner_client
        del anon.headers[DEV_USER_HEADER]
        anon.post(f"{api}/public/campaigns/{campaign_id}/views", json={"session_id": SESSION})
        anon.headers[DEV_USER_HEADER] = "user_test_owner"

        response = owner_client.delete(f"{api}/campaigns/{campaign_id}/ads/{ad_id}")

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "AD_LOCKED"


class TestViewerAccess:
    def test_a_viewer_opens_the_primary_ad_without_naming_one(
        self, client: TestClient, api: str, published_campaign: dict
    ) -> None:
        campaign_id = published_campaign["id"]

        body = client.get(f"{api}/public/campaigns/{campaign_id}").json()

        assert body["ad"]["id"] == published_campaign["ads"][0]["id"]
        assert body["ad"]["cta"] == "LEARN_MORE"
        assert body["ad"]["description"] == (
            "Reviewed by an advisor, matched to your risk profile."
        )

    def test_a_viewer_can_open_a_named_ad(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        second = owner_client.post(f"{api}/campaigns/{campaign_id}/ads", json=_second_ad()).json()
        owner_client.post(f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"})

        anon = owner_client
        del anon.headers[DEV_USER_HEADER]
        body = anon.get(f"{api}/public/campaigns/{campaign_id}?ad_id={second['id']}").json()

        assert body["ad"]["id"] == second["id"]
        assert body["ad"]["headline"] == "Every month costs you"

    def test_a_paused_ad_is_closed_even_inside_a_live_campaign(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        campaign_id = published_campaign["id"]
        ad_id = published_campaign["ads"][0]["id"]
        owner_client.post(
            f"{api}/campaigns/{campaign_id}/ads/{ad_id}/status", json={"status": "PAUSED"}
        )

        anon = owner_client
        del anon.headers[DEV_USER_HEADER]
        response = anon.get(f"{api}/public/campaigns/{campaign_id}?ad_id={ad_id}")

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "AD_NOT_LIVE"

    def test_the_owner_can_preview_a_draft_ad(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        """A draft ad must be checkable before it is switched on."""
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        second = owner_client.post(f"{api}/campaigns/{campaign_id}/ads", json=_second_ad()).json()

        body = owner_client.get(
            f"{api}/campaigns/{campaign_id}/preview?ad_id={second['id']}"
        ).json()

        assert body["ad"]["id"] == second["id"]


class TestAdAnalytics:
    def test_events_are_attributed_to_the_ad_they_happened_on(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        campaign_id = published_campaign["id"]
        ad_id = published_campaign["ads"][0]["id"]
        option_id = published_campaign["ads"][0]["options"][0]["id"]

        anon = owner_client
        del anon.headers[DEV_USER_HEADER]
        anon.post(f"{api}/public/campaigns/{campaign_id}/views", json={"session_id": SESSION})
        anon.post(
            f"{api}/public/campaigns/{campaign_id}/responses",
            json={"session_id": SESSION, "option_id": option_id},
        )
        anon.headers[DEV_USER_HEADER] = "user_test_owner"

        analytics = owner_client.get(f"{api}/campaigns/{campaign_id}/analytics").json()

        assert len(analytics["by_ad"]) == 1
        row = analytics["by_ad"][0]
        assert row["ad_id"] == ad_id
        assert row["views"] == 1
        assert row["interactions"] == 1
        assert row["share_of_views"] == 1.0
        assert all(option["ad_id"] == ad_id for option in analytics["by_option"])

    def test_an_ad_with_no_activity_still_gets_a_row(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        campaign_id = published_campaign["id"]
        owner_client.post(f"{api}/campaigns/{campaign_id}/ads", json=_second_ad())

        analytics = owner_client.get(f"{api}/campaigns/{campaign_id}/analytics").json()

        assert len(analytics["by_ad"]) == 2
        assert analytics["by_ad"][1]["views"] == 0


class TestAdsLibraryWithManyAds:
    def test_every_live_ad_gets_its_own_card(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        """One card per campaign would silently hide all but the first creative."""
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        owner_client.post(f"{api}/campaigns/{campaign_id}/ads", json=_second_ad())
        owner_client.post(f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"})

        anon = owner_client
        del anon.headers[DEV_USER_HEADER]
        items = anon.get(f"{api}/public/campaigns").json()["items"]

        assert len(items) == 2
        assert {item["ad_name"] for item in items} == {
            "Investment Opportunity - advisor call",
            "Cost of waiting",
        }
        assert all(item["campaign_id"] == campaign_id for item in items)


class TestAdCeiling:
    """Five creatives per campaign, enforced server-side."""

    def test_the_sixth_ad_is_refused(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]

        # The fixture already contributes one, so four more fill the campaign.
        for index in range(2, MAX_ADS_PER_CAMPAIGN + 1):
            created = owner_client.post(
                f"{api}/campaigns/{campaign_id}/ads", json=_second_ad(f"Angle {index}")
            )
            assert created.status_code == 201, created.text

        response = owner_client.post(
            f"{api}/campaigns/{campaign_id}/ads", json=_second_ad("One too many")
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "AD_LIMIT_REACHED"
        assert str(MAX_ADS_PER_CAMPAIGN) in response.json()["error"]["message"]

    def test_creating_a_campaign_with_too_many_ads_is_refused(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        payload = {
            **draft_payload,
            "ads": [_second_ad(f"Angle {i}") for i in range(MAX_ADS_PER_CAMPAIGN + 1)],
        }

        response = owner_client.post(f"{api}/campaigns", json=payload)

        assert response.status_code == 422
        assert response.json()["error"]["details"][0]["field"] == "ads"

    def test_a_campaign_can_be_created_with_no_ads_at_all(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        """The builder creates the campaign first and adds creatives after."""
        response = owner_client.post(f"{api}/campaigns", json={**draft_payload, "ads": []})

        assert response.status_code == 201
        assert response.json()["ads"] == []
        assert "ads" in response.json()["publish_blockers"]
