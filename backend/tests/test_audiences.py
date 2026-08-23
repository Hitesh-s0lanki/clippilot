"""Audiences: reusable lists, ragged imports, segments and campaign selection.

The three things this has to get right are the three the feature is for: an
upload where most fields are missing still lands, a breakdown accounts for
everybody including the people who did not say, and a campaign cannot publish
against a list that is not there.
"""

from fastapi.testclient import TestClient

from src.core.security import DEV_USER_HEADER
from src.services.sample_audience import SAMPLE_TOTAL
from tests.conftest import OTHER_OWNER, OWNER


def _members(count: int, *, prefix: str = "Person") -> list[dict]:
    return [{"full_name": f"{prefix} {i}"} for i in range(count)]


class TestAudienceCrud:
    def test_create_returns_the_audience_with_an_empty_breakdown(
        self, owner_client: TestClient, api: str
    ) -> None:
        response = owner_client.post(f"{api}/audiences", json={"name": "Metro HNI"})

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["name"] == "Metro HNI"
        assert body["member_count"] == 0
        assert body["campaign_count"] == 0
        assert body["segments"]["total"] == 0
        assert body["segments"]["age_groups"] == []

    def test_names_are_unique_per_owner_case_insensitively(
        self, owner_client: TestClient, api: str
    ) -> None:
        owner_client.post(f"{api}/audiences", json={"name": "Metro HNI"})

        clash = owner_client.post(f"{api}/audiences", json={"name": "metro hni"})

        assert clash.status_code == 409
        assert clash.json()["error"]["code"] == "AUDIENCE_NAME_TAKEN"

    def test_another_owner_may_reuse_the_same_name(
        self, owner_client: TestClient, api: str
    ) -> None:
        owner_client.post(f"{api}/audiences", json={"name": "Metro HNI"})

        owner_client.headers[DEV_USER_HEADER] = OTHER_OWNER
        response = owner_client.post(f"{api}/audiences", json={"name": "Metro HNI"})

        assert response.status_code == 201

    def test_someone_elses_audience_is_not_found_rather_than_forbidden(
        self, owner_client: TestClient, api: str, audience: dict
    ) -> None:
        owner_client.headers[DEV_USER_HEADER] = OTHER_OWNER

        response = owner_client.get(f"{api}/audiences/{audience['id']}")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "AUDIENCE_NOT_FOUND"


class TestRaggedImport:
    def test_only_a_name_is_required(self, owner_client: TestClient, api: str) -> None:
        created = owner_client.post(
            f"{api}/audiences",
            json={"name": "Sparse list", "members": [{"full_name": "Just A Name"}]},
        )

        assert created.status_code == 201, created.text
        assert created.json()["member_count"] == 1

    def test_a_repeated_email_costs_its_row_and_not_the_upload(
        self, owner_client: TestClient, api: str, audience: dict
    ) -> None:
        response = owner_client.post(
            f"{api}/audiences/{audience['id']}/members",
            json={
                "members": [
                    {"full_name": "New Person", "email": "new@example.com"},
                    {"full_name": "Rahul Again", "email": "rahul@example.com"},
                    {"full_name": "Third Person"},
                ]
            },
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["added"] == 2
        assert body["member_count"] == 3
        assert [s["full_name"] for s in body["skipped"]] == ["Rahul Again"]
        assert "already on this audience" in body["skipped"][0]["reason"]

    def test_an_email_repeated_inside_one_upload_is_caught_too(
        self, owner_client: TestClient, api: str, audience: dict
    ) -> None:
        response = owner_client.post(
            f"{api}/audiences/{audience['id']}/members",
            json={
                "members": [
                    {"full_name": "First", "email": "same@example.com"},
                    {"full_name": "Second", "email": "same@example.com"},
                ]
            },
        )

        assert response.json()["added"] == 1
        assert response.json()["skipped"][0]["full_name"] == "Second"

    def test_a_city_is_folded_to_one_spelling(self, owner_client: TestClient, api: str) -> None:
        """Two spellings of one city must not become two segments."""
        created = owner_client.post(
            f"{api}/audiences",
            json={
                "name": "Spelling",
                "members": [
                    {"full_name": "A", "city": "mumbai", "country": "india"},
                    {"full_name": "B", "city": "MUMBAI", "country": "INDIA"},
                    {"full_name": "C", "city": "Mumbai", "country": "India"},
                ],
            },
        )

        cities = created.json()["segments"]["cities"]
        assert cities == [{"key": "Mumbai", "count": 3, "share": 1.0}]


class TestSegments:
    def test_the_breakdown_accounts_for_everyone(self, owner_client: TestClient, api: str) -> None:
        """Shares add to 1: a member with no age is UNKNOWN, never dropped."""
        created = owner_client.post(
            f"{api}/audiences",
            json={
                "name": "Mixed",
                "members": [
                    {"full_name": "A", "age": 21, "gender": "FEMALE"},
                    {"full_name": "B", "age": 30, "gender": "MALE"},
                    {"full_name": "C", "age": 31},
                    {"full_name": "D"},
                ],
            },
        )

        segments = created.json()["segments"]

        assert segments["total"] == 4
        assert sum(b["count"] for b in segments["age_groups"]) == 4
        assert sum(b["count"] for b in segments["genders"]) == 4
        assert {b["key"]: b["count"] for b in segments["age_groups"]} == {
            "AGE_18_24": 1,
            "AGE_25_34": 2,
            "UNKNOWN": 1,
        }
        assert {b["key"]: b["count"] for b in segments["genders"]}["UNKNOWN"] == 2

    def test_reach_counts_only_the_people_who_can_be_reached(
        self, owner_client: TestClient, api: str
    ) -> None:
        created = owner_client.post(
            f"{api}/audiences",
            json={
                "name": "Reach",
                "members": [
                    {"full_name": "A", "email": "a@example.com", "phone": "+919876543210"},
                    {"full_name": "B", "email": "b@example.com"},
                    {"full_name": "C"},
                ],
            },
        )

        segments = created.json()["segments"]

        assert (segments["total"], segments["with_email"], segments["with_phone"]) == (3, 2, 1)

    def test_the_breakdown_names_nobody(
        self, owner_client: TestClient, api: str, audience: dict
    ) -> None:
        response = owner_client.get(f"{api}/audiences/{audience['id']}/segments")

        assert "Rahul" not in response.text
        assert "rahul@example.com" not in response.text


class TestMemberFilters:
    def _seeded(self, owner_client: TestClient, api: str) -> str:
        created = owner_client.post(
            f"{api}/audiences",
            json={
                "name": "Filterable",
                "members": [
                    {"full_name": "Mumbai Young", "age": 22, "city": "Mumbai", "gender": "FEMALE"},
                    {"full_name": "Mumbai Older", "age": 58, "city": "Mumbai", "gender": "MALE"},
                    {
                        "full_name": "Delhi Mid",
                        "age": 30,
                        "city": "Delhi",
                        "email": "d@example.com",
                    },
                ],
            },
        )
        return created.json()["id"]

    def test_filters_combine_and_total_counts_the_segment_not_the_list(
        self, owner_client: TestClient, api: str
    ) -> None:
        audience_id = self._seeded(owner_client, api)

        response = owner_client.get(
            f"{api}/audiences/{audience_id}/members?city=Mumbai&age_group=AGE_18_24"
        )

        body = response.json()
        assert body["total"] == 1
        assert [m["full_name"] for m in body["items"]] == ["Mumbai Young"]

    def test_age_group_is_derived_rather_than_stored(
        self, owner_client: TestClient, api: str
    ) -> None:
        audience_id = self._seeded(owner_client, api)

        items = owner_client.get(f"{api}/audiences/{audience_id}/members").json()["items"]

        assert {m["full_name"]: m["age_group"] for m in items} == {
            "Mumbai Young": "AGE_18_24",
            "Mumbai Older": "AGE_55_64",
            "Delhi Mid": "AGE_25_34",
        }

    def test_search_matches_more_than_the_name(self, owner_client: TestClient, api: str) -> None:
        audience_id = self._seeded(owner_client, api)

        body = owner_client.get(f"{api}/audiences/{audience_id}/members?search=d@example").json()

        assert [m["full_name"] for m in body["items"]] == ["Delhi Mid"]

    def test_reachability_is_filterable(self, owner_client: TestClient, api: str) -> None:
        audience_id = self._seeded(owner_client, api)

        body = owner_client.get(f"{api}/audiences/{audience_id}/members?has_email=true").json()

        assert body["total"] == 1

    def test_the_page_window_is_echoed(self, owner_client: TestClient, api: str) -> None:
        created = owner_client.post(
            f"{api}/audiences", json={"name": "Big", "members": _members(30)}
        )
        audience_id = created.json()["id"]

        body = owner_client.get(f"{api}/audiences/{audience_id}/members?limit=10&offset=20").json()

        assert (body["total"], body["limit"], body["offset"]) == (30, 10, 20)
        assert len(body["items"]) == 10


class TestCampaignSelection:
    def test_a_campaign_reports_the_audience_it_targets(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        body = owner_client.post(f"{api}/campaigns", json=draft_payload).json()

        assert body["audience"]["name"] == "Investment Opportunity - Q3 HNI"
        assert body["audience"]["member_count"] == 1

    def test_the_dashboard_row_carries_the_audience_too(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        owner_client.post(f"{api}/campaigns", json=draft_payload)

        row = owner_client.get(f"{api}/campaigns").json()["items"][0]

        assert row["audience_name"] == "Investment Opportunity - Q3 HNI"
        assert row["audience_size"] == 1

    def test_someone_elses_audience_cannot_be_attached(
        self, owner_client: TestClient, api: str
    ) -> None:
        """The foreign key alone would accept any id that exists.

        One client with a swapped identity header rather than two: a second
        TestClient spins up its own event loop, and the engine pool already
        holds connections bound to the first.
        """
        owner_client.headers[DEV_USER_HEADER] = OTHER_OWNER
        theirs = owner_client.post(f"{api}/audiences", json={"name": "Not yours"}).json()["id"]

        owner_client.headers[DEV_USER_HEADER] = OWNER
        response = owner_client.post(
            f"{api}/campaigns", json={"name": "Borrowed list", "audience_id": theirs}
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "AUDIENCE_NOT_FOUND"

    def test_publishing_without_an_audience_is_blocked(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        payload = {**draft_payload, "audience_id": None}
        campaign_id = owner_client.post(f"{api}/campaigns", json=payload).json()["id"]

        response = owner_client.post(
            f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"}
        )

        assert response.status_code == 422
        assert "audience_id" in {d["field"] for d in response.json()["error"]["details"]}

    def test_publishing_against_an_empty_audience_is_blocked(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        empty = owner_client.post(f"{api}/audiences", json={"name": "Nobody yet"}).json()
        payload = {**draft_payload, "audience_id": empty["id"]}
        campaign_id = owner_client.post(f"{api}/campaigns", json=payload).json()["id"]

        response = owner_client.post(
            f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"}
        )

        assert response.status_code == 422
        detail = next(d for d in response.json()["error"]["details"] if d["field"] == "audience_id")
        assert "Nobody yet" in detail["message"]

    def test_an_audience_in_use_cannot_be_deleted(
        self, owner_client: TestClient, api: str, draft_payload: dict, audience: dict
    ) -> None:
        owner_client.post(f"{api}/campaigns", json=draft_payload)

        response = owner_client.delete(f"{api}/audiences/{audience['id']}")

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "AUDIENCE_IN_USE"

    def test_an_unused_audience_deletes(self, owner_client: TestClient, api: str) -> None:
        audience_id = owner_client.post(f"{api}/audiences", json={"name": "Spare"}).json()["id"]

        assert owner_client.delete(f"{api}/audiences/{audience_id}").status_code == 204
        assert owner_client.get(f"{api}/audiences/{audience_id}").status_code == 404


class TestPersonalisationAcrossTheAudience:
    def test_each_member_gets_their_own_render(
        self, owner_client: TestClient, api: str, draft_payload: dict, audience: dict
    ) -> None:
        """The bug the old shape had: one name signed everybody's copy."""
        owner_client.post(
            f"{api}/audiences/{audience['id']}/members",
            json={"members": [{"full_name": "Priya Nair", "city": "Delhi"}]},
        )
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        members = owner_client.get(f"{api}/audiences/{audience['id']}/members").json()["items"]
        second = next(m for m in members if m["full_name"] == "Priya Nair")

        body = owner_client.get(
            f"{api}/campaigns/{campaign_id}/preview?member_id={second['id']}"
        ).json()

        assert body["customer_name"] == "Priya Nair"
        assert body["member_id"] == second["id"]
        assert body["ad"]["personalised_message"].startswith("Hi Priya Nair,")

    def test_the_follow_up_is_addressed_to_whoever_responded(
        self, owner_client: TestClient, api: str, audience: dict, draft_payload: dict
    ) -> None:
        owner_client.post(
            f"{api}/audiences/{audience['id']}/members",
            json={"members": [{"full_name": "Priya Nair"}]},
        )
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        owner_client.post(f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"})

        members = owner_client.get(f"{api}/audiences/{audience['id']}/members").json()["items"]
        priya = next(m for m in members if m["full_name"] == "Priya Nair")
        preview = owner_client.get(
            f"{api}/campaigns/{campaign_id}/preview?member_id={priya['id']}"
        ).json()
        option_id = preview["ad"]["options"][0]["id"]

        result = owner_client.post(
            f"{api}/public/campaigns/{campaign_id}/responses",
            json={
                "session_id": "priya-session-1",
                "option_id": option_id,
                "member_id": priya["id"],
            },
        )

        assert result.status_code == 201, result.text
        assert result.json()["follow_up_message"] == "Great, Priya Nair - an advisor will call."

    def test_a_missing_city_falls_back_rather_than_leaving_a_gap(
        self, owner_client: TestClient, api: str, audience: dict, draft_payload: dict
    ) -> None:
        """A ragged list is the normal case, so an empty city must still read."""
        payload = {**draft_payload}
        payload["ads"] = [
            {
                **draft_payload["ads"][0],
                "personalised_message": "Hi {{first_name}}, an opportunity in {{city}}.",
            }
        ]
        owner_client.post(
            f"{api}/audiences/{audience['id']}/members",
            json={"members": [{"full_name": "Priya Nair"}]},
        )
        campaign_id = owner_client.post(f"{api}/campaigns", json=payload).json()["id"]
        members = owner_client.get(f"{api}/audiences/{audience['id']}/members").json()["items"]
        priya = next(m for m in members if m["full_name"] == "Priya Nair")

        body = owner_client.get(
            f"{api}/campaigns/{campaign_id}/preview?member_id={priya['id']}"
        ).json()

        assert body["ad"]["personalised_message"] == "Hi Priya, an opportunity in your city."

    def test_a_member_id_from_another_audience_is_rejected(
        self, owner_client: TestClient, api: str, draft_payload: dict
    ) -> None:
        other = owner_client.post(
            f"{api}/audiences",
            json={"name": "Elsewhere", "members": [{"full_name": "Outsider"}]},
        ).json()
        outsider = owner_client.get(f"{api}/audiences/{other['id']}/members").json()["items"][0]
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]

        response = owner_client.get(
            f"{api}/campaigns/{campaign_id}/preview?member_id={outsider['id']}"
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "MEMBER_NOT_FOUND"


class TestMemberRemoval:
    def test_removing_someone_recalculates_the_breakdown(
        self, owner_client: TestClient, api: str, audience: dict
    ) -> None:
        member = owner_client.get(f"{api}/audiences/{audience['id']}/members").json()["items"][0]

        response = owner_client.delete(f"{api}/audiences/{audience['id']}/members/{member['id']}")

        assert response.status_code == 200
        assert response.json()["member_count"] == 0
        assert response.json()["segments"]["total"] == 0

    def test_removing_someone_keeps_the_views_they_recorded(
        self, owner_client: TestClient, api: str, draft_payload: dict, audience: dict
    ) -> None:
        """Deleting a person must not delete the history they made."""
        campaign_id = owner_client.post(f"{api}/campaigns", json=draft_payload).json()["id"]
        owner_client.post(f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"})
        member = owner_client.get(f"{api}/audiences/{audience['id']}/members").json()["items"][0]
        owner_client.post(
            f"{api}/public/campaigns/{campaign_id}/views",
            json={"session_id": "seen-once-1", "member_id": member["id"]},
        )

        # The campaign has to let go of the list before the list can be deleted.
        owner_client.patch(f"{api}/campaigns/{campaign_id}", json={"audience_id": None})
        owner_client.delete(f"{api}/audiences/{audience['id']}")

        analytics = owner_client.get(f"{api}/campaigns/{campaign_id}/analytics").json()
        assert analytics["views"] == 1


class TestSampleAudiences:
    """Every account lands on a populated screen, not an empty one."""

    def test_a_new_account_is_given_the_sample_lists(
        self, sample_data_client: TestClient, api: str
    ) -> None:
        body = sample_data_client.get(f"{api}/audiences").json()

        assert body["total"] == 3
        assert sum(a["member_count"] for a in body["items"]) == SAMPLE_TOTAL
        assert all(a["campaign_count"] == 0 for a in body["items"])

    def test_the_sample_breakdown_is_worth_looking_at(
        self, sample_data_client: TestClient, api: str
    ) -> None:
        """The point of the data is that the segments are not all one bucket."""
        listing = sample_data_client.get(f"{api}/audiences").json()
        audience_id = listing["items"][0]["id"]

        segments = sample_data_client.get(f"{api}/audiences/{audience_id}/segments").json()

        assert len(segments["age_groups"]) > 1
        assert len(segments["cities"]) > 1
        # Ragged on purpose: some people are reachable and some are not, which
        # is what makes the reach numbers say anything at all.
        assert 0 < segments["with_email"] < segments["total"]
        assert 0 < segments["with_phone"] < segments["total"]

    def test_the_sample_people_are_ragged(self, sample_data_client: TestClient, api: str) -> None:
        listing = sample_data_client.get(f"{api}/audiences").json()
        audience_id = listing["items"][0]["id"]

        page = sample_data_client.get(f"{api}/audiences/{audience_id}/members?limit=200").json()

        assert any(m["email"] is None for m in page["items"])
        assert any(m["city"] is None for m in page["items"])
        assert any(m["age_group"] == "UNKNOWN" for m in page["items"])
        assert all(m["full_name"] for m in page["items"])

    def test_listing_twice_does_not_double_anybody(
        self, sample_data_client: TestClient, api: str
    ) -> None:
        first = sample_data_client.get(f"{api}/audiences").json()
        second = sample_data_client.get(f"{api}/audiences").json()

        assert second["total"] == first["total"] == 3
        assert sum(a["member_count"] for a in second["items"]) == SAMPLE_TOTAL

    def test_each_account_gets_its_own_copy(self, sample_data_client: TestClient, api: str) -> None:
        """Shared rows would let one account edit another's list."""
        mine = sample_data_client.get(f"{api}/audiences").json()

        sample_data_client.headers[DEV_USER_HEADER] = OTHER_OWNER
        theirs = sample_data_client.get(f"{api}/audiences").json()

        assert theirs["total"] == 3
        assert {a["id"] for a in mine["items"]}.isdisjoint({a["id"] for a in theirs["items"]})

    def test_an_account_that_already_has_a_list_is_left_alone(
        self, sample_data_client: TestClient, api: str
    ) -> None:
        sample_data_client.post(f"{api}/audiences", json={"name": "My own list"})

        body = sample_data_client.get(f"{api}/audiences").json()

        assert body["total"] == 1
        assert body["items"][0]["name"] == "My own list"

    def test_a_search_that_matches_nothing_does_not_provision(
        self, sample_data_client: TestClient, api: str
    ) -> None:
        """ "No match for 'zzz'" is not the same as "this account has nothing"."""
        body = sample_data_client.get(f"{api}/audiences?search=zzz").json()

        assert body["total"] == 0

    def test_the_behaviour_can_be_switched_off(self, owner_client: TestClient, api: str) -> None:
        """`owner_client` runs with sample_audiences=False."""
        assert owner_client.get(f"{api}/audiences").json()["total"] == 0


class TestOwnership:
    def test_the_listing_only_shows_your_own(
        self, owner_client: TestClient, api: str, audience: dict
    ) -> None:
        owner_client.headers[DEV_USER_HEADER] = OTHER_OWNER
        owner_client.post(f"{api}/audiences", json={"name": "Theirs"})

        owner_client.headers[DEV_USER_HEADER] = OWNER
        body = owner_client.get(f"{api}/audiences").json()

        assert body["total"] == 1
        assert [a["name"] for a in body["items"]] == ["Investment Opportunity - Q3 HNI"]
