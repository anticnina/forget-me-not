from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

import models.user as user_model
from utils.auth import hash_password
from utils.flower import flower_img_tag


class SignupWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.created_user = None
        self._pic_path: str | None = None
        self.setWindowTitle("forget me not — Create Account")
        self.setFixedSize(440, 620)
        self.setModal(True)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(0)

        title = QLabel(f'{flower_img_tag(28)} Create Account')
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20pt; font-weight: bold; color: #0D2333;")
        root.addWidget(title)
        root.addSpacing(24)

        # Profile picture row
        pic_row = QHBoxLayout()
        self.pic_label = QLabel()
        self.pic_label.setFixedSize(72, 72)
        self.pic_label.setObjectName("picPlaceholder")
        self.pic_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pic_label.setText("👤")
        self.pic_label.setFont(QFont("Nunito", 28))
        pic_row.addWidget(self.pic_label)

        choose_btn = QPushButton("Choose Photo")
        choose_btn.setObjectName("secondary")
        choose_btn.clicked.connect(self._choose_pic)
        pic_row.addSpacing(16)
        pic_row.addWidget(choose_btn)
        pic_row.addStretch()
        root.addLayout(pic_row)
        root.addSpacing(20)

        # Name row
        name_row = QHBoxLayout()
        name_row.setSpacing(12)
        first_col = QVBoxLayout()
        first_col.addWidget(QLabel("First Name"))
        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("Jane")
        first_col.addWidget(self.first_name)

        last_col = QVBoxLayout()
        last_col.addWidget(QLabel("Last Name"))
        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("Doe")
        last_col.addWidget(self.last_name)

        name_row.addLayout(first_col)
        name_row.addLayout(last_col)
        root.addLayout(name_row)
        root.addSpacing(14)

        # Username
        root.addWidget(QLabel("Username  (unique, no spaces)"))
        self.username = QLineEdit()
        self.username.setPlaceholderText("jane_doe")
        root.addWidget(self.username)
        root.addSpacing(14)

        # Password
        root.addWidget(QLabel("Password  (min 6 characters)"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("••••••••")
        root.addWidget(self.password)
        root.addSpacing(14)

        # Confirm password
        root.addWidget(QLabel("Confirm Password"))
        self.confirm = QLineEdit()
        self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm.setPlaceholderText("••••••••")
        root.addWidget(self.confirm)
        root.addSpacing(28)

        # Submit
        btn = QPushButton("Create Account")
        btn.setObjectName("primary")
        btn.setFixedHeight(44)
        btn.clicked.connect(self._on_submit)
        root.addWidget(btn)
        root.addStretch()

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog { background: #EAF4FB; }
            QLabel  { font-size: 13px; color: #1B2631; margin-bottom: 3px; }
            QLabel#picPlaceholder {
                border: 2px dashed #85C1E9; border-radius: 36px;
                background: #D4EAF7;
            }
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
            QPushButton#secondary {
                background: white; color: #1E6FA8;
                border: 1.5px solid #1E6FA8; border-radius: 8px;
                padding: 6px 14px; font-size: 13px; font-weight: bold;
            }
        """)

    # ── Slots ─────────────────────────────────────────────────

    def _choose_pic(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Profile Picture", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if path:
            self._pic_path = path
            pix = QPixmap(path).scaled(
                72, 72,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.pic_label.setPixmap(pix)
            self.pic_label.setText("")

    def _on_submit(self):
        first = self.first_name.text().strip()
        last = self.last_name.text().strip()
        uname = self.username.text().strip().lower()
        pwd = self.password.text()
        cpwd = self.confirm.text()

        # Validation
        if not all([first, last, uname, pwd]):
            QMessageBox.warning(self, "Missing fields", "All fields except photo are required.")
            return
        if " " in uname:
            QMessageBox.warning(self, "Invalid username", "Username cannot contain spaces.")
            return
        if len(pwd) < 6:
            QMessageBox.warning(self, "Weak password", "Password must be at least 6 characters.")
            return
        if pwd != cpwd:
            QMessageBox.warning(self, "Password mismatch", "Passwords do not match.")
            return
        if user_model.get_by_username(uname):
            QMessageBox.warning(self, "Username taken", f'"{uname}" is already in use.')
            return

        user = user_model.create_user(first, last, uname, hash_password(pwd), self._pic_path)
        if user:
            self.created_user = user
            QMessageBox.information(self, "Welcome!", f"Account created. Welcome, {first}! 🌸")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Could not create account. Please try again.")
