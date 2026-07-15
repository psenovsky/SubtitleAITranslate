import configparser
import os
import sys

from PyQt6.QtWidgets import QApplication

import config_helper
from gui.translate_form import TranslateForm


def main():
    """Launch the GUI application."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
    config.read(config_path)
    config_helper.migrate_old_config(config)
    config_helper.ensure_general_section(config)
    config_helper.ensure_active_model(config)

    app = QApplication(sys.argv)
    window = TranslateForm(config, config_path)
    window.show()
    sys.exit(app.exec())
