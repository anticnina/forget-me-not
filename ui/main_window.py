from __future__ import annotations
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QInputDialog, QMessageBox, QDialog, QCheckBox, QMenu, QStackedWidget,
)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

import os

import models.map_model as map_model
from models.map_model import Map, FriendMap
from models.user import User
from ui.map_view import MapView
from ui.friends_panel import FriendsPanel
from ui.feed_panel import FeedPanel
from ui.profile_window import ProfileWindow
from utils.flower import flower_img_tag
from utils.avatar import circular_pixmap


class CreateMapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Map")
        self.setFixedSize(340, 180)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(10)
        from PyQt6.QtWidgets import QLineEdit
        root.addWidget(QLabel("Map Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Summer Road Trip 2025")
        root.addWidget(self.title_input)
        self.private_cb = QCheckBox("Private map (invite-only)")
        root.addWidget(self.private_cb)
        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Create 🌸")
        ok.setStyleSheet("QPushButton{background:#1E6FA8;color:white;border:none;"
                         "border-radius:7px;padding:7px 18px;font-weight:bold;}"
                         "QPushButton:hover{background:#155A8A;}")
        ok.clicked.connect(self._on_ok)
        btn_row.addWidget(cancel)
        btn_row.addWidget(ok)
        root.addLayout(btn_row)
        self.setStyleSheet(
            "QDialog{background:#EAF4FB;} QLabel{font-size:13px;color:#1B2631;font-weight:bold;}"
            "QLineEdit{border:1.5px solid #85C1E9;border-radius:7px;"
            "padding:7px 10px;font-size:14px;background:#F0F8FF;color:#1B2631;}"
            "QCheckBox{color:#1B2631;font-size:13px;}"
            "QPushButton{background:white;color:#1E6FA8;border:1.5px solid #85C1E9;"
            "border-radius:7px;padding:5px 14px;}"
        )

    def _on_ok(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Title required", "Please enter a map title.")
            return
        self.accept()

    @property
    def title(self) -> str:
        return self.title_input.text().strip()

    @property
    def is_private(self) -> bool:
        return self.private_cb.isChecked()


class FriendMapItemWidget(QWidget):
    """Custom list item showing a friend's avatar + map title."""

    def __init__(self, fm: FriendMap, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        avatar = QLabel()
        avatar.setFixedSize(30, 30)
        avatar.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        if fm.friend_profile_pic and os.path.exists(fm.friend_profile_pic):
            pix = circular_pixmap(QPixmap(fm.friend_profile_pic), 30)
            avatar.setPixmap(pix)
        else:
            avatar.setText("👤")
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(avatar)

        icon = "🔒" if fm.is_private else "🌐"
        title_lbl = QLabel(f"{icon} {fm.title}")
        title_lbl.setStyleSheet("font-size:13px; color:#1B2631; background:transparent;")
        layout.addWidget(title_lbl)
        layout.addStretch()

        self.setStyleSheet("background: transparent;")


class MapListPanel(QWidget):
    """Left-panel section: tabbed map selector + create button."""

    map_deleted = pyqtSignal(int)   # emits deleted map id

    def __init__(self, current_user: User, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._on_map_selected = None
        self._build_ui()

    def set_on_map_selected(self, fn):
        self._on_map_selected = fn

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 4)
        root.setSpacing(6)

        header = QLabel("Maps")
        header.setFont(QFont("Nunito", 12, QFont.Weight.Bold))
        root.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.my_list = QListWidget()
        self.shared_list = QListWidget()
        self.friends_map_list = QListWidget()
        self.friends_map_list.setObjectName("friendsMapList")

        self.tabs.addTab(self.my_list, "Mine")
        self.tabs.addTab(self.shared_list, "Shared")
        self.tabs.addTab(self.friends_map_list, "Friends")

        for lst in (self.my_list, self.shared_list, self.friends_map_list):
            lst.itemClicked.connect(self._item_clicked)

        self.my_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.my_list.customContextMenuRequested.connect(self._my_map_context_menu)

        root.addWidget(self.tabs)

        create_btn = QPushButton("＋ New Map")
        create_btn.setStyleSheet(
            "QPushButton{background:#1E6FA8;color:white;border:none;"
            "border-radius:8px;padding:8px;font-size:13px;font-weight:bold;}"
            "QPushButton:hover{background:#155A8A;}"
        )
        create_btn.clicked.connect(self._create_map)
        root.addWidget(create_btn)

        self.setStyleSheet(
            "QWidget{background:#D4EAF7;}"
            "QLabel{font-size:13px;color:#1B2631;font-weight:bold;}"
            "QTabWidget::pane{border:1px solid #85C1E9;background:white;}"
            "QTabBar::tab{background:#C0DDF0;color:#1B2631;padding:5px 10px;"
            "font-size:12px;font-weight:bold;border-radius:4px 4px 0 0;}"
            "QTabBar::tab:selected{background:#EAF4FB;color:#0D2333;}"
            "QListWidget{border:1px solid #85C1E9;border-radius:6px;background:white;}"
            "QListWidget::item{padding:7px 8px;color:#1B2631;}"
            "QListWidget#friendsMapList::item{padding:0px;color:#1B2631;}"
            "QListWidget::item:hover{background:#BED9F0;color:#1B2631;}"
            "QListWidget::item:selected{background:#7EC8E3;color:#0D2333;}"
        )

    def refresh(self):
        def _fill(lst, maps):
            lst.clear()
            for m in maps:
                icon = "🔒" if m.is_private else "🌐"
                item = QListWidgetItem(f"{icon} {m.title}")
                item.setData(Qt.ItemDataRole.UserRole, m)
                lst.addItem(item)

        _fill(self.my_list, map_model.get_my_maps(self.current_user.id))
        _fill(self.shared_list, map_model.get_shared_maps(self.current_user.id))
        self._fill_friends_maps(map_model.get_friends_maps(self.current_user.id))

    def _fill_friends_maps(self, friend_maps):
        self.friends_map_list.clear()
        for fm in friend_maps:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, fm)
            item.setSizeHint(QSize(0, 46))
            self.friends_map_list.addItem(item)
            self.friends_map_list.setItemWidget(item, FriendMapItemWidget(fm))

    def _item_clicked(self, item: QListWidgetItem):
        m: Map = item.data(Qt.ItemDataRole.UserRole)
        if self._on_map_selected and m:
            self._on_map_selected(m)

    def _my_map_context_menu(self, pos):
        item = self.my_list.itemAt(pos)
        if not item:
            return
        m: Map = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background:#EAF4FB; color:#1B2631; border:1px solid #85C1E9; }"
            "QMenu::item { padding:6px 20px; }"
            "QMenu::item:selected { background:#7EC8E3; }"
        )
        menu.addAction("🗑️  Delete map", lambda: self._delete_map(m))
        menu.exec(self.my_list.mapToGlobal(pos))

    def _delete_map(self, m: Map):
        reply = QMessageBox.question(
            self, "Delete Map",
            f'Delete "{m.title}"?\n\nAll pins on this map will also be deleted. This cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            map_model.delete_map(m.id)
            self.refresh()
            self.map_deleted.emit(m.id)

    def _create_map(self):
        dlg = CreateMapDialog(self)
        if dlg.exec():
            m = map_model.create_map(self.current_user.id, dlg.title, dlg.is_private)
            if m:
                self.refresh()
                if self._on_map_selected:
                    self._on_map_selected(m)


class MainWindow(QMainWindow):
    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.setWindowTitle("🌸 forget me not")
        self.resize(1200, 780)
        self._build_ui()
        self._apply_style()

        # Periodic sidebar refresh to pick up changes from collaborators
        self._sidebar_timer = QTimer(self)
        self._sidebar_timer.setInterval(10000)  # every 10s refresh map lists
        self._sidebar_timer.timeout.connect(self._refresh_sidebar)
        self._sidebar_timer.start()

    # ── UI construction ───────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──────────────────────────────────────────
        top_bar = self._build_top_bar()
        root.addWidget(top_bar)

        # ── Body splitter ────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(270)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        self.map_panel = MapListPanel(self.current_user)
        self.map_panel.set_on_map_selected(self._on_map_selected)
        self.map_panel.map_deleted.connect(self._on_map_deleted)
        sidebar_layout.addWidget(self.map_panel, 3)

        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background:#85C1E9;")
        sidebar_layout.addWidget(divider)

        self.friends_panel = FriendsPanel(self.current_user)
        self.friends_panel.friends_changed.connect(self.map_panel.refresh)
        self.friends_panel.map_created.connect(self._on_shared_map_created)
        self.friends_panel.view_profile.connect(self._open_profile)
        sidebar_layout.addWidget(self.friends_panel, 2)

        splitter.addWidget(sidebar)

        # Right-side stack: Feed (0) is default, Map (1) shown when selected
        self.right_stack = QStackedWidget()

        self.feed_panel = FeedPanel(self.current_user)
        self.feed_panel.post_clicked.connect(self._on_feed_post_clicked)
        self.right_stack.addWidget(self.feed_panel)   # index 0

        self.map_view = MapView(self.current_user)
        self.map_view.set_friends_provider(self.friends_panel.get_friends)
        self.map_view.map_changed.connect(self._refresh_sidebar)
        self.right_stack.addWidget(self.map_view)     # index 1

        self.right_stack.setCurrentIndex(0)           # Feed first

        splitter.addWidget(self.right_stack)

        splitter.setSizes([270, 930])
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter)

        self.map_panel.refresh()

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setObjectName("topBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)

        logo = QLabel(f'{flower_img_tag(22)} forget me not')
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setStyleSheet("font-size:15pt; font-weight:bold; color:#0D2333;")
        layout.addWidget(logo)
        layout.addStretch()

        feed_btn = QPushButton("📰 Feed")
        feed_btn.setObjectName("feedBtn")
        feed_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        feed_btn.clicked.connect(self._show_feed)
        layout.addWidget(feed_btn)

        # Profile avatar (clickable)
        self._avatar_lbl = QLabel()
        self._avatar_lbl.setFixedSize(36, 36)
        self._avatar_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self._avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar_lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._avatar_lbl.setStyleSheet("background: transparent; border: none;")
        self._refresh_top_bar_avatar()
        layout.addWidget(self._avatar_lbl)

        # Username button — opens own profile
        self._user_btn = QPushButton(f"👤 {self.current_user.username}")
        self._user_btn.setFlat(True)
        self._user_btn.setObjectName("userBtn")
        self._user_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._user_btn.clicked.connect(self._open_own_profile)
        layout.addWidget(self._user_btn)

        logout_btn = QPushButton("Sign Out")
        logout_btn.setObjectName("logout")
        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)

        return bar

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background: #EAF4FB; }
            QWidget#topBar { background: #C0DDF0; border-bottom: 2px solid #85C1E9; }
            QPushButton#logout {
                background: white; color: #C0392B;
                border: 1.5px solid #E74C3C; border-radius: 7px;
                padding: 5px 14px; font-size: 13px; font-weight: bold;
            }
            QPushButton#logout:hover { background: #FDECEA; }
            QPushButton#userBtn {
                font-size: 14px; color: #1B2631; font-weight: bold;
                background: transparent; border: none; padding: 4px 6px;
            }
            QPushButton#userBtn:hover { color: #1E6FA8; text-decoration: underline; }
            QPushButton#feedBtn {
                font-size: 13px; color: #1B2631; font-weight: bold;
                background: white; border: 1.5px solid #85C1E9;
                border-radius: 7px; padding: 4px 12px;
            }
            QPushButton#feedBtn:hover { background: #D4EAF7; color: #1E6FA8; }
            QSplitter::handle { background: #85C1E9; width: 1px; }
        """)

    # ── Slots ─────────────────────────────────────────────────

    def _on_map_selected(self, m: Map):
        if not map_model.can_access(self.current_user.id, m):
            QMessageBox.warning(self, "Private Map",
                                "You don't have access to this private map.")
            return
        self.right_stack.setCurrentIndex(1)
        self.map_view.load_map(m)

    def _show_feed(self):
        self.right_stack.setCurrentIndex(0)
        self.feed_panel.refresh()

    def _on_feed_post_clicked(self, map_id: int, lat: float, lng: float, pin_id: int):
        m = map_model.get_by_id(map_id)
        if not m or not map_model.can_access(self.current_user.id, m):
            return
        self.right_stack.setCurrentIndex(1)
        self.map_view.load_map(m, focus=(lat, lng, pin_id))

    def _refresh_top_bar_avatar(self):
        path = self.current_user.profile_pic_path
        if path and os.path.exists(path):
            pix = circular_pixmap(QPixmap(path), 36)
            self._avatar_lbl.setPixmap(pix)
            self._avatar_lbl.setText("")
        else:
            self._avatar_lbl.setPixmap(QPixmap())
            self._avatar_lbl.setText("👤")
            self._avatar_lbl.setStyleSheet("font-size:18px; background: transparent; border: none;")

    def _open_own_profile(self):
        self._open_profile(self.current_user)

    def _open_profile(self, user: User):
        friends = self.friends_panel.get_friends()
        dlg = ProfileWindow(user, self.current_user, friends=friends, parent=self)
        dlg.open_map.connect(self._on_map_selected)
        dlg.profile_updated.connect(self._on_profile_updated)
        dlg.exec()

    def _on_profile_updated(self, updated: User):
        self.current_user = updated
        self._user_btn.setText(f"👤 {updated.username}")
        self._refresh_top_bar_avatar()

    def _on_map_deleted(self, map_id: int):
        if self.map_view.current_map and self.map_view.current_map.id == map_id:
            self.map_view.clear()

    def _on_shared_map_created(self, new_map):
        self._refresh_sidebar()
        self.map_view.load_map(new_map)

    def _refresh_sidebar(self):
        self.map_panel.refresh()
        self.friends_panel.refresh()
        if self.right_stack.currentIndex() == 0:
            self.feed_panel.refresh()

    def _logout(self):
        self.map_view.clear()
        self._sidebar_timer.stop()
        self.close()
        from ui.login_window import LoginWindow
        login = LoginWindow()
        if login.exec() and login.logged_in_user:
            win = MainWindow(login.logged_in_user)
            win.show()
            self._replacement = win

    def closeEvent(self, event):
        self.map_view.refresh_timer.stop()
        self._sidebar_timer.stop()
        super().closeEvent(event)
