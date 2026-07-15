import configparser


def get_active_model(config: configparser.ConfigParser) -> str:
    """Return the name of the currently active model.

    Args:
        config: Parsed configuration file.

    Returns:
        The active model name, defaulting to "default".
    """
    return config.get("general", "active_model", fallback="default")


def get_model_config(config: configparser.ConfigParser, model_name: str = None) -> dict:
    """Return the configuration dict for a given model.

    Args:
        config: Parsed configuration file.
        model_name: Name of the model to look up. Uses the active model if None.

    Returns:
        Dictionary of model settings.

    Raises:
        ValueError: If the model is not found.
    """
    if model_name is None:
        model_name = get_active_model(config)
    section = f"model.{model_name}"
    if config.has_section(section):
        return dict(config[section])
    if config.has_section("model.default"):
        return dict(config["model.default"])
    raise ValueError(f"Model '{model_name}' not found")


def list_models(config: configparser.ConfigParser) -> list[str]:
    """Return a list of all configured model names.

    Args:
        config: Parsed configuration file.

    Returns:
        List of model names found in config sections prefixed with 'model.'.
    """
    models = []
    for section in config.sections():
        if section.startswith("model."):
            name = section[6:]
            models.append(name)
    return models


def add_model(config: configparser.ConfigParser, name: str, settings: dict) -> bool:
    """Add a new model to the configuration.

    Args:
        config: Parsed configuration file.
        name: Name for the new model.
        settings: Dictionary of model settings to store.

    Returns:
        True if the model was added, False if it already exists.
    """
    section = f"model.{name}"
    if config.has_section(section):
        return False
    config.add_section(section)
    for key, value in settings.items():
        config.set(section, key, str(value))
    return True


def remove_model(config: configparser.ConfigParser, name: str) -> bool:
    """Remove a model from the configuration.

    If the removed model was active, switches to the first available model.

    Args:
        config: Parsed configuration file.
        name: Name of the model to remove.

    Returns:
        True if the model was removed, False if it did not exist.
    """
    section = f"model.{name}"
    if not config.has_section(section):
        return False
    config.remove_section(section)
    if get_active_model(config) == name:
        models = list_models(config)
        if models:
            set_active_model(config, models[0])
    return True


def rename_model(config: configparser.ConfigParser, old_name: str, new_name: str) -> bool:
    """Rename a model in the configuration.

    Args:
        config: Parsed configuration file.
        old_name: Current name of the model.
        new_name: Desired new name for the model.

    Returns:
        True if renamed successfully, False if old name missing or new name taken.
    """
    old_section = f"model.{old_name}"
    new_section = f"model.{new_name}"
    if not config.has_section(old_section) or config.has_section(new_section):
        return False
    settings = dict(config[old_section])
    config.remove_section(old_section)
    config.add_section(new_section)
    for key, value in settings.items():
        config.set(new_section, key, value)
    if get_active_model(config) == old_name:
        set_active_model(config, new_name)
    return True


def set_active_model(config: configparser.ConfigParser, name: str) -> bool:
    """Set the active model in the [general] section.

    Args:
        config: Parsed configuration file.
        name: Name of the model to activate.

    Returns:
        True if the model was activated, False if the model section does not exist.
    """
    section = f"model.{name}"
    if not config.has_section(section):
        return False
    if not config.has_section("general"):
        config.add_section("general")
    config.set("general", "active_model", name)
    return True


def migrate_old_config(config: configparser.ConfigParser) -> bool:
    """Migrate an old single-[AI] config to the multi-model format.

    Converts the legacy [AI] section into a 'default' model entry.

    Args:
        config: Parsed configuration file to migrate in place.

    Returns:
        True if migration was performed, False otherwise.
    """
    if config.has_section("AI") and not list_models(config):
        settings = dict(config["AI"])
        config.remove_section("AI")
        add_model(config, "default", settings)
        set_active_model(config, "default")
        return True
    return False


def ensure_general_section(config: configparser.ConfigParser):
    """Create the [general] config section if it does not exist.

    Args:
        config: Parsed configuration file.
    """
    if not config.has_section("general"):
        config.add_section("general")


def ensure_active_model(config: configparser.ConfigParser):
    """Ensure an active model is configured, creating a default if needed.

    Args:
        config: Parsed configuration file.
    """
    ensure_general_section(config)
    if not config.has_option("general", "active_model"):
        models = list_models(config)
        if models:
            set_active_model(config, models[0])
        else:
            add_model(config, "default", {})
            set_active_model(config, "default")
