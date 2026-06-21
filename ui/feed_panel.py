from __future__ import annotations

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from models.pin import FeedItem, get_feed_for_user
from models.user import User
from utils.avatar import circular_pixmap


class FeedCard(QFrame):
    # map_id, lat, lng, pin_id
    clicked = pyqtSignal(int, float, float, int)

    def __init__(self, item: FeedItem, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("feedCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._item = item
        self._build(item)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(
                self._item.map_id,
                self._item.latitude,
                self._item.longitude,
                self._item.pin_id,
            )
        super().mousePressEvent(event)

    def _build(self, item: FeedItem):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(8)

        # ── Header: avatar + username + map name + timestamp ──
        top = QHBoxLayout()
        top.setSpacing(10)

        avatar_lbl = QLabel()
        avatar_lbl.setFixedSize(40, 40)
        avatar_lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        avatar_lbl.setStyleSheet("background: transparent; border: none;")
        if item.profile_pic_path and os.path.exists(item.profile_pic_path):
            pix = circular_pixmap(QPixmap(item.profile_pic_path), 40)
            avatar_lbl.setPixmap(pix)
        else:
            avatar_lbl.setText("👤")
            avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(avatar_lbl, alignment=Qt.AlignmentFlag.AlignTop)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        username_lbl = QLabel(f"<b>{item.username}</b>")
        username_lbl.setObjectName("cardUsername")
        info_col.addWidget(username_lbl)

        map_lbl = QLabel(f"🗺️  {item.map_title}")
        map_lbl.setObjectName("cardMap")
        info_col.addWidget(map_lbl)

        top.addLayout(info_col)
        top.addStretch()

        if item.created_at and hasattr(item.created_at, "strftime"):
            ts_str = item.created_at.strftime("%b %d, %Y  %H:%M")
        elif item.created_at:
            ts_str = str(item.created_at)[:16]
        else:
            ts_str = ""
        ts_lbl = QLabel(ts_str)
        ts_lbl.setObjectName("cardTs")
        top.addWidget(ts_lbl, alignment=Qt.AlignmentFlag.AlignTop)

        root.addLayout(top)

        # ── Pin name ──────────────────────────────────────────
        name_lbl = QLabel(item.person_name)
        name_lbl.setObjectName("cardPinName")
        root.addWidget(name_lbl)

        # ── Description ───────────────────────────────────────
        if item.description:
            desc_lbl = QLabel(item.description)
            desc_lbl.setObjectName("cardDesc")
            desc_lbl.setWordWrap(True)
            root.addWidget(desc_lbl)

        # ── Photo ─────────────────────────────────────────────
        if item.image_path and os.path.exists(item.image_path):
            photo_lbl = QLabel()
            pix = QPixmap(item.image_path).scaled(
                300, 220,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            photo_lbl.setPixmap(pix)
            photo_lbl.setObjectName("cardPhoto")
            photo_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            root.addWidget(photo_lbl)


class FeedPanel(QWidget):
    # map_id, lat, lng, pin_id
    post_clicked = pyqtSignal(int, float, float, int)

    def __init__(self, current_user: User, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._build_ui()
        self._apply_style()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar
        header_bar = QWidget()
        header_bar.setObjectName("feedHeader")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(16, 10, 16, 10)

        title = QLabel("Friends' Feed")
        title.setFont(QFont("Nunito", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #0D2333;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.setObjectName("feedRefreshBtn")
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)

        root.addWidget(header_bar)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setObjectName("feedScroll")

        self.container = QWidget()
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(16, 16, 16, 16)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()

        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll)

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget { background: #EAF4FB; font-family: Nunito; }
            QWidget#feedHeader {
                background: #D4EAF7;
                border-bottom: 1px solid #85C1E9;
            }
            QScrollArea#feedScroll { border: none; background: #EAF4FB; }
            QFrame#feedCard {
                background: white;
                border: 1px solid #C8E0F0;
                border-radius: 10px;
            }
            QLabel#cardUsername { font-size: 13px; color: #1B2631; font-weight: bold; }
            QLabel#cardMap       { font-size: 11px; color: #4A6FA5; }
            QLabel#cardPinName   { font-size: 14px; font-weight: bold; color: #0D2333; }
            QLabel#cardDesc      { font-size: 13px; color: #2C3E50; }
            QLabel#cardTs        { font-size: 11px; color: #7F8C8D; }
            QLabel#cardPhoto     { border-radius: 6px; margin-top: 4px; }
            QPushButton#feedRefreshBtn {
                background: white; color: #1E6FA8;
                border: 1.5px solid #85C1E9; border-radius: 6px;
                padding: 4px 12px; font-size: 12px; font-weight: bold;
            }
            QPushButton#feedRefreshBtn:hover { background: #BED9F0; }
        """)

    def refresh(self):
        # Clear existing cards but keep the trailing stretch
        while self.cards_layout.count() > 1:
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        items = get_feed_for_user(self.current_user.id)

        if not items:
            empty = QLabel(
                "No recent activity from friends yet.\n\n"
                "Connect with friends and check back once they plant some memories!"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setWordWrap(True)
            empty.setStyleSheet(
                "color: #7F8C8D; font-size: 14px; padding: 40px; background: transparent;"
            )
            self.cards_layout.insertWidget(0, empty)
            return

        for i, feed_item in enumerate(items):
            card = FeedCard(feed_item)
            card.clicked.connect(self.post_clicked)
            self.cards_layout.insertWidget(i, card)
