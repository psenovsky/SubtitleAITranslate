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
from subtitle_trans import translate_subtitles


class TranslateWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, subtitles, language_from, language_to, config):
        super().__init__()
        self.subtitles = subtitles
        self.language_from = language_from
        self.language_to = language_to
        self.config = config

    def run(self):
        try:
            result = translate_subtitles(
                subtitles=self.subtitles,
                language_from=self.language_from,
                language_to=self.language_to,
                config=self.config,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class TranslateForm(QMainWindow):
    def __init__(self, config, config_path):
        super().__init__()
        self.config = config
        self.config_path = config_path
        self.worker = None
        self.audio_window = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Subtitle AI Translate")
        self.setMinimumSize(500, 220)

        self._init_menu()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        form = QFormLayout()

        self.source_edit = QLineEdit()
        source_row = QHBoxLayout()
        source_row.addWidget(self.source_edit)
        browse_source = QPushButton("Browse...")
        browse_source.clicked.connect(self._browse_source)
        source_row.addWidget(browse_source)
        source_widget = QWidget()
        source_widget.setLayout(source_row)
        form.addRow("Source subtitle file:", source_widget)

        self.target_edit = QLineEdit()
        target_row = QHBoxLayout()
        target_row.addWidget(self.target_edit)
        browse_target = QPushButton("Browse...")
        browse_target.clicked.connect(self._browse_target)
        target_row.addWidget(browse_target)
        target_widget = QWidget()
        target_widget.setLayout(target_row)
        form.addRow("Target file:", target_widget)

        self.source_lang_edit = QLineEdit("english")
        form.addRow("Source language:", self.source_lang_edit)

        self.target_lang_edit = QLineEdit("czech")
        form.addRow("Target language:", self.target_lang_edit)

        layout.addLayout(form)

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.go_button = QPushButton("GO")
        self.go_button.setMinimumWidth(100)
        self.go_button.setMinimumHeight(36)
        font = self.go_button.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        self.go_button.setFont(font)
        self.go_button.clicked.connect(self._on_go)
        button_row.addWidget(self.go_button)
        button_row.addStretch()
        layout.addLayout(button_row)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def _init_menu(self):
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
        dialog = ConfigForm(self.config, self.config_path, parent=self)
        dialog.exec()

    def _on_audio_subtitle(self):
        if self.audio_window is None:
            self.audio_window = AudioSubtitleForm()
        self.audio_window.show()
        self.audio_window.raise_()
        self.audio_window.activateWindow()

    def _browse_source(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Source Subtitle File", "", "SRT Files (*.srt);;All Files (*)"
        )
        if path:
            self.source_edit.setText(path)

    def _browse_target(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Select Target File", "", "SRT Files (*.srt);;All Files (*)"
        )
        if path:
            self.target_edit.setText(path)

    def _on_go(self):
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

        self.worker = TranslateWorker(subtitles, source_lang, target_lang, self.config)
        self.worker.finished.connect(lambda result: self._on_translation_done(target_path, result))
        self.worker.error.connect(self._on_translation_error)
        self.worker.start()

    def _on_translation_done(self, target_path, result):
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
        QMessageBox.critical(self, "Translation Error", f"Translation failed:\n{error_msg}")
        self.status_label.setText("Translation failed.")
        self.status_label.setStyleSheet("color: red;")
        self.go_button.setEnabled(True)
