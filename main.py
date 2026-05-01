import sys

from PyQt6.QtWidgets import QApplication

import database as db
from login_window import LoginWindow


def main():
    db.init_db()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
