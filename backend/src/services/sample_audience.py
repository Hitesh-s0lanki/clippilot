"""The sample audiences every account starts with.

An empty audience screen teaches nobody anything: the segment breakdown is the
point of the feature, and a breakdown of nothing is a blank card. So a new
account is given three lists of realistic people to look at, filter and target
a first campaign with.

The data is deliberately **ragged** - about a fifth of these people have no
email, a third no phone, and a handful no age, city or gender. That is what an
uploaded list actually looks like, and it is what proves the optional fields
are genuinely optional and gives the UNKNOWN buckets something to hold.

One definition, two callers: the runtime provisioner in ``AudienceService`` and
the ``seed_audiences`` script. Two copies of a hundred fake people would drift.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.schemas.enums import Gender

# Deterministic: the same account always gets the same hundred people, so a
# screenshot taken today still matches the database tomorrow.
SEED = 20260823

FIRST_NAMES_F = [
    "Priya",
    "Ananya",
    "Kavya",
    "Meera",
    "Divya",
    "Sneha",
    "Aditi",
    "Ishita",
    "Neha",
    "Pooja",
    "Riya",
    "Shruti",
    "Tanvi",
    "Nisha",
    "Lakshmi",
    "Deepika",
]
FIRST_NAMES_M = [
    "Rahul",
    "Arjun",
    "Vikram",
    "Rohan",
    "Aditya",
    "Karan",
    "Siddharth",
    "Nikhil",
    "Amit",
    "Rajesh",
    "Sanjay",
    "Varun",
    "Manish",
    "Ashok",
    "Harsh",
    "Gaurav",
]
SURNAMES = [
    "Mehta",
    "Sharma",
    "Iyer",
    "Nair",
    "Reddy",
    "Kapoor",
    "Desai",
    "Bose",
    "Chopra",
    "Malhotra",
    "Patel",
    "Rao",
    "Joshi",
    "Verma",
    "Banerjee",
    "Gupta",
]

# Weighted so the breakdown has a recognisable shape rather than eight equal
# bars - a real list is concentrated in a few places.
CITIES: list[tuple[str, str, int]] = [
    ("Mumbai", "India", 22),
    ("Delhi", "India", 16),
    ("Bangalore", "India", 15),
    ("Pune", "India", 9),
    ("Hyderabad", "India", 8),
    ("Chennai", "India", 7),
    ("Kolkata", "India", 5),
    ("Ahmedabad", "India", 4),
    ("Dubai", "United Arab Emirates", 6),
    ("Singapore", "Singapore", 4),
    ("London", "United Kingdom", 3),
    ("New York", "United States", 3),
]


@dataclass(frozen=True, slots=True)
class SampleSegment:
    """One audience to create, and how many people to put in it."""

    name: str
    description: str
    size: int
    age_range: tuple[int, int]


SAMPLE_SEGMENTS: tuple[SampleSegment, ...] = (
    SampleSegment(
        name="HNI Investors - Metro",
        description=(
            "Sample data. High net worth contacts across the top metros - the list "
            "the illustrative investment campaign was built for."
        ),
        size=40,
        age_range=(34, 68),
    ),
    SampleSegment(
        name="Mutual Fund Prospects",
        description=(
            "Sample data. Warm leads from the SIP calculator: younger, mobile-first, "
            "and more reachable by phone than by email."
        ),
        size=35,
        age_range=(22, 41),
    ),
    SampleSegment(
        name="Lapsed Policyholders",
        description=(
            "Sample data. Policies that ran out in the last 18 months and were never "
            "renewed - the re-engagement list."
        ),
        size=25,
        age_range=(29, 74),
    ),
)

SAMPLE_TOTAL = sum(segment.size for segment in SAMPLE_SEGMENTS)


def sample_people(segment: SampleSegment) -> list[dict]:
    """Build one segment's worth of people, with realistic gaps in the data.

    Seeded from the segment's own name rather than from a shared counter, so
    adding a fourth segment later does not reshuffle the first three.
    """
    rng = random.Random(SEED + sum(ord(char) for char in segment.name))
    cities = [(city, country) for city, country, _ in CITIES]
    weights = [weight for _, _, weight in CITIES]
    used_emails: set[str] = set()
    people: list[dict] = []

    for index in range(segment.size):
        gender = rng.choices(
            [Gender.FEMALE, Gender.MALE, Gender.OTHER, Gender.UNKNOWN],
            weights=[45, 45, 3, 7],
        )[0]

        pool = FIRST_NAMES_F if gender is Gender.FEMALE else FIRST_NAMES_M
        if gender in {Gender.OTHER, Gender.UNKNOWN}:
            pool = FIRST_NAMES_F + FIRST_NAMES_M

        first = rng.choice(pool)
        last = rng.choice(SURNAMES)

        email = None
        if rng.random() < 0.80:
            candidate = f"{first}.{last}{index}".lower()
            if candidate not in used_emails:
                used_emails.add(candidate)
                email = f"{candidate}@example.com"

        city, country = (
            rng.choices(cities, weights=weights)[0] if rng.random() < 0.88 else (None, None)
        )

        people.append(
            {
                "full_name": f"{first} {last}",
                "email": email,
                "phone": f"+9198{rng.randint(10000000, 99999999)}" if rng.random() < 0.66 else None,
                "age": rng.randint(*segment.age_range) if rng.random() < 0.92 else None,
                "gender": gender.value,
                "city": city,
                "country": country,
                "external_ref": f"CRM-{rng.randint(10000, 99999)}" if rng.random() < 0.55 else None,
            }
        )

    return people
