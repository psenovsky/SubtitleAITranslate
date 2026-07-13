from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ConfigForm(QDialog):
    def __init__(self, config, config_path, parent=None):
        super().__init__(parent)
        self.config = config
        self.config_path = config_path
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)
        self._init_ui()
        self._load_fields()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        ai_group = QGroupBox("AI")
        ai_form = QFormLayout()

        self.host_edit = QLineEdit()
        ai_form.addRow("Host:", self.host_edit)

        self.port_edit = QLineEdit()
        ai_form.addRow("Port:", self.port_edit)

        self.model_edit = QLineEdit()
        ai_form.addRow("Model:", self.model_edit)

        self.max_tokens_edit = QLineEdit()
        ai_form.addRow("Max tokens:", self.max_tokens_edit)

        ai_group.setLayout(ai_form)
        layout.addWidget(ai_group)

        general_group = QGroupBox("General")
        general_form = QFormLayout()

        self.version_edit = QLineEdit()
        general_form.addRow("Version:", self.version_edit)

        general_group.setLayout(general_form)
        layout.addWidget(general_group)

        button_row = QVBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._on_save)
        button_row.addWidget(self.save_button)

        self.status_label = QLabel("")
        self.status_label.setAlignment(self.status_label.alignment())
        button_row.addWidget(self.status_label)

        layout.addLayout(button_row)

    def _load_fields(self):
        self.host_edit.setText(self.config.get("AI", "host", fallback=""))
        self.port_edit.setText(self.config.get("AI", "port", fallback=""))
        self.model_edit.setText(self.config.get("AI", "model", fallback=""))
        self.max_tokens_edit.setText(self.config.get("AI", "max_tokens", fallback=""))
        self.version_edit.setText(self.config.get("general", "version", fallback=""))

    def _validate(self):
        errors = []

        host = self.host_edit.text().strip()
        if not host:
            errors.append("Host cannot be empty.")
            self.host_edit.setStyleSheet("background-color: #ffcccc;")
        else:
            self.host_edit.setStyleSheet("")

        port = self.port_edit.text().strip()
        if not port:
            errors.append("Port cannot be empty.")
            self.port_edit.setStyleSheet("background-color: #ffcccc;")
        else:
            try:
                port_num = int(port)
                if not (1 <= port_num <= 65535):
                    errors.append("Port must be between 1 and 65535.")
                    self.port_edit.setStyleSheet("background-color: #ffcccc;")
                else:
                    self.port_edit.setStyleSheet("")
            except ValueError:
                errors.append("Port must be a valid integer.")
                self.port_edit.setStyleSheet("background-color: #ffcccc;")

        model = self.model_edit.text().strip()
        if not model:
            errors.append("Model cannot be empty.")
            self.model_edit.setStyleSheet("background-color: #ffcccc;")
        else:
            self.model_edit.setStyleSheet("")

        max_tokens = self.max_tokens_edit.text().strip()
        if not max_tokens:
            errors.append("Max tokens cannot be empty.")
            self.max_tokens_edit.setStyleSheet("background-color: #ffcccc;")
        else:
            try:
                mt = int(max_tokens)
                if mt <= 0:
                    errors.append("Max tokens must be a positive integer.")
                    self.max_tokens_edit.setStyleSheet("background-color: #ffcccc;")
                else:
                    self.max_tokens_edit.setStyleSheet("")
            except ValueError:
                errors.append("Max tokens must be a valid integer.")
                self.max_tokens_edit.setStyleSheet("background-color: #ffcccc;")

        version = self.version_edit.text().strip()
        if not version:
            errors.append("Version cannot be empty.")
            self.version_edit.setStyleSheet("background-color: #ffcccc;")
        else:
            self.version_edit.setStyleSheet("")

        return errors

    def _on_save(self):
        errors = self._validate()
        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return

        if not self.config.has_section("AI"):
            self.config.add_section("AI")
        if not self.config.has_section("general"):
            self.config.add_section("general")

        self.config.set("AI", "host", self.host_edit.text().strip())
        self.config.set("AI", "port", self.port_edit.text().strip())
        self.config.set("AI", "model", self.model_edit.text().strip())
        self.config.set("AI", "max_tokens", self.max_tokens_edit.text().strip())
        self.config.set("general", "version", self.version_edit.text().strip())

        with open(self.config_path, "w") as f:
            self.config.write(f)

        self.status_label.setText("Settings saved.")
        self.status_label.setStyleSheet("color: green;")
        self.accept()
