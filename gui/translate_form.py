import os

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.audio_subtitle_form import AudioSubtitleForm
from gui.config_form import ConfigForm
from lib.subtitle_trans import translate_subtitles


class TranslateWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, subtitles, language_from, language_to, config, model_name=None):
        """Initialize the translation worker thread.

        Args:
            subtitles: Raw SRT content to translate.
            language_from: Source language name.
            language_to: Target language name.
            config: Parsed configuration file.
            model_name: Optional model name override.
        """
        super().__init__()
        self.subtitles = subtitles
        self.language_from = language_from
        self.language_to = language_to
        self.config = config
        self.model_name = model_name

    def run(self):
        """Run the translation and emit finished or error signal."""
        try:
            result = translate_subtitles(
                subtitles=self.subtitles,
                language_from=self.language_from,
                language_to=self.language_to,
                config=self.config,
                model_name=self.model_name,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class TranslateForm(QMainWindow):
    def __init__(self, config, config_path):
        """Initialize the main translation window.

        Args:
            config: Parsed configuration file.
            config_path: Path to the configuration file on disk.
        """
        super().__init__()
        self.config = config
        self.config_path = config_path
        self.worker = None
        self.audio_window = None
        self._init_ui()

    def _init_ui(self):
        """Build the main translation form layout."""
        self.setWindowTitle("Subtitle AI Translate")
        self.setMinimumSize(520, 240)

        self._init_menu()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Path to .srt file to translate")
        source_row = QHBoxLayout()
        source_row.setSpacing(6)
        source_row.addWidget(self.source_edit)
        browse_source = QPushButton("Browse...")
        browse_source.setToolTip("Select source subtitle file")
        browse_source.clicked.connect(self._browse_source)
        source_row.addWidget(browse_source)
        source_widget = QWidget()
        source_widget.setLayout(source_row)
        form.addRow("Source subtitle file:", source_widget)

        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Path for translated output file")
        target_row = QHBoxLayout()
        target_row.setSpacing(6)
        target_row.addWidget(self.target_edit)
        browse_target = QPushButton("Browse...")
        browse_target.setToolTip("Select target output file")
        browse_target.clicked.connect(self._browse_target)
        target_row.addWidget(browse_target)
        target_widget = QWidget()
        target_widget.setLayout(target_row)
        form.addRow("Target file:", target_widget)

        self.source_lang_edit = QLineEdit("english")
        self.source_lang_edit.setPlaceholderText("e.g. english")
        form.addRow("Source language:", self.source_lang_edit)

        self.target_lang_edit = QLineEdit("czech")
        self.target_lang_edit.setPlaceholderText("e.g. czech")
        form.addRow("Target language:", self.target_lang_edit)

        layout.addLayout(form)

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.go_button = QPushButton("GO")
        self.go_button.setMinimumWidth(100)
        self.go_button.setMinimumHeight(36)
        self.go_button.setStyleSheet(
            "QPushButton { font-weight: bold; font-size: 14px; }"
            "QPushButton:disabled { color: gray; }"
        )
        self.go_button.setToolTip("Start translation")
        self.go_button.clicked.connect(self._on_go)
        button_row.addWidget(self.go_button)
        button_row.addStretch()
        layout.addLayout(button_row)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def _init_menu(self):
        """Create the menu bar with File and Tools menus."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        settings_action = file_menu.addAction("Settings...")
        settings_action.triggered.connect(self._on_settings)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        tools_menu = menu_bar.addMenu("Tools")

        audio_action = tools_menu.addAction("Audio Extract && Subtitle Creator...")
        audio_action.triggered.connect(self._on_audio_subtitle)

    def _on_settings(self):
        """Open the settings dialog."""
        dialog = ConfigForm(self.config, self.config_path, parent=self)
        dialog.exec()

    def _on_audio_subtitle(self):
        """Open or raise the audio extraction and subtitle creation window."""
        if self.audio_window is None:
            self.audio_window = AudioSubtitleForm(self.config)
        self.audio_window.show()
        self.audio_window.raise_()
        self.audio_window.activateWindow()

    def _browse_source(self):
        """Open a file dialog to select the source SRT file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Source Subtitle File", "", "SRT Files (*.srt);;All Files (*)"
        )
        if path:
            self.source_edit.setText(path)

    def _browse_target(self):
        """Open a save file dialog to select the target SRT file path."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Select Target File", "", "SRT Files (*.srt);;All Files (*)"
        )
        if path:
            self.target_edit.setText(path)

    def _on_go(self):
        """Validate inputs and start the translation worker thread."""
        source_path = self.source_edit.text().strip()
        target_path = self.target_edit.text().strip()
        source_lang = self.source_lang_edit.text().strip()
        target_lang = self.target_lang_edit.text().strip()

        if not source_lang or not target_lang:
            QMessageBox.warning(self, "Missing Languages", "Both source and target languages must be set.")
            return

        if not os.path.isfile(source_path):
            QMessageBox.warning(self, "File Not Found", f"Source file does not exist:\n{source_path}")
            return

        if os.path.isfile(target_path):
            reply = QMessageBox.question(
                self,
                "Overwrite File?",
                f"Target file already exists:\n{target_path}\n\nOverwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        try:
            with open(source_path, "r", encoding="utf-8") as f:
                subtitles = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Read Error", f"Could not read source file:\n{e}")
            return

        self.go_button.setEnabled(False)
        self.status_label.setText("Translating...")
        self.status_label.setStyleSheet("color: gray;")

        self.worker = TranslateWorker(subtitles, source_lang, target_lang, self.config, model_name=None)
        self.worker.finished.connect(lambda result: self._on_translation_done(target_path, result))
        self.worker.error.connect(self._on_translation_error)
        self.worker.start()

    def _on_translation_done(self, target_path, result):
        """Write translated content to file and update status.

        Args:
            target_path: Path to the target SRT file.
            result: Translated SRT content string.
        """
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(result)
            self.status_label.setText(f"Translation saved to {target_path}")
            self.status_label.setStyleSheet("color: green;")
        except Exception as e:
            QMessageBox.critical(self, "Write Error", f"Could not write target file:\n{e}")
            self.status_label.setText("Translation completed but save failed.")
            self.status_label.setStyleSheet("color: red;")
        finally:
            self.go_button.setEnabled(True)

    def _on_translation_error(self, error_msg):
        """Handle translation error.

        Args:
            error_msg: Error message string.
        """
        QMessageBox.critical(self, "Translation Error", f"Translation failed:\n{error_msg}")
        self.status_label.setText("Translation failed.")
        self.status_label.setStyleSheet("color: red;")
        self.go_button.setEnabled(True)
