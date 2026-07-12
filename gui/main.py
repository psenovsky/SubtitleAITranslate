import configparser
import os
import sys

from PyQt6.QtWidgets import QApplication

from gui.translate_form import TranslateForm


def main():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
    config.read(config_path)

    app = QApplication(sys.argv)
    window = TranslateForm(config)
    window.show()
    sys.exit(app.exec())
