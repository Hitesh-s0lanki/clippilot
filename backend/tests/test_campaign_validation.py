"""Validation, the publish contract and lifecycle transitions."""

from fastapi.testclient import TestClient


class TestDraftValidation:
    def test_a_draft_needs_only_a_name(self, owner_client: TestClient, api: str) -> None:
        response = owner_client.post(f"{api}/campaigns", json={"name": "Bare draft"})

        assert response.status_code == 201
        assert response.json()["effective_status"] == "INCOMPLETE"

    def test_name_is_required(self, owner_client: TestClient, api: str) -> None:
        response = owner_client.post(f"{api}/campaigns", json={})

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_duplicate_name_is_rejected_case_insensitively(
        self, owner_client: TestClient, api: str
    ) -> None:
        owner_client.post(f"{api}/campaigns", json={"name": "Investment Opportunity"})
        response = owner_client.post(f"{api}/campaigns", json={"name": "investment opportunity"})

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "CAMPAIGN_NAME_TAKEN"

    def test_unknown_fields_are_rejected(self, owner_client: TestClient, api: str) -> None:
        response = owner_client.post(f"{api}/campaigns", json={"name": "X", "sneaky": "value"})

        assert response.status_code == 422

    def test_owner_cannot_be_set_by_the_client(self, owner_client: TestClient, api: str) -> None:
        # owner_user_id is taken from the Clerk session, never the payload.
        response = owner_client.post(
            f"{api}/campaigns", json={"name": "X", "owner_user_id": "user_someone_else"}
        )

        assert response.status_code == 422

    def test_insecure_video_url_is_rejected(self, owner_client: TestClient, api: str) -> None:
        response = owner_client.post(
            f"{api}/campaigns",
            json={
                "name": "Insecure",
                "ads": [{"name": "Ad 1", "video_url": "http://cdn.example.com/a.mp4"}],
            },
        )

        assert response.status_code == 422
        assert "https" in str(response.json()["error"]["details"]).lower()

    def test_private_address_video_url_is_rejected(
        self, owner_client: TestClient, api: str
    ) -> None:
        response = owner_client.post(
            f"{api}/campaigns",
            json={
                "name": "SSRF",
                "ads": [{"name": "Ad 1", "video_url": "https://192.168.0.10/a.mp4"}],
            },
        )

        assert response.status_code == 422


class TestPublishContract:
    def test_incomplete_campaign_cannot_publish(self, owner_client: TestClient, api: str) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json={"name": "Bare draft"}).json()[
            "id"
        ]

        response = owner_client.post(
            f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"}
        )

        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"

        fields = {d["field"] for d in body["error"]["details"]}
        assert "ads" in fields
        assert "audience_id" in fields

    def test_details_is_always_an_array(self, owner_client: TestClient, api: str) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json={"name": "Bare draft"}).json()[
            "id"
        ]

        body = owner_client.post(
            f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"}
        ).json()

        assert isinstance(body["error"]["details"], list)

    def test_blockers_are_reported_on_read_before_publishing(
        self, owner_client: TestClient, api: str
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json={"name": "Bare draft"}).json()[
            "id"
        ]

        body = owner_client.get(f"{api}/campaigns/{campaign_id}").json()

        # The builder can disable Publish without attempting the call.
        assert "ads" in body["publish_blockers"]
        assert body["effective_status"] == "INCOMPLETE"

    def test_financial_category_requires_a_disclaimer(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        payload = {**draft_payload}
        payload["compliance"] = {"special_category": "FINANCIAL_PRODUCTS_SERVICES"}

        response = owner_client.post(f"{api}/campaigns", json=payload)

        assert response.status_code == 422
        assert "disclaimer" in str(response.json()["error"]["details"]).lower()


class TestLifecycle:
    def test_publishing_a_future_campaign_yields_scheduled(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        payload = {**draft_payload, "schedule": {"start_at": "2099-01-01T00:00:00Z"}}
        campaign_id = owner_client.post(f"{api}/campaigns", json=payload).json()["id"]

        body = owner_client.post(
            f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"}
        ).json()

        # The server picks SCHEDULED because the start is in the future.
        assert body["status"] == "SCHEDULED"
        assert body["badge"] == "Published"
        assert body["effective_status"] == "SCHEDULED"

    def test_a_scheduled_campaign_is_not_open_to_viewers(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        payload = {**draft_payload, "schedule": {"start_at": "2099-01-01T00:00:00Z"}}
        campaign_id = owner_client.post(f"{api}/campaigns", json=payload).json()["id"]
        owner_client.post(f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"})

        response = owner_client.get(f"{api}/public/campaigns/{campaign_id}")

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "CAMPAIGN_NOT_LIVE"

    def test_a_draft_is_not_open_to_viewers(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]

        assert owner_client.get(f"{api}/public/campaigns/{campaign_id}").status_code == 403

    def test_the_owner_can_still_preview_a_draft(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]

        response = owner_client.get(f"{api}/campaigns/{campaign_id}/preview")

        assert response.status_code == 200
        assert response.json()["customer_name"] == "Rahul"

    def test_pause_closes_it_to_viewers(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        campaign_id = published_campaign["id"]
        owner_client.post(f"{api}/campaigns/{campaign_id}/status", json={"status": "PAUSED"})

        assert owner_client.get(f"{api}/public/campaigns/{campaign_id}").status_code == 403

    def test_unpublish_is_blocked_once_events_exist(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        campaign_id = published_campaign["id"]
        owner_client.post(
            f"{api}/public/campaigns/{campaign_id}/views",
            json={"session_id": "sess-12345678"},
        )

        response = owner_client.post(
            f"{api}/campaigns/{campaign_id}/status", json={"status": "DRAFT"}
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "CAMPAIGN_LOCKED"

    def test_unpublish_is_allowed_before_any_events(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        response = owner_client.post(
            f"{api}/campaigns/{published_campaign['id']}/status",
            json={"status": "DRAFT"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "DRAFT"

    def test_archived_is_terminal(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        campaign_id = published_campaign["id"]
        owner_client.post(f"{api}/campaigns/{campaign_id}/status", json={"status": "ARCHIVED"})

        response = owner_client.post(
            f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"}
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "CAMPAIGN_INVALID_TRANSITION"

    def test_archived_is_hidden_from_the_dashboard(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        owner_client.post(
            f"{api}/campaigns/{published_campaign['id']}/status",
            json={"status": "ARCHIVED"},
        )

        assert owner_client.get(f"{api}/campaigns").json()["total"] == 0
        assert (
            owner_client.get(f"{api}/campaigns", params={"include_archived": True}).json()["total"]
            == 1
        )

    def test_objective_freezes_after_publishing(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        response = owner_client.patch(
            f"{api}/campaigns/{published_campaign['id']}",
            json={"objective": "AWARENESS"},
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "CAMPAIGN_LOCKED"


class TestEditing:
    def test_partial_update_leaves_other_fields_alone(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]

        updated = owner_client.patch(
            f"{api}/campaigns/{campaign_id}", json={"description": "A note."}
        ).json()

        assert updated["description"] == "A note."
        assert updated["name"] == "Investment Opportunity"
        assert updated["ads"][0]["video_url"] == "https://cdn.example.com/investment.mp4"

    def test_rewording_a_label_keeps_its_analytics_key(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        ad = owner_client.get(f"{api}/campaigns/{campaign_id}").json()["ads"][0]
        original_key = ad["options"][0]["key"]

        options = [
            {**draft_payload["ads"][0]["options"][0], "label": "Yes, I'm interested"},
            draft_payload["ads"][0]["options"][1],
        ]
        updated = owner_client.patch(
            f"{api}/campaigns/{campaign_id}/ads/{ad['id']}", json={"options": options}
        ).json()

        assert updated["options"][0]["label"] == "Yes, I'm interested"
        # The key is stable, so the metric does not split into two series.
        assert updated["options"][0]["key"] == original_key == "tell-me-more"

    def test_editing_a_missing_campaign_is_404(self, owner_client: TestClient, api: str) -> None:
        response = owner_client.patch(f"{api}/campaigns/does-not-exist", json={"name": "X"})

        assert response.status_code == 404
