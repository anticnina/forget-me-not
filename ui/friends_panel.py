from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox,
    QTabWidget, QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import models.user as user_model
import models.friendship as fs_model
import models.map_invitation as invite_model
from models.user import User

# Item type tags stored in UserRole+1
_TYPE_FRIEND_REQ = "friend_request"
_TYPE_MAP_INVITE = "map_invite"


class FriendsPanel(QWidget):
    """Left-panel widget: friend list, search, and combined requests inbox."""

    friends_changed = pyqtSignal()
    map_created     = pyqtSignal(object)   # emits the new Map when an invite is accepted
    view_profile    = pyqtSignal(object)   # emits User whose profile to open

    def __init__(self, current_user: User, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._build_ui()
        self._apply_style()
        self.refresh()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        header = QLabel("Friends")
        header.setFont(QFont("Nunito", 12, QFont.Weight.Bold))
        root.addWidget(header)

        # Search bar — press Enter to search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users… (press Enter)")
        self.search_input.returnPressed.connect(self._do_search)
        root.addWidget(self.search_input)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Tab 0 – My Friends (click → profile, right-click → context menu)
        self.friends_list = QListWidget()
        self.friends_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.friends_list.customContextMenuRequested.connect(self._friend_context_menu)
        self.friends_list.itemClicked.connect(self._friend_clicked)

        # Tab 1 – Requests (friend requests + map invites combined)
        self.requests_list = QListWidget()
        self.requests_list.itemDoubleClicked.connect(self._handle_request_dclick)

        # Tab 2 – Search results
        self.search_list = QListWidget()
        self.search_list.itemDoubleClicked.connect(self._send_request_from_search)

        self.tabs.addTab(self.friends_list, "My Friends")
        self.tabs.addTab(self.requests_list, "Requests")
        self.tabs.addTab(self.search_list, "Search")

        root.addWidget(self.tabs)

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget { font-size: 13px; }
            QLabel  { font-size: 13px; color: #1B2631; font-weight: bold; }
            QLineEdit {
                border: 1.5px solid #85C1E9; border-radius: 6px;
                padding: 5px 8px; background: #F0F8FF; color: #1B2631;
            }
            QLineEdit:focus { border-color: #1E6FA8; background: white; }
            QListWidget {
                border: 1px solid #85C1E9; border-radius: 6px;
                background: white; color: #1B2631;
            }
            QListWidget::item { padding: 6px 8px; color: #1B2631; }
            QListWidget::item:hover { background: #BED9F0; color: #1B2631; }
            QListWidget::item:selected { background: #7EC8E3; color: #0D2333; }
                    QTabWidget::pane { border: 1px solid #85C1E9; background: white; }
            QTabBar::tab {
                background: #C0DDF0; color: #1B2631; padding: 5px 8px;
                font-size: 12px; font-weight: bold; border-radius: 4px 4px 0 0;
            }
            QTabBar::tab:selected { background: #EAF4FB; color: #0D2333; }
        """)

    # ── Refresh ───────────────────────────────────────────────

    def refresh(self):
        self._load_friends()
        self._load_requests()

    def _load_friends(self):
        self.friends_list.clear()
        for friend in fs_model.get_friends(self.current_user.id):
            item = QListWidgetItem(f"👤 {friend.username}")
            item.setData(Qt.ItemDataRole.UserRole, friend)
            self.friends_list.addItem(item)

    def _load_requests(self):
        self.requests_list.clear()
        count = 0

        # ── Friend requests ───────────────────────────────────
        for row in fs_model.get_pending_incoming(self.current_user.id):
            text = (f"🤝 {row['username']} ({row['first_name']} {row['last_name']})"
                    " wants to be friends  — double-click to accept")
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, _TYPE_FRIEND_REQ)
            self.requests_list.addItem(item)
            count += 1

        # ── Map invitations ───────────────────────────────────
        for inv in invite_model.get_pending_for_user(self.current_user.id):
            text = (f"🗺️ {inv.sender_username} ({inv.sender_first_name} {inv.sender_last_name})"
                    " wants to create a shared map  — double-click to accept")
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, inv)
            item.setData(Qt.ItemDataRole.UserRole + 1, _TYPE_MAP_INVITE)
            self.requests_list.addItem(item)
            count += 1

        tab_label = f"Requests ({count})" if count else "Requests"
        self.tabs.setTabText(1, tab_label)

    # ── Context menu on friends list ──────────────────────────

    def _friend_clicked(self, item: QListWidgetItem):
        friend: User = item.data(Qt.ItemDataRole.UserRole)
        if friend:
            self.view_profile.emit(friend)

    def _friend_context_menu(self, pos):
        item = self.friends_list.itemAt(pos)
        if not item:
            return
        friend: User = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background:#EAF4FB; color:#1B2631; border:1px solid #85C1E9; }"
            "QMenu::item:selected { background:#7EC8E3; }"
        )
        menu.addAction(
            f"👤  View {friend.username}'s profile",
            lambda: self.view_profile.emit(friend),
        )
        menu.addSeparator()
        menu.addAction(
            f"🗺️  Invite {friend.username} to create a shared map",
            lambda: self._send_map_invite(friend),
        )
        menu.addSeparator()
        menu.addAction(
            f"❌  Remove {friend.username} from friends",
            lambda: self._remove_friend(friend),
        )
        menu.exec(self.friends_list.mapToGlobal(pos))

    def _send_map_invite(self, friend: User):
        if invite_model.has_pending_between(self.current_user.id, friend.id):
            QMessageBox.information(
                self, "Already pending",
                f"There is already a pending map invite between you and {friend.username}."
            )
            return
        ok = invite_model.send_invite(self.current_user.id, friend.id)
        if ok:
            QMessageBox.information(
                self, "Invite sent 🗺️",
                f"Map invite sent to {friend.username}!\n"
                "Once they accept, a shared map will be created for both of you."
            )
        else:
            QMessageBox.warning(self, "Could not send", "Invite could not be sent.")

    def _remove_friend(self, friend: User):
        reply = QMessageBox.question(
            self, "Remove Friend",
            f"Remove {friend.username} from your friends?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            fs_model.remove_friendship(self.current_user.id, friend.id)
            self.refresh()
            self.friends_changed.emit()

    # ── Request double-click dispatcher ───────────────────────

    def _handle_request_dclick(self, item: QListWidgetItem):
        item_type = item.data(Qt.ItemDataRole.UserRole + 1)
        if item_type == _TYPE_FRIEND_REQ:
            self._accept_friend_request(item)
        elif item_type == _TYPE_MAP_INVITE:
            self._handle_map_invite(item)

    def _accept_friend_request(self, item: QListWidgetItem):
        requester_id: int = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "Friend Request", "Accept this friend request?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            fs_model.accept_request(requester_id, self.current_user.id)
            self.refresh()
            self.friends_changed.emit()

    def _handle_map_invite(self, item: QListWidgetItem):
        inv = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "Map Invitation",
            f"Accept {inv.sender_username}'s invitation to create a shared map?\n\n"
            "A private shared map will be created automatically for both of you.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            new_map = invite_model.accept_invite(inv)
            QMessageBox.information(
                self, "Map created 🗺️🌸",
                f'Shared map "{new_map.title}" has been created!\n'
                "It now appears under both your Shared Maps."
            )
            self.refresh()
            self.map_created.emit(new_map)
        else:
            reply2 = QMessageBox.question(
                self, "Decline", "Decline this map invitation?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply2 == QMessageBox.StandardButton.Yes:
                invite_model.decline_invite(inv.id)
                self.refresh()

    # ── Search ────────────────────────────────────────────────

    def _do_search(self):
        query = self.search_input.text().strip()
        if len(query) < 2:
            QMessageBox.information(self, "Search", "Enter at least 2 characters.")
            return
        self.search_list.clear()
        results = user_model.search_users(query, self.current_user.id)
        if not results:
            self.search_list.addItem("No users found.")
            self.tabs.setCurrentIndex(2)
            return
        for u in results:
            status_row = fs_model.get_status(self.current_user.id, u.id)
            if status_row:
                badge = {"pending": "⏳", "accepted": "✅", "declined": "❌"}.get(
                    status_row["status"], ""
                )
                label = f"{badge} {u.username}  ({u.full_name})"
            else:
                label = f"➕ {u.username}  ({u.full_name})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, u)
            self.search_list.addItem(item)
        self.tabs.setCurrentIndex(2)

    def _send_request_from_search(self, item: QListWidgetItem):
        user: User = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(user, User):
            return
        status_row = fs_model.get_status(self.current_user.id, user.id)
        if status_row and status_row["status"] == "accepted":
            QMessageBox.information(self, "Already friends",
                                    f"You are already friends with {user.username}.")
            return
        if status_row and status_row["status"] == "pending":
            QMessageBox.information(self, "Pending",
                                    f"A friend request to {user.username} is already pending.")
            return
        fs_model.send_request(self.current_user.id, user.id)
        QMessageBox.information(self, "Request sent",
                                f"Friend request sent to {user.username}! 🌸")
        self._do_search()

    # ── Accessor ──────────────────────────────────────────────

    def get_friends(self) -> list:
        return fs_model.get_friends(self.current_user.id)
