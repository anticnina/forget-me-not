from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from database.connection import execute


@dataclass
class User:
    id: int
    first_name: str
    last_name: str
    username: str
    password_hash: str
    profile_pic_path: Optional[str] = None
    bio: Optional[str] = None
    created_at: object = None  # datetime from psycopg2

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


# ── DB helpers ────────────────────────────────────────────────

def create_user(
    first_name: str,
    last_name: str,
    username: str,
    password_hash: str,
    profile_pic_path: Optional[str] = None,
) -> Optional[User]:
    row = execute(
        "INSERT INTO users (first_name, last_name, username, password_hash, profile_pic_path) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING *",
        (first_name, last_name, username, password_hash, profile_pic_path),
        fetch="one",
    )
    return User(**row) if row else None


def get_by_username(username: str) -> Optional[User]:
    row = execute("SELECT * FROM users WHERE username = %s", (username,), fetch="one")
    return User(**row) if row else None


def get_by_id(user_id: int) -> Optional[User]:
    row = execute("SELECT * FROM users WHERE id = %s", (user_id,), fetch="one")
    return User(**row) if row else None


def search_users(query: str, exclude_id: int) -> list[User]:
    rows = execute(
        "SELECT * FROM users WHERE username ILIKE %s AND id != %s ORDER BY username LIMIT 20",
        (f"%{query}%", exclude_id),
        fetch="all",
    )
    return [User(**r) for r in rows]


def update_profile_pic(user_id: int, path: str) -> None:
    execute("UPDATE users SET profile_pic_path = %s WHERE id = %s", (path, user_id))


def update_profile(user_id: int, first_name: str, last_name: str,
                   profile_pic_path: "str | None",
                   bio: "str | None" = None) -> "User":
    execute(
        "UPDATE users SET first_name=%s, last_name=%s, "
        "profile_pic_path=%s, bio=%s WHERE id=%s",
        (first_name, last_name, profile_pic_path, bio or None, user_id),
    )
    return get_by_id(user_id)
