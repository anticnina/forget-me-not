"""
Forget Me Not — entry point.

Usage:
    python main.py

Prerequisites:
    1. pip install -r requirements.txt
    2. Create DB:  CREATE DATABASE forget_me_not;
    3. Run schema: psql -U postgres -d forget_me_not -f database/schema.sql
       (or paste schema.sql into pgAdmin 4 Query Tool and hit F5)
    4. Adjust config.ini if your PostgreSQL credentials differ.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase
# Must be imported before QApplication is instantiated
from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401

_FONTS_DIR = Path(__file__).parent / "assets" / "fonts"


def main():
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("forget me not")
    app.setOrganizationName("ForgetMeNot")

    # Load and register Nunito (variable font — one file covers all weights)
    for ttf in _FONTS_DIR.glob("Nunito*.ttf"):
        QFontDatabase.addApplicationFont(str(ttf))
    app.setFont(QFont("Nunito", 13))

    # Verify DB connection early so the user gets a clear error
    try:
        from database.connection import get_connection, execute as db_exec
        get_connection()
        # Graceful schema migration: add columns that may not exist yet
        try:
            db_exec("ALTER TABLE users ADD COLUMN bio TEXT")
        except Exception:
            pass  # column already present
    except Exception as exc:
        QMessageBox.critical(
            None, "Database Error",
            f"Could not connect to PostgreSQL:\n\n{exc}\n\n"
            "Check config.ini and make sure PostgreSQL is running."
        )
        sys.exit(1)

    from ui.login_window import LoginWindow
    from ui.main_window import MainWindow

    login = LoginWindow()
    if login.exec() != LoginWindow.DialogCode.Accepted or not login.logged_in_user:
        sys.exit(0)

    window = MainWindow(login.logged_in_user)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
