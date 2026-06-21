from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import models.user as user_model
from utils.auth import verify_password
from utils.flower import flower_img_tag


class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logged_in_user = None
        self.setWindowTitle("forget me not — Sign In")
        self.setFixedSize(400, 480)
        self.setModal(True)
        self._build_ui()
        self._apply_style()

    # ── UI construction ───────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(0)

        # Header
        title = QLabel(f'{flower_img_tag(30)} forget me not')
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22pt; font-weight: bold; color: #0D2333;")
        root.addWidget(title)

        subtitle = QLabel("Sign in to your account")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("subtitle")
        root.addWidget(subtitle)
        root.addSpacing(30)

        # Username
        root.addWidget(QLabel("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("your_username")
        root.addWidget(self.username_input)
        root.addSpacing(14)

        # Password
        root.addWidget(QLabel("Password"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        root.addWidget(self.password_input)
        root.addSpacing(24)

        # Login button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setObjectName("primary")
        self.login_btn.setFixedHeight(44)
        self.login_btn.clicked.connect(self._on_login)
        root.addWidget(self.login_btn)
        root.addSpacing(12)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)
        root.addSpacing(12)

        # Sign-up link
        signup_row = QHBoxLayout()
        signup_row.addWidget(QLabel("Don't have an account?"))
        self.signup_btn = QPushButton("Create one")
        self.signup_btn.setFlat(True)
        self.signup_btn.setObjectName("link")
        self.signup_btn.clicked.connect(self._on_signup)
        signup_row.addWidget(self.signup_btn)
        signup_row.addStretch()
        root.addLayout(signup_row)

        root.addStretch()

        # Enter key submits
        self.password_input.returnPressed.connect(self._on_login)
        self.username_input.returnPressed.connect(self.password_input.setFocus)

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog { background: #EAF4FB; }
            QLabel  { font-size: 13px; color: #1B2631; margin-bottom: 4px; }
            QLabel#subtitle { color: #4A6FA5; font-size: 13px; margin-bottom: 0; }
            QLineEdit {
                border: 1.5px solid #85C1E9; border-radius: 8px;
                padding: 8px 12px; font-size: 14px;
                background: #F0F8FF; color: #1B2631;
            }
            QLineEdit:focus { border-color: #1E6FA8; background: white; }
            QPushButton#primary {
                background: #1E6FA8; color: white; border: none;
                border-radius: 8px; font-size: 15px; font-weight: bold;
            }
            QPushButton#primary:hover { background: #155A8A; }
            QPushButton#link { color: #1E6FA8; font-size: 13px; font-weight: bold; }
            QFrame[frameShape="4"] { color: #85C1E9; }
        """)

    # ── Slots ─────────────────────────────────────────────────

    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Missing fields", "Please fill in both fields.")
            return

        user = user_model.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            QMessageBox.warning(self, "Sign In Failed", "Invalid username or password.")
            self.password_input.clear()
            return

        self.logged_in_user = user
        self.accept()

    def _on_signup(self):
        from ui.signup_window import SignupWindow
        dlg = SignupWindow(self)
        if dlg.exec():
            self.logged_in_user = dlg.created_user
            self.accept()
