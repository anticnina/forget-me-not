from __future__ import annotations
import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTabWidget, QWidget,
    QFileDialog, QMessageBox, QLineEdit, QMenu, QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

import models.map_model as map_model
import models.user as user_model
from models.map_model import Map
from models.user import User
from utils.avatar import circular_pixmap


# ── Edit own profile ──────────────────────────────────────────

class EditProfileDialog(QDialog):
    profile_updated = pyqtSignal(object)

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self._pic_path = user.profile_pic_path
        self.setWindowTitle("Edit Profile")
        self.setFixedSize(400, 400)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(10)

        # Avatar
        pic_row = QHBoxLayout()
        self.pic_label = QLabel()
        self.pic_label.setFixedSize(72, 72)
        self.pic_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pic_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.pic_label.setStyleSheet("background: transparent; border: none;")
        self._refresh_pic()
        pic_row.addWidget(self.pic_label)
        pic_row.addSpacing(14)
        change_btn = QPushButton("Change Photo")
        change_btn.clicked.connect(self._choose_pic)
        pic_row.addWidget(change_btn)
        pic_row.addStretch()
        root.addLayout(pic_row)

        root.addWidget(QLabel("First name"))
        self.first_input = QLineEdit(self.user.first_name)
        root.addWidget(self.first_input)

        root.addWidget(QLabel("Last name"))
        self.last_input = QLineEdit(self.user.last_name)
        root.addWidget(self.last_input)

        root.addWidget(QLabel("Bio  (optional — a few words about yourself)"))
        self.bio_input = QTextEdit()
        self.bio_input.setPlaceholderText("e.g. Travel lover, memory keeper 🌸")
        self.bio_input.setPlainText(self.user.bio or "")
        self.bio_input.setFixedHeight(64)
        root.addWidget(self.bio_input)

        root.addSpacing(6)
        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save changes")
        save.setObjectName("primary")
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        root.addLayout(btn_row)

    def _refresh_pic(self):
        if self._pic_path and os.path.exists(self._pic_path):
            pix = circular_pixmap(QPixmap(self._pic_path), 72)
            self.pic_label.setPixmap(pix)
            self.pic_label.setText("")
        else:
            self.pic_label.setPixmap(QPixmap())
            self.pic_label.setText("👤")
            self.pic_label.setFont(QFont("Nunito", 26))

    def _choose_pic(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Photo", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self._pic_path = path
            self._refresh_pic()

    def _save(self):
        first = self.first_input.text().strip()
        last  = self.last_input.text().strip()
        if not first or not last:
            QMessageBox.warning(self, "Required", "Please fill in both name fields.")
            return
        bio = self.bio_input.toPlainText().strip() or None
        updated = user_model.update_profile(self.user.id, first, last, self._pic_path, bio)
        self.profile_updated.emit(updated)
        self.accept()

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog   { background: #EAF4FB; }
            QLabel    { color: #1B2631; font-size: 13px; font-weight: bold; }
            QLineEdit, QTextEdit {
                border: 1.5px solid #85C1E9; border-radius: 7px;
                padding: 7px 10px; font-size: 14px;
                background: #F0F8FF; color: #1B2631; }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #1E6FA8; background: white; }
            QPushButton {
                background: white; color: #1E6FA8;
                border: 1.5px solid #85C1E9; border-radius: 7px;
                padding: 6px 14px; font-size: 13px; }
            QPushButton:hover { background: #D4EAF7; }
            QPushButton#primary {
                background: #1E6FA8; color: white;
                border: none; font-weight: bold; }
            QPushButton#primary:hover { background: #155A8A; }
        """)


# ── Profile view ──────────────────────────────────────────────

class ProfileWindow(QDialog):
    open_map        = pyqtSignal(object)   # emits Map
    profile_updated = pyqtSignal(object)   # emits updated User (own only)

    def __init__(self, viewed_user: User, current_user: User,
                 friends: list[User] | None = None, parent=None):
        super().__init__(parent)
        self.viewed_user  = viewed_user
        self.current_user = current_user
        self._friends     = friends or []
        self._is_own      = viewed_user.id == current_user.id
        self.setWindowTitle(f"@{viewed_user.username}")
        self.resize(480, 600)
        self._build_ui()
        self._apply_style()
        self._load_maps()

    # ── Construction ─────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(8)

        # ── Header: avatar + name ─────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(18)

        self._avatar_lbl = QLabel()
        self._avatar_lbl.setFixedSize(80, 80)
        self._avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar_lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._avatar_lbl.setStyleSheet("background: transparent; border: none;")
        self._refresh_avatar()
        header.addWidget(self._avatar_lbl, alignment=Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(2)
        uname_lbl = QLabel(f"@{self.viewed_user.username}")
        uname_lbl.setStyleSheet(
            "font-size:18px; font-weight:bold; color:#0D2333; border:none;")
        info.addWidget(uname_lbl)
        full_lbl = QLabel(self.viewed_user.full_name)
        full_lbl.setStyleSheet(
            "font-size:13px; color:#4A6FA5; font-weight:normal; border:none;")
        info.addWidget(full_lbl)

        # ── Bio sits right under the name ─────────────────────
        self._bio_lbl = QLabel()
        self._bio_lbl.setWordWrap(True)
        self._bio_lbl.setStyleSheet(
            "font-size:12px; color:#1B2631; font-weight:normal;"
            "font-style:italic; padding:0; border:none;")
        self._refresh_bio()
        info.addSpacing(2)
        info.addWidget(self._bio_lbl)
        info.addStretch()

        header.addLayout(info)
        header.addStretch()

        if self._is_own:
            edit_btn = QPushButton("✏️  Edit Profile")
            edit_btn.setObjectName("editBtn")
            edit_btn.clicked.connect(self._edit_profile)
            header.addWidget(edit_btn, alignment=Qt.AlignmentFlag.AlignTop)

        root.addLayout(header)

        # ── Divider ───────────────────────────────────────────
        div = QWidget()
        div.setFixedHeight(1)
        div.setStyleSheet("background:#85C1E9;")
        root.addWidget(div)

        maps_lbl = QLabel("Maps")
        maps_lbl.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#0D2333; border:none;")
        root.addWidget(maps_lbl)

        # ── Tabs ──────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.public_list  = QListWidget()
        self.private_list = QListWidget()

        # Single click opens the map
        self.public_list.itemClicked.connect(self._open_map_item)
        self.private_list.itemClicked.connect(self._open_map_item)

        self.tabs.addTab(self.public_list,  "Public")
        self.tabs.addTab(self.private_list,
                         "Private" if self._is_own else "Shared with me")
        root.addWidget(self.tabs)

        if self._is_own:
            self.private_list.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu)
            self.private_list.customContextMenuRequested.connect(
                self._private_map_menu)

    # ── Avatar & bio refresh ──────────────────────────────────

    def _refresh_avatar(self):
        path = self.viewed_user.profile_pic_path
        if path and os.path.exists(path):
            pix = circular_pixmap(QPixmap(path), 80)
            self._avatar_lbl.setPixmap(pix)
            self._avatar_lbl.setText("")
        else:
            self._avatar_lbl.setPixmap(QPixmap())
            self._avatar_lbl.setText("👤")
            self._avatar_lbl.setFont(QFont("Nunito", 30))

    def _refresh_bio(self):
        bio = self.viewed_user.bio
        if bio:
            self._bio_lbl.setText(bio)
            self._bio_lbl.setVisible(True)
        else:
            self._bio_lbl.setVisible(False)

    # ── Data ─────────────────────────────────────────────────

    def _load_maps(self):
        self.public_list.clear()
        self.private_list.clear()
        for m in map_model.get_public_maps_by_owner(self.viewed_user.id):
            item = QListWidgetItem(f"🌐  {m.title}")
            item.setData(Qt.ItemDataRole.UserRole, m)
            self.public_list.addItem(item)
        for m in map_model.get_private_maps_visible_to(
                self.viewed_user.id, self.current_user.id):
            item = QListWidgetItem(f"🔒  {m.title}")
            item.setData(Qt.ItemDataRole.UserRole, m)
            self.private_list.addItem(item)

    # ── Private-map access management ────────────────────────

    def _private_map_menu(self, pos):
        item = self.private_list.itemAt(pos)
        if not item:
            return
        m: Map = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background:#EAF4FB; color:#1B2631; border:1px solid #85C1E9; }"
            "QMenu::item { padding:6px 20px; }"
            "QMenu::item:selected { background:#7EC8E3; }"
        )
        menu.addAction("👥  Manage who can see this map",
                       lambda: self._manage_access(m))
        menu.exec(self.private_list.mapToGlobal(pos))

    def _manage_access(self, m: Map):
        if not self._friends:
            QMessageBox.information(
                self, "No friends yet",
                "Add friends first to manage who can see this map.")
            return
        from ui.map_view import InviteDialog
        dlg = InviteDialog(m, self.current_user, self._friends, self)
        dlg.exec()

    # ── Open map ─────────────────────────────────────────────

    def _open_map_item(self, item: QListWidgetItem):
        m: Map = item.data(Qt.ItemDataRole.UserRole)
        if m:
            self.open_map.emit(m)
            self.accept()

    # ── Edit own profile ──────────────────────────────────────

    def _edit_profile(self):
        dlg = EditProfileDialog(self.viewed_user, self)
        dlg.profile_updated.connect(self._on_profile_updated)
        dlg.exec()

    def _on_profile_updated(self, updated: User):
        self.viewed_user  = updated
        self.current_user = updated
        self._refresh_avatar()
        self._refresh_bio()
        self.profile_updated.emit(updated)

    # ── Style ─────────────────────────────────────────────────

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog { background: #EAF4FB; }
            QTabWidget::pane { border: 1px solid #85C1E9; background: white; }
            QTabBar::tab { background: #C0DDF0; color: #1B2631; padding: 5px 16px;
                           font-size: 12px; font-weight: bold;
                           border-radius: 4px 4px 0 0; }
            QTabBar::tab:selected { background: #EAF4FB; color: #0D2333; }
            QListWidget { border: none; background: white; color: #1B2631; }
            QListWidget::item { padding: 9px 12px;
                                border-bottom: 1px solid #EAF4FB;
                                color: #1B2631; cursor: pointer; }
            QListWidget::item:hover    { background: #BED9F0; }
            QListWidget::item:selected { background: #7EC8E3; color: #0D2333; }
            QPushButton { background: white; color: #1E6FA8;
                          border: 1.5px solid #85C1E9; border-radius: 7px;
                          padding: 6px 14px; font-size: 13px; }
            QPushButton:hover { background: #D4EAF7; }
            QPushButton#editBtn { font-size: 12px; padding: 5px 12px; }
        """)
