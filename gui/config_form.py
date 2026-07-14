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

import config_helper


class ConfigForm(QDialog):
    def __init__(self, config, config_path, parent=None):
        super().__init__(parent)
        self.config = config
        self.config_path = config_path
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self._init_ui()
        self._load_models()
        self._load_fields()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        model_group = QGroupBox("AI Models")
        model_layout = QVBoxLayout()

        model_select_row = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self._on_model_selected)
        model_select_row.addWidget(self.model_combo)

        self.add_model_button = QPushButton("Add")
        self.add_model_button.clicked.connect(self._on_add_model)
        model_select_row.addWidget(self.add_model_button)

        self.remove_model_button = QPushButton("Remove")
        self.remove_model_button.clicked.connect(self._on_remove_model)
        model_select_row.addWidget(self.remove_model_button)

        self.rename_model_button = QPushButton("Rename")
        self.rename_model_button.clicked.connect(self._on_rename_model)
        model_select_row.addWidget(self.rename_model_button)

        model_layout.addLayout(model_select_row)

        ai_form = QFormLayout()

        self.host_edit = QLineEdit()
        ai_form.addRow("Host:", self.host_edit)

        self.port_edit = QLineEdit()
        ai_form.addRow("Port:", self.port_edit)

        self.model_edit = QLineEdit()
        ai_form.addRow("Model:", self.model_edit)

        self.max_tokens_edit = QLineEdit()
        ai_form.addRow("Max tokens:", self.max_tokens_edit)

        self.min_batch_size_edit = QLineEdit()
        ai_form.addRow("Min batch size:", self.min_batch_size_edit)

        self.max_batch_size_edit = QLineEdit()
        ai_form.addRow("Max batch size:", self.max_batch_size_edit)

        self.active_check = QCheckBox("Set as active model")
        ai_form.addRow("", self.active_check)

        model_layout.addLayout(ai_form)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

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

    def _load_models(self):
        self.model_combo.clear()
        models = config_helper.list_models(self.config)
        self.model_combo.addItems(models)
        active = config_helper.get_active_model(self.config)
        idx = self.model_combo.findText(active)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

    def _on_model_selected(self, model_name):
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
        self.version_edit.setText(self.config.get("general", "version", fallback=""))

    def _validate(self):
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
