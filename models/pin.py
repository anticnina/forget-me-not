from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from database.connection import execute


@dataclass
class FeedItem:
    pin_id: int
    creator_id: int
    username: str
    profile_pic_path: Optional[str]
    map_id: int
    map_title: str
    person_name: str
    description: Optional[str]
    image_path: Optional[str]
    created_at: object
    latitude: float = 0.0
    longitude: float = 0.0


def get_feed_for_user(user_id: int) -> list[FeedItem]:
    """Recent pins by friends on maps the current user can access."""
    rows = execute(
        """
        SELECT p.id AS pin_id, p.creator_id, u.username, u.profile_pic_path,
               p.map_id, m.title AS map_title, p.person_name, p.description,
               p.image_path, p.created_at, p.latitude, p.longitude
        FROM pins p
        JOIN users u ON u.id = p.creator_id
        JOIN maps m ON m.id = p.map_id
        WHERE p.creator_id IN (
            SELECT CASE WHEN user_id1 = %s THEN user_id2 ELSE user_id1 END
            FROM friendships
            WHERE (user_id1 = %s OR user_id2 = %s) AND status = 'accepted'
        )
        AND (
            m.is_private = FALSE
            OR m.creator_id = %s
            OR EXISTS (
                SELECT 1 FROM map_collaborators mc
                WHERE mc.map_id = m.id AND mc.user_id = %s
            )
        )
        ORDER BY p.created_at DESC
        LIMIT 50
        """,
        (user_id, user_id, user_id, user_id, user_id),
        fetch="all",
    )
    return [FeedItem(**r) for r in rows] if rows else []


@dataclass
class Pin:
    id: int
    map_id: int
    creator_id: Optional[int]
    latitude: float
    longitude: float
    person_name: str
    description: Optional[str] = None
    image_path: Optional[str] = None
    created_at: object = None


def create_pin(
    map_id: int,
    creator_id: int,
    lat: float,
    lng: float,
    person_name: str,
    description: Optional[str] = None,
    image_path: Optional[str] = None,
) -> Optional[Pin]:
    row = execute(
        "INSERT INTO pins (map_id, creator_id, latitude, longitude, person_name, description, image_path) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *",
        (map_id, creator_id, lat, lng, person_name, description, image_path),
        fetch="one",
    )
    return Pin(**row) if row else None


def get_pins_for_map(map_id: int) -> list[Pin]:
    rows = execute(
        "SELECT * FROM pins WHERE map_id = %s ORDER BY created_at",
        (map_id,),
        fetch="all",
    )
    return [Pin(**r) for r in rows]


def delete_pin(pin_id: int) -> None:
    execute("DELETE FROM pins WHERE id = %s", (pin_id,))


def count_pins_for_map(map_id: int) -> int:
    row = execute(
        "SELECT COUNT(*) AS n FROM pins WHERE map_id = %s", (map_id,), fetch="one"
    )
    return int(row["n"]) if row else 0
