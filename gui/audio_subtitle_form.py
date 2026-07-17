import os

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lib.audio_extract import check_ffmpeg, extract_audio, generate_output_path, get_audio_streams
from lib.whisper_transcribe import (
    load_iso639_data,
    load_whisper_support,
    segments_to_srt,
    transcribe_audio,
    validate_audio_filename,
)


class ExtractWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(int, list)
    error = pyqtSignal(str)

    def __init__(self, video_path, streams, output_dir):
        """Initialize the extraction worker thread.

        Args:
            video_path: Path to the source video file.
            streams: List of audio stream dicts to extract.
            output_dir: Directory to save extracted audio files.
        """
        super().__init__()
        self.video_path = video_path
        self.streams = streams
        self.output_dir = output_dir

    def run(self):
        """Extract each audio stream and emit progress/finished/error signals."""
        extracted = []
        for s in self.streams:
            lang = s["language"]
            out_path = generate_output_path(self.video_path, lang, self.output_dir)
            self.progress.emit(f"Extracting stream {s['index']} ({lang})...")
            if extract_audio(self.video_path, s["index"], out_path):
                extracted.append(out_path)
            else:
                self.error.emit(f"Failed to extract stream {s['index']} ({lang}).")
                return
        self.finished.emit(len(extracted), extracted)


class TranscribeWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, audio_path, language_name, output_path):
        """Initialize the transcription worker thread.

        Args:
            audio_path: Path to the WAV audio file to transcribe.
            language_name: Language name for Whisper transcription.
            output_path: Path where the generated SRT file will be saved.
        """
        super().__init__()
        self.audio_path = audio_path
        self.language_name = language_name
        self.output_path = output_path

    def run(self):
        """Transcribe audio with Whisper and emit progress/finished/error signals."""
        try:
            self.progress.emit(f"Transcribing with Whisper (large model)...")
            segments = transcribe_audio(self.audio_path, self.language_name)
            self.progress.emit(f"Generated {len(segments)} subtitle segments")
            srt_content = segments_to_srt(segments)
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


class AudioSubtitleForm(QMainWindow):
    def __init__(self):
        """Initialize the main audio extraction and subtitle creation window."""
        super().__init__()
        self.extract_worker = None
        self.transcribe_worker = None
        self.streams = []
        self.iso639_data = {}
        self.whisper_supported = set()
        self._load_language_data()
        self._init_ui()

    def _project_root(self):
        """Return the absolute path to the project root directory."""
        return os.path.join(os.path.dirname(__file__), "..")

    def _load_language_data(self):
        """Load ISO 639 and Whisper language data from CSV files."""
        data_dir = os.path.join(self._project_root(), "data")
        try:
            self.iso639_data = load_iso639_data(data_dir)
            self.whisper_supported = load_whisper_support(data_dir)
        except Exception:
            pass
        self._whisper_languages = self._build_whisper_languages()

    def _build_whisper_languages(self):
        """Build sorted list of (name, code_639_2) for Whisper-supported languages."""
        languages = []
        for code_639_2, (code_639_1, name) in self.iso639_data.items():
            if code_639_1 in self.whisper_supported:
                languages.append((name, code_639_2))
        languages.sort(key=lambda x: x[0].lower())
        return languages

    def _init_ui(self):
        """Build the main window layout with extract and transcribe groups."""
        self.setWindowTitle("Audio Extract & Subtitle Creator")
        self.setMinimumSize(620, 540)

        self._init_menu()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 8, 12, 8)

        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        splitter.addWidget(self._build_extract_group())
        splitter.addWidget(self._build_transcribe_group())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

    def _init_menu(self):
        """Create the menu bar with File > Exit action."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

    def _build_extract_group(self):
        """Build the 'Extract Audio from Video' group box with all controls.

        Returns:
            The constructed QGroupBox widget.
        """
        group = QGroupBox("Extract Audio from Video")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        form = QFormLayout()
        form.setSpacing(6)

        self.video_edit = QLineEdit()
        self.video_edit.setPlaceholderText("Path to video file (.mkv, .mp4, etc.)")
        video_row = QHBoxLayout()
        video_row.setSpacing(6)
        video_row.addWidget(self.video_edit)
        browse_video = QPushButton("Browse...")
        browse_video.setToolTip("Select video file")
        browse_video.clicked.connect(self._browse_video)
        video_row.addWidget(browse_video)
        video_widget = QWidget()
        video_widget.setLayout(video_row)
        form.addRow("Video file:", video_widget)

        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Output directory (defaults to video location)")
        output_row = QHBoxLayout()
        output_row.setSpacing(6)
        output_row.addWidget(self.output_dir_edit)
        browse_output = QPushButton("Browse...")
        browse_output.setToolTip("Select output directory")
        browse_output.clicked.connect(self._browse_output_dir)
        output_row.addWidget(browse_output)
        output_widget = QWidget()
        output_widget.setLayout(output_row)
        form.addRow("Output directory:", output_widget)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.detect_button = QPushButton("Detect Streams")
        self.detect_button.setToolTip("Scan video for audio streams")
        self.detect_button.clicked.connect(self._on_detect)
        btn_row.addWidget(self.detect_button)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.streams_table = QTableWidget()
        self.streams_table.setColumnCount(6)
        self.streams_table.setHorizontalHeaderLabels(
            ["Language", "Override", "Codec", "Channels", "Duration", "Bitrate"]
        )
        self.streams_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.streams_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.streams_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.streams_table.setMinimumHeight(120)
        layout.addWidget(self.streams_table)

        extract_row = QHBoxLayout()
        extract_row.setSpacing(6)
        self.extract_all_button = QPushButton("Extract All")
        self.extract_all_button.setToolTip("Extract all detected audio streams")
        self.extract_all_button.setEnabled(False)
        self.extract_all_button.clicked.connect(self._on_extract_all)
        extract_row.addWidget(self.extract_all_button)
        self.extract_selected_button = QPushButton("Extract Selected")
        self.extract_selected_button.setToolTip("Extract only checked streams")
        self.extract_selected_button.setEnabled(False)
        self.extract_selected_button.clicked.connect(self._on_extract_selected)
        extract_row.addWidget(self.extract_selected_button)
        extract_row.addStretch()
        layout.addLayout(extract_row)

        self.extract_status = QLabel("")
        self.extract_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.extract_status)

        return group

    def _build_transcribe_group(self):
        """Build the 'Transcribe Audio to SRT' group box with all controls.

        Returns:
            The constructed QGroupBox widget.
        """
        group = QGroupBox("Transcribe Audio to SRT")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        form = QFormLayout()
        form.setSpacing(6)

        self.audio_edit = QLineEdit()
        self.audio_edit.setPlaceholderText("Path to WAV audio file")
        audio_row = QHBoxLayout()
        audio_row.setSpacing(6)
        audio_row.addWidget(self.audio_edit)
        browse_audio = QPushButton("Browse...")
        browse_audio.setToolTip("Select WAV audio file")
        browse_audio.clicked.connect(self._browse_audio)
        audio_row.addWidget(browse_audio)
        audio_widget = QWidget()
        audio_widget.setLayout(audio_row)
        form.addRow("Audio file:", audio_widget)

        self.lang_info_label = QLabel("")
        form.addRow("Detected language:", self.lang_info_label)

        self.audio_edit.textChanged.connect(self._on_audio_path_changed)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.transcribe_button = QPushButton("Transcribe")
        self.transcribe_button.setToolTip("Transcribe audio to SRT subtitles")
        self.transcribe_button.setEnabled(False)
        self.transcribe_button.clicked.connect(self._on_transcribe)
        btn_row.addWidget(self.transcribe_button)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.transcribe_status = QLabel("")
        self.transcribe_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.transcribe_status)

        return group

    def _browse_video(self):
        """Open a file dialog to select a video file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mkv *.mp4 *.avi *.mov *.ts *.flv);;All Files (*)",
        )
        if path:
            self.video_edit.setText(path)
            if not self.output_dir_edit.text().strip():
                self.output_dir_edit.setText(os.path.dirname(path))

    def _browse_output_dir(self):
        """Open a directory dialog to select the output directory."""
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self.output_dir_edit.setText(path)

    def _browse_audio(self):
        """Open a file dialog to select a WAV audio file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "WAV Files (*.wav);;All Files (*)",
        )
        if path:
            self.audio_edit.setText(path)

    def _on_detect(self):
        """Detect audio streams in the selected video file and populate the table."""
        video_path = self.video_edit.text().strip()
        if not video_path:
            QMessageBox.warning(self, "No File", "Please select a video file.")
            return
        if not os.path.isfile(video_path):
            QMessageBox.warning(self, "File Not Found", f"Video file does not exist:\n{video_path}")
            return
        if not check_ffmpeg():
            QMessageBox.critical(
                self,
                "ffmpeg Not Found",
                "ffmpeg and ffprobe must be installed and on PATH.",
            )
            return

        self.detect_button.setEnabled(False)
        self.extract_status.setText("Detecting audio streams...")
        self.extract_status.setStyleSheet("color: gray;")

        self.streams_table.setRowCount(0)
        self.extract_all_button.setEnabled(False)
        self.extract_selected_button.setEnabled(False)

        streams = get_audio_streams(video_path)
        self.detect_button.setEnabled(True)

        if not streams:
            self.extract_status.setText("No audio streams found.")
            self.extract_status.setStyleSheet("color: red;")
            return

        self.streams = streams
        self.streams_table.setRowCount(len(streams))
        for i, s in enumerate(streams):
            self.streams_table.setItem(i, 0, QTableWidgetItem(s["language"]))
            self.streams_table.item(i, 0).setCheckState(Qt.CheckState.Checked)

            override_combo = QComboBox()
            override_combo.addItem("— use detected —", "")
            detected_code2 = s["language"]
            detected_index = 0
            for idx, (name, code2) in enumerate(self._whisper_languages, 1):
                override_combo.addItem(f"{name} ({code2})", code2)
                if code2 == detected_code2:
                    detected_index = idx
            override_combo.setCurrentIndex(detected_index)
            self.streams_table.setCellWidget(i, 1, override_combo)

            self.streams_table.setItem(i, 2, QTableWidgetItem(s["codec_name"]))
            self.streams_table.setItem(i, 3, QTableWidgetItem(str(s["channels"])))
            duration = s["duration"]
            if duration != "N/A" and "." in duration:
                duration = duration.split(".")[0]
            self.streams_table.setItem(i, 4, QTableWidgetItem(duration))
            self.streams_table.setItem(i, 5, QTableWidgetItem(str(s["bit_rate"])))

        self.extract_all_button.setEnabled(True)
        self.extract_selected_button.setEnabled(True)
        self.extract_status.setText(f"Found {len(streams)} audio stream(s). Select streams and extract.")
        self.extract_status.setStyleSheet("color: green;")

    def _get_selected_streams(self):
        """Return a list of stream dicts for checked rows, with language overrides applied.

        Returns:
            List of selected audio stream dictionaries.
        """
        selected = []
        for i in range(self.streams_table.rowCount()):
            item = self.streams_table.item(i, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                stream = dict(self.streams[i])
                combo = self.streams_table.cellWidget(i, 1)
                if combo and combo.currentData():
                    stream["language"] = combo.currentData()
                selected.append(stream)
        return selected

    def _on_extract_all(self):
        """Handle 'Extract All' button click."""
        self._start_extraction(self.streams)

    def _on_extract_selected(self):
        """Handle 'Extract Selected' button click."""
        selected = self._get_selected_streams()
        if not selected:
            QMessageBox.warning(self, "No Selection", "No streams selected for extraction.")
            return
        self._start_extraction(selected)

    def _start_extraction(self, streams):
        """Validate output, confirm overwrite, and start the extraction worker.

        Args:
            streams: List of audio stream dicts to extract.
        """
        video_path = self.video_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip() or os.path.dirname(video_path)

        if os.path.isdir(output_dir):
            reply = QMessageBox.question(
                self,
                "Overwrite Files?",
                f"Extracted files will be saved to:\n{output_dir}\n\nExisting files with the same name will be overwritten.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.extract_all_button.setEnabled(False)
        self.extract_selected_button.setEnabled(False)
        self.detect_button.setEnabled(False)

        self.extract_worker = ExtractWorker(video_path, streams, output_dir)
        self.extract_worker.progress.connect(self._on_extract_progress)
        self.extract_worker.finished.connect(self._on_extract_done)
        self.extract_worker.error.connect(self._on_extract_error)
        self.extract_worker.start()

    def _on_extract_progress(self, msg):
        """Update the status label with an extraction progress message.

        Args:
            msg: Progress message string.
        """
        self.extract_status.setText(msg)
        self.extract_status.setStyleSheet("color: gray;")

    def _on_extract_done(self, count, files):
        """Handle successful extraction completion.

        Args:
            count: Number of files extracted.
            files: List of extracted file paths.
        """
        self.extract_status.setText(f"Extracted {count} file(s) successfully.")
        self.extract_status.setStyleSheet("color: green;")
        self.extract_all_button.setEnabled(True)
        self.extract_selected_button.setEnabled(True)
        self.detect_button.setEnabled(True)
        if files:
            last = files[-1]
            self.audio_edit.setText(last)

    def _on_extract_error(self, msg):
        """Handle extraction error.

        Args:
            msg: Error message string.
        """
        QMessageBox.critical(self, "Extraction Error", msg)
        self.extract_status.setText("Extraction failed.")
        self.extract_status.setStyleSheet("color: red;")
        self.extract_all_button.setEnabled(True)
        self.extract_selected_button.setEnabled(True)
        self.detect_button.setEnabled(True)

    def _on_audio_path_changed(self, path):
        """Validate the audio path and update language detection.

        Args:
            path: New audio file path from the text field.
        """
        path = path.strip()
        self.lang_info_label.setText("")
        self.transcribe_button.setEnabled(False)

        if not path or not path.endswith(".wav"):
            return

        filename = os.path.basename(path)
        try:
            video_name, code2, code1, name = validate_audio_filename(filename, self.iso639_data)
        except ValueError:
            self.lang_info_label.setText("Invalid filename format (expected: name.lang.wav)")
            self.lang_info_label.setStyleSheet("color: red;")
            return

        if code1 not in self.whisper_supported:
            self.lang_info_label.setText(f"{name} - not supported by Whisper")
            self.lang_info_label.setStyleSheet("color: red;")
            return

        self.lang_info_label.setText(f"{name} ({code2}/{code1})")
        self.lang_info_label.setStyleSheet("color: green;")
        self.transcribe_button.setEnabled(True)

    def _on_transcribe(self):
        """Validate inputs and start the transcription worker thread."""
        audio_path = self.audio_edit.text().strip()
        if not audio_path or not os.path.isfile(audio_path):
            QMessageBox.warning(self, "File Not Found", f"Audio file does not exist:\n{audio_path}")
            return

        filename = os.path.basename(audio_path)
        try:
            video_name, code2, code1, language_name = validate_audio_filename(filename, self.iso639_data)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Filename", str(e))
            return

        output_path = os.path.splitext(audio_path)[0] + ".srt"
        if os.path.isfile(output_path):
            reply = QMessageBox.question(
                self,
                "Overwrite File?",
                f"SRT file already exists:\n{output_path}\n\nOverwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.transcribe_button.setEnabled(False)
        self.transcribe_status.setText("Transcribing...")
        self.transcribe_status.setStyleSheet("color: gray;")

        self.transcribe_worker = TranscribeWorker(audio_path, language_name, output_path)
        self.transcribe_worker.progress.connect(self._on_transcribe_progress)
        self.transcribe_worker.finished.connect(self._on_transcribe_done)
        self.transcribe_worker.error.connect(self._on_transcribe_error)
        self.transcribe_worker.start()

    def _on_transcribe_progress(self, msg):
        """Update the status label with a transcription progress message.

        Args:
            msg: Progress message string.
        """
        self.transcribe_status.setText(msg)
        self.transcribe_status.setStyleSheet("color: gray;")

    def _on_transcribe_done(self, output_path):
        """Handle successful transcription completion.

        Args:
            output_path: Path to the generated SRT file.
        """
        self.transcribe_status.setText(f"SRT saved to {output_path}")
        self.transcribe_status.setStyleSheet("color: green;")
        self.transcribe_button.setEnabled(True)

    def _on_transcribe_error(self, msg):
        """Handle transcription error.

        Args:
            msg: Error message string.
        """
        QMessageBox.critical(self, "Transcription Error", f"Transcription failed:\n{msg}")
        self.transcribe_status.setText("Transcription failed.")
        self.transcribe_status.setStyleSheet("color: red;")
        self.transcribe_button.setEnabled(True)
