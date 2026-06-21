from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from models.pin import create_pin


class PinDialog(QDialog):
    """Dialog shown when the user clicks a spot on the map."""

    def __init__(self, lat: float, lng: float, map_id: int, creator_id: int, parent=None):
        super().__init__(parent)
        self.lat = lat
        self.lng = lng
        self.map_id = map_id
        self.creator_id = creator_id
        self._image_path: str | None = None
        self.created_pin = None

        self.setWindowTitle("Add Memory Marker 🌸")
        self.setFixedSize(400, 480)
        self.setModal(True)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(10)

        coords = QLabel(f"📍 {self.lat:.5f}, {self.lng:.5f}")
        coords.setObjectName("coords")
        root.addWidget(coords)

        root.addWidget(QLabel("Person / Memory Name  *"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Grandma's favourite bench")
        root.addWidget(self.name_input)

        root.addWidget(QLabel("Description"))
        self.desc_input = QTextEdit()
        self.desc_input.setFixedHeight(100)
        self.desc_input.setPlaceholderText("What happened here? What do you want to remember?")
        root.addWidget(self.desc_input)

        root.addWidget(QLabel("Photo  (optional)"))
        photo_row = QHBoxLayout()
        self.photo_preview = QLabel("No photo")
        self.photo_preview.setObjectName("photoPreview")
        self.photo_preview.setFixedSize(80, 60)
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_row.addWidget(self.photo_preview)
        choose_photo = QPushButton("Browse…")
        choose_photo.setObjectName("secondary")
        choose_photo.clicked.connect(self._choose_photo)
        photo_row.addWidget(choose_photo)
        photo_row.addStretch()
        root.addLayout(photo_row)

        root.addStretch()

        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("secondary")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Plant Memory 🌸")
        save.setObjectName("primary")
        save.setFixedHeight(40)
        save.clicked.connect(self._on_save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        root.addLayout(btn_row)

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog { background: #EAF4FB; }
            QLabel  { font-size: 13px; color: #1B2631; }
            QLabel#coords { color: #4A6FA5; font-size: 12px; font-weight: bold; margin-bottom: 6px; }
            QLabel#photoPreview {
                border: 1.5px dashed #85C1E9; border-radius: 6px;
                background: #D4EAF7; color: #4A6FA5; font-size: 11px;
            }
            QLineEdit, QTextEdit {
                border: 1.5px solid #85C1E9; border-radius: 8px;
                padding: 8px 10px; font-size: 14px;
                background: #F0F8FF; color: #1B2631;
            }
            QLineEdit:focus, QTextEdit:focus { border-color: #1E6FA8; background: white; }
            QPushButton#primary {
                background: #1E6FA8; color: white; border: none;
                border-radius: 8px; font-size: 14px; font-weight: bold;
                padding: 6px 20px;
            }
            QPushButton#primary:hover { background: #155A8A; }
            QPushButton#secondary {
                background: white; color: #1E6FA8;
                border: 1.5px solid #1E6FA8; border-radius: 8px;
                padding: 6px 14px; font-size: 13px; font-weight: bold;
            }
        """)

    def _choose_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Photo", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if path:
            self._image_path = path
            pix = QPixmap(path).scaled(
                80, 60,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.photo_preview.setPixmap(pix)

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Name required", "Please enter a name for this memory.")
            return

        desc = self.desc_input.toPlainText().strip() or None
        pin = create_pin(
            self.map_id, self.creator_id,
            self.lat, self.lng,
            name, desc, self._image_path,
        )
        if pin:
            self.created_pin = pin
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Could not save marker. Please try again.")
