"""The public ads library: GET /public/campaigns.

The widest unauthenticated surface in the API - no campaign id to guess - so
these tests are as much about what the payload must *not* contain as what it
must.
"""

from fastapi.testclient import TestClient

from src.core.security import DEV_USER_HEADER


def _anonymous(client: TestClient) -> TestClient:
    """Drop the identity header rather than building a second TestClient.

    A second client spins up its own event loop, and the engine pool already
    holds connections bound to the first one.
    """
    client.headers.pop(DEV_USER_HEADER, None)
    return client


class TestAdsLibrary:
    def test_empty_before_anything_is_published(self, client: TestClient, api: str) -> None:
        body = client.get(f"{api}/public/campaigns").json()

        assert body == {"items": [], "total": 0, "limit": 24, "offset": 0}

    def test_draft_campaigns_are_not_listed(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        created = owner_client.post(f"{api}/campaigns", json=draft_payload)
        assert created.status_code == 201, created.text

        body = _anonymous(owner_client).get(f"{api}/public/campaigns").json()

        assert body["total"] == 0

    def test_published_campaign_is_listed_without_a_session(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        body = _anonymous(owner_client).get(f"{api}/public/campaigns").json()

        assert body["total"] == 1
        card = body["items"][0]
        assert card["campaign_id"] == published_campaign["id"]
        assert card["campaign_name"] == "Investment Opportunity"
        assert card["objective"] == "LEAD_CAPTURE"
        assert card["special_category"] == "FINANCIAL_PRODUCTS_SERVICES"
        assert card["option_labels"] == ["Tell me more", "Not interested"]
        assert card["published_at"]

    def test_listing_never_names_anyone_in_the_audience(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        """The campaign is addressed to Rahul; the public listing must not say so."""
        response = _anonymous(owner_client).get(f"{api}/public/campaigns")

        assert "Rahul" not in response.text
        card = response.json()["items"][0]
        assert card["preview_message"] == (
            "Hi there, we have identified an investment opportunity for you."
        )

    def test_listing_carries_no_owner_or_commercial_fields(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        card = _anonymous(owner_client).get(f"{api}/public/campaigns").json()["items"][0]

        for leaked in (
            "owner_user_id",
            "budget",
            "delivery",
            "tracking",
            "audience",
            "audience_size",
            "metrics",
            "disclaimer_text",
        ):
            assert leaked not in card

    def test_pausing_removes_it_from_the_library(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        campaign_id = published_campaign["id"]
        paused = owner_client.post(
            f"{api}/campaigns/{campaign_id}/status", json={"status": "PAUSED"}
        )
        assert paused.status_code == 200, paused.text

        body = _anonymous(owner_client).get(f"{api}/public/campaigns").json()

        assert body["total"] == 0

    def test_pagination_echoes_the_window(
        self, owner_client: TestClient, api: str, published_campaign: dict
    ) -> None:
        body = (
            _anonymous(owner_client)
            .get(f"{api}/public/campaigns", params={"limit": 1, "offset": 1})
            .json()
        )

        assert body["total"] == 1
        assert body["items"] == []
        assert body["limit"] == 1
        assert body["offset"] == 1

    def test_limit_is_bounded(self, client: TestClient, api: str) -> None:
        assert client.get(f"{api}/public/campaigns", params={"limit": 500}).status_code == 422
