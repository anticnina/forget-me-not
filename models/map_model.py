from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from database.connection import execute


@dataclass
class Map:
    id: int
    creator_id: int
    title: str
    is_private: bool
    created_at: object = None


@dataclass
class FriendMap:
    id: int
    creator_id: int
    title: str
    is_private: bool
    created_at: object
    friend_username: str
    friend_profile_pic: Optional[str]


# ── CRUD ─────────────────────────────────────────────────────

def create_map(creator_id: int, title: str, is_private: bool = False) -> Optional[Map]:
    row = execute(
        "INSERT INTO maps (creator_id, title, is_private) VALUES (%s, %s, %s) RETURNING *",
        (creator_id, title, is_private),
        fetch="one",
    )
    return Map(**row) if row else None


def get_by_id(map_id: int) -> Optional[Map]:
    row = execute("SELECT * FROM maps WHERE id = %s", (map_id,), fetch="one")
    return Map(**row) if row else None


def delete_map(map_id: int) -> None:
    execute("DELETE FROM maps WHERE id = %s", (map_id,))


def update_privacy(map_id: int, is_private: bool) -> None:
    execute("UPDATE maps SET is_private = %s WHERE id = %s", (is_private, map_id))


def update_title(map_id: int, title: str) -> None:
    execute("UPDATE maps SET title = %s WHERE id = %s", (title, map_id))


# ── Queries by visibility ─────────────────────────────────────

def get_my_maps(user_id: int) -> list[Map]:
    rows = execute(
        "SELECT * FROM maps WHERE creator_id = %s ORDER BY created_at DESC",
        (user_id,),
        fetch="all",
    )
    return [Map(**r) for r in rows]


def get_shared_maps(user_id: int) -> list[Map]:
    """Maps the user was invited to but did not create."""
    rows = execute(
        "SELECT m.* FROM maps m "
        "JOIN map_collaborators mc ON mc.map_id = m.id "
        "WHERE mc.user_id = %s AND m.creator_id != %s "
        "ORDER BY m.created_at DESC",
        (user_id, user_id),
        fetch="all",
    )
    return [Map(**r) for r in rows]


def get_public_maps() -> list[Map]:
    rows = execute(
        "SELECT * FROM maps WHERE is_private = FALSE ORDER BY created_at DESC",
        fetch="all",
    )
    return [Map(**r) for r in rows]


# ── Collaborators ─────────────────────────────────────────────

def add_collaborator(map_id: int, user_id: int) -> None:
    execute(
        "INSERT INTO map_collaborators (map_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (map_id, user_id),
    )


def remove_collaborator(map_id: int, user_id: int) -> None:
    execute(
        "DELETE FROM map_collaborators WHERE map_id = %s AND user_id = %s",
        (map_id, user_id),
    )


def get_collaborators(map_id: int) -> list:
    from models.user import User
    rows = execute(
        "SELECT u.* FROM users u "
        "JOIN map_collaborators mc ON mc.user_id = u.id "
        "WHERE mc.map_id = %s ORDER BY u.username",
        (map_id,),
        fetch="all",
    )
    return [User(**r) for r in rows]


def can_access(user_id: int, m: Map) -> bool:
    if not m.is_private:
        return True
    if m.creator_id == user_id:
        return True
    row = execute(
        "SELECT 1 FROM map_collaborators WHERE map_id = %s AND user_id = %s",
        (m.id, user_id),
        fetch="one",
    )
    return row is not None


def can_pin(user_id: int, m: Map) -> bool:
    """True if user may add pins: must be owner or explicit collaborator."""
    if m.creator_id == user_id:
        return True
    row = execute(
        "SELECT 1 FROM map_collaborators WHERE map_id = %s AND user_id = %s",
        (m.id, user_id),
        fetch="one",
    )
    return row is not None


def is_owner(user_id: int, m: Map) -> bool:
    return m.creator_id == user_id


def get_public_maps_by_owner(owner_id: int) -> list[Map]:
    rows = execute(
        "SELECT * FROM maps WHERE creator_id=%s AND is_private=FALSE ORDER BY created_at DESC",
        (owner_id,), fetch="all",
    )
    return [Map(**r) for r in rows]


def get_friends_maps(user_id: int) -> list[FriendMap]:
    """All maps created by friends that the current user can access
    (their public maps + private maps where user_id is a collaborator)."""
    rows = execute(
        """
        SELECT m.id, m.creator_id, m.title, m.is_private, m.created_at,
               u.username AS friend_username, u.profile_pic_path AS friend_profile_pic
        FROM maps m
        JOIN users u ON u.id = m.creator_id
        WHERE m.creator_id IN (
            SELECT CASE WHEN user_id1 = %s THEN user_id2 ELSE user_id1 END
            FROM friendships
            WHERE (user_id1 = %s OR user_id2 = %s) AND status = 'accepted'
        )
        AND (
            m.is_private = FALSE
            OR EXISTS (
                SELECT 1 FROM map_collaborators mc
                WHERE mc.map_id = m.id AND mc.user_id = %s
            )
        )
        ORDER BY u.username, m.created_at DESC
        """,
        (user_id, user_id, user_id, user_id),
        fetch="all",
    )
    return [FriendMap(**r) for r in rows] if rows else []


def get_private_maps_visible_to(owner_id: int, viewer_id: int) -> list[Map]:
    """Private maps created by owner_id that viewer_id is allowed to see."""
    if owner_id == viewer_id:
        rows = execute(
            "SELECT * FROM maps WHERE creator_id=%s AND is_private=TRUE ORDER BY created_at DESC",
            (owner_id,), fetch="all",
        )
    else:
        rows = execute(
            "SELECT m.* FROM maps m "
            "JOIN map_collaborators mc ON mc.map_id = m.id "
            "WHERE m.creator_id=%s AND m.is_private=TRUE AND mc.user_id=%s "
            "ORDER BY m.created_at DESC",
            (owner_id, viewer_id), fetch="all",
        )
    return [Map(**r) for r in rows]
