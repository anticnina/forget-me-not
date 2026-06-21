from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from database.connection import execute


@dataclass
class MapInvitation:
    id: int
    sender_id: int
    recipient_id: int
    status: str
    map_id: Optional[int] = None
    created_at: object = None
    # joined fields (set when fetched with user info)
    sender_username: str = ""
    sender_first_name: str = ""
    sender_last_name: str = ""


def send_invite(sender_id: int, recipient_id: int) -> bool:
    """
    Send a map-creation invite. Returns False if a pending invite already
    exists in either direction between these two users.
    """
    existing = execute(
        "SELECT 1 FROM map_invitations "
        "WHERE status = 'pending' "
        "  AND ((sender_id = %s AND recipient_id = %s) "
        "    OR (sender_id = %s AND recipient_id = %s))",
        (sender_id, recipient_id, recipient_id, sender_id),
        fetch="one",
    )
    if existing:
        return False
    execute(
        "INSERT INTO map_invitations (sender_id, recipient_id) VALUES (%s, %s)",
        (sender_id, recipient_id),
    )
    return True


def get_pending_for_user(user_id: int) -> list[MapInvitation]:
    """All pending invites where user_id is the recipient."""
    rows = execute(
        "SELECT mi.*, u.username AS sender_username, "
        "       u.first_name AS sender_first_name, u.last_name AS sender_last_name "
        "FROM map_invitations mi "
        "JOIN users u ON u.id = mi.sender_id "
        "WHERE mi.recipient_id = %s AND mi.status = 'pending' "
        "ORDER BY mi.created_at DESC",
        (user_id,),
        fetch="all",
    )
    return [
        MapInvitation(
            id=r["id"], sender_id=r["sender_id"], recipient_id=r["recipient_id"],
            status=r["status"], map_id=r["map_id"], created_at=r["created_at"],
            sender_username=r["sender_username"],
            sender_first_name=r["sender_first_name"],
            sender_last_name=r["sender_last_name"],
        )
        for r in rows
    ]


def accept_invite(invite: MapInvitation) -> "Map":  # type: ignore[name-defined]
    """
    Accept the invite: auto-create a shared private map named after both users,
    make the sender its owner, add the recipient as collaborator, and mark
    the invite as accepted.
    """
    from models.user import get_by_id
    from models.map_model import create_map, add_collaborator

    sender = get_by_id(invite.sender_id)
    recipient = get_by_id(invite.recipient_id)

    title = f"{sender.username} & {recipient.username}'s Map"
    new_map = create_map(invite.sender_id, title, is_private=True)

    # Both users are collaborators (sender is also creator, so always has access)
    add_collaborator(new_map.id, invite.recipient_id)

    execute(
        "UPDATE map_invitations SET status = 'accepted', map_id = %s WHERE id = %s",
        (new_map.id, invite.id),
    )
    return new_map


def decline_invite(invite_id: int) -> None:
    execute(
        "UPDATE map_invitations SET status = 'declined' WHERE id = %s", (invite_id,)
    )


def has_pending_between(user_a: int, user_b: int) -> bool:
    row = execute(
        "SELECT 1 FROM map_invitations WHERE status = 'pending' "
        "AND ((sender_id = %s AND recipient_id = %s) "
        "  OR (sender_id = %s AND recipient_id = %s))",
        (user_a, user_b, user_b, user_a),
        fetch="one",
    )
    return row is not None
