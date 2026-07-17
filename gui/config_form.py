from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import lib.config_helper as config_helper


class ConfigForm(QDialog):
    def __init__(self, config, config_path, parent=None):
        """Initialize the settings dialog.

        Args:
            config: Parsed configuration file.
            config_path: Path to the configuration file on disk.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.config = config
        self.config_path = config_path
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self._init_ui()
        self._load_models()
        self._load_fields()

    def _init_ui(self):
        """Build the settings dialog layout with AI Models and General groups."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        model_group = QGroupBox("AI Models")
        model_layout = QVBoxLayout()
        model_layout.setSpacing(8)

        model_select_row = QHBoxLayout()
        model_select_row.setSpacing(6)
        self.model_combo = QComboBox()
        self.model_combo.setToolTip("Select a model to edit its settings")
        self.model_combo.currentTextChanged.connect(self._on_model_selected)
        model_select_row.addWidget(self.model_combo)

        self.add_model_button = QPushButton("Add")
        self.add_model_button.setToolTip("Add a new model configuration")
        self.add_model_button.clicked.connect(self._on_add_model)
        model_select_row.addWidget(self.add_model_button)

        self.remove_model_button = QPushButton("Remove")
        self.remove_model_button.setToolTip("Remove the selected model")
        self.remove_model_button.clicked.connect(self._on_remove_model)
        model_select_row.addWidget(self.remove_model_button)

        self.rename_model_button = QPushButton("Rename")
        self.rename_model_button.setToolTip("Rename the selected model")
        self.rename_model_button.clicked.connect(self._on_rename_model)
        model_select_row.addWidget(self.rename_model_button)

        model_layout.addLayout(model_select_row)

        ai_form = QFormLayout()
        ai_form.setSpacing(6)

        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("e.g. localhost")
        ai_form.addRow("Host:", self.host_edit)

        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("e.g. 1234")
        ai_form.addRow("Port:", self.port_edit)

        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("e.g. qwen2.5")
        ai_form.addRow("Model:", self.model_edit)

        self.max_tokens_edit = QLineEdit()
        self.max_tokens_edit.setPlaceholderText("e.g. 200000")
        ai_form.addRow("Max tokens:", self.max_tokens_edit)

        self.min_batch_size_edit = QLineEdit()
        self.min_batch_size_edit.setPlaceholderText("e.g. 3")
        ai_form.addRow("Min batch size:", self.min_batch_size_edit)

        self.max_batch_size_edit = QLineEdit()
        self.max_batch_size_edit.setPlaceholderText("e.g. 30")
        ai_form.addRow("Max batch size:", self.max_batch_size_edit)

        self.active_check = QCheckBox("Set as active model")
        self.active_check.setToolTip("Mark this model as the default for translations")
        ai_form.addRow("", self.active_check)

        model_layout.addLayout(ai_form)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        general_group = QGroupBox("General")
        general_form = QFormLayout()
        general_form.setSpacing(6)

        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("e.g. 1.0")
        general_form.addRow("Version:", self.version_edit)

        general_group.setLayout(general_form)
        layout.addWidget(general_group)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.addStretch()
        self.save_button = QPushButton("Save")
        self.save_button.setMinimumWidth(80)
        self.save_button.setToolTip("Save settings and close")
        self.save_button.clicked.connect(self._on_save)
        button_row.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(80)
        self.cancel_button.setToolTip("Discard changes and close")
        self.cancel_button.clicked.connect(self.reject)
        button_row.addWidget(self.cancel_button)
        layout.addLayout(button_row)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def _load_models(self):
        """Populate the model combo box from config and select the active model."""
        self.model_combo.clear()
        models = config_helper.list_models(self.config)
        self.model_combo.addItems(models)
        active = config_helper.get_active_model(self.config)
        idx = self.model_combo.findText(active)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

    def _on_model_selected(self, model_name):
        """Load the selected model's settings into the form fields.

        Args:
            model_name: Name of the selected model.
        """
        if not model_name:
            return
        model_cfg = config_helper.get_model_config(self.config, model_name)
        self.host_edit.setText(model_cfg.get("host", ""))
        self.port_edit.setText(model_cfg.get("port", ""))
        self.model_edit.setText(model_cfg.get("model", ""))
        self.max_tokens_edit.setText(model_cfg.get("max_tokens", ""))
        self.min_batch_size_edit.setText(model_cfg.get("min_batch_size", ""))
        self.max_batch_size_edit.setText(model_cfg.get("max_batch_size", ""))
        self.active_check.setChecked(model_name == config_helper.get_active_model(self.config))

    def _on_add_model(self):
        """Prompt for a new model name and add it with default settings."""
        new_name, ok = QInputDialog.getText(self, "Add Model", "Enter new model name:")
        if ok and new_name:
            settings = {
                "host": "localhost",
                "port": "1234",
                "model": "model-name",
                "max_tokens": "200000",
                "min_batch_size": "3",
                "max_batch_size": "30",
            }
            if config_helper.add_model(self.config, new_name, settings):
                self._load_models()
                self.model_combo.setCurrentText(new_name)
            else:
                QMessageBox.warning(self, "Error", f"Model '{new_name}' already exists.")

    def _on_remove_model(self):
        """Prompt for confirmation and remove the selected model."""
        model_name = self.model_combo.currentText()
        if not model_name:
            return
        reply = QMessageBox.question(
            self,
            "Remove Model",
            f"Remove model '{model_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if config_helper.remove_model(self.config, model_name):
                self._load_models()
            else:
                QMessageBox.warning(self, "Error", f"Could not remove model '{model_name}'.")

    def _on_rename_model(self):
        """Prompt for a new name and rename the selected model."""
        old_name = self.model_combo.currentText()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(self, "Rename Model", f"New name for '{old_name}':")
        if ok and new_name:
            if config_helper.rename_model(self.config, old_name, new_name):
                self._load_models()
                self.model_combo.setCurrentText(new_name)
            else:
                QMessageBox.warning(self, "Error", f"Could not rename model to '{new_name}'.")

    def _load_fields(self):
        """Load general settings into the form fields."""
        self.version_edit.setText(self.config.get("general", "version", fallback=""))

    def _validate(self):
        """Validate all form fields and highlight invalid ones.

        Returns:
            List of error message strings. Empty if all fields are valid.
        """
        errors = []

        model_name = self.model_combo.currentText()
        if not model_name:
            errors.append("No model selected.")

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

        min_batch_size = self.min_batch_size_edit.text().strip()
        if not min_batch_size:
            errors.append("Min batch size cannot be empty.")
            self.min_batch_size_edit.setStyleSheet("background-color: #ffcccc;")
        else:
            try:
                mbs = int(min_batch_size)
                if mbs <= 0:
                    errors.append("Min batch size must be a positive integer.")
                    self.min_batch_size_edit.setStyleSheet("background-color: #ffcccc;")
                else:
                    self.min_batch_size_edit.setStyleSheet("")
            except ValueError:
                errors.append("Min batch size must be a valid integer.")
                self.min_batch_size_edit.setStyleSheet("background-color: #ffcccc;")

        max_batch_size = self.max_batch_size_edit.text().strip()
        if not max_batch_size:
            errors.append("Max batch size cannot be empty.")
            self.max_batch_size_edit.setStyleSheet("background-color: #ffcccc;")
        else:
            try:
                MBS = int(max_batch_size)
                if MBS <= 0:
                    errors.append("Max batch size must be a positive integer.")
                    self.max_batch_size_edit.setStyleSheet("background-color: #ffcccc;")
                else:
                    self.max_batch_size_edit.setStyleSheet("")
            except ValueError:
                errors.append("Max batch size must be a valid integer.")
                self.max_batch_size_edit.setStyleSheet("background-color: #ffcccc;")

        version = self.version_edit.text().strip()
        if not version:
            errors.append("Version cannot be empty.")
            self.version_edit.setStyleSheet("background-color: #ffcccc;")
        else:
            self.version_edit.setStyleSheet("")

        return errors

    def _on_save(self):
        """Validate, save settings to config file, and close the dialog."""
        errors = self._validate()
        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return

        model_name = self.model_combo.currentText()
        if model_name:
            settings = {
                "host": self.host_edit.text().strip(),
                "port": self.port_edit.text().strip(),
                "model": self.model_edit.text().strip(),
                "max_tokens": self.max_tokens_edit.text().strip(),
                "min_batch_size": self.min_batch_size_edit.text().strip(),
                "max_batch_size": self.max_batch_size_edit.text().strip(),
            }
            section = f"model.{model_name}"
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, value in settings.items():
                self.config.set(section, key, value)

            if self.active_check.isChecked():
                config_helper.set_active_model(self.config, model_name)

        if not self.config.has_section("general"):
            self.config.add_section("general")
        self.config.set("general", "version", self.version_edit.text().strip())

        with open(self.config_path, "w") as f:
            self.config.write(f)

        self.status_label.setText("Settings saved.")
        self.status_label.setStyleSheet("color: green;")
        self.accept()
