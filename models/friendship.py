from __future__ import annotations
from typing import Optional
from database.connection import execute


def _ordered(a: int, b: int) -> tuple[int, int]:
    return (min(a, b), max(a, b))


def send_request(from_id: int, to_id: int) -> None:
    u1, u2 = _ordered(from_id, to_id)
    execute(
        "INSERT INTO friendships (user_id1, user_id2, requester_id, status) "
        "VALUES (%s, %s, %s, 'pending') ON CONFLICT DO NOTHING",
        (u1, u2, from_id),
    )


def accept_request(from_id: int, to_id: int) -> None:
    u1, u2 = _ordered(from_id, to_id)
    execute(
        "UPDATE friendships SET status = 'accepted' WHERE user_id1 = %s AND user_id2 = %s",
        (u1, u2),
    )


def decline_request(from_id: int, to_id: int) -> None:
    u1, u2 = _ordered(from_id, to_id)
    execute(
        "UPDATE friendships SET status = 'declined' WHERE user_id1 = %s AND user_id2 = %s",
        (u1, u2),
    )


def remove_friendship(user_id: int, other_id: int) -> None:
    u1, u2 = _ordered(user_id, other_id)
    execute(
        "DELETE FROM friendships WHERE user_id1 = %s AND user_id2 = %s", (u1, u2)
    )


def get_status(user_id: int, other_id: int) -> Optional[dict]:
    u1, u2 = _ordered(user_id, other_id)
    return execute(
        "SELECT * FROM friendships WHERE user_id1 = %s AND user_id2 = %s",
        (u1, u2),
        fetch="one",
    )


def get_friends(user_id: int) -> list:
    from models.user import User
    rows = execute(
        "SELECT u.* FROM users u "
        "JOIN friendships f ON (f.user_id1 = u.id OR f.user_id2 = u.id) "
        "WHERE (f.user_id1 = %s OR f.user_id2 = %s) "
        "  AND f.status = 'accepted' AND u.id != %s "
        "ORDER BY u.username",
        (user_id, user_id, user_id),
        fetch="all",
    )
    return [User(**r) for r in rows]


def get_pending_incoming(user_id: int) -> list[dict]:
    """Requests sent *to* user_id that are still pending."""
    return execute(
        "SELECT u.id, u.username, u.first_name, u.last_name, u.profile_pic_path "
        "FROM users u "
        "JOIN friendships f ON f.requester_id = u.id "
        "WHERE ((f.user_id1 = %s AND f.user_id2 = u.id) "
        "    OR (f.user_id2 = %s AND f.user_id1 = u.id)) "
        "  AND f.status = 'pending' AND f.requester_id != %s",
        (user_id, user_id, user_id),
        fetch="all",
    ) or []
