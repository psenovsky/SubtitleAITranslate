import configparser


def get_active_model(config: configparser.ConfigParser) -> str:
    return config.get("general", "active_model", fallback="default")


def get_model_config(config: configparser.ConfigParser, model_name: str = None) -> dict:
    if model_name is None:
        model_name = get_active_model(config)
    section = f"model.{model_name}"
    if config.has_section(section):
        return dict(config[section])
    if config.has_section("model.default"):
        return dict(config["model.default"])
    raise ValueError(f"Model '{model_name}' not found")


def list_models(config: configparser.ConfigParser) -> list[str]:
    models = []
    for section in config.sections():
        if section.startswith("model."):
            name = section[6:]
            models.append(name)
    return models


def add_model(config: configparser.ConfigParser, name: str, settings: dict) -> bool:
    section = f"model.{name}"
    if config.has_section(section):
        return False
    config.add_section(section)
    for key, value in settings.items():
        config.set(section, key, str(value))
    return True


def remove_model(config: configparser.ConfigParser, name: str) -> bool:
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
    section = f"model.{name}"
    if not config.has_section(section):
        return False
    if not config.has_section("general"):
        config.add_section("general")
    config.set("general", "active_model", name)
    return True


def migrate_old_config(config: configparser.ConfigParser) -> bool:
    if config.has_section("AI") and not list_models(config):
        settings = dict(config["AI"])
        config.remove_section("AI")
        add_model(config, "default", settings)
        set_active_model(config, "default")
        return True
    return False


def ensure_general_section(config: configparser.ConfigParser):
    if not config.has_section("general"):
        config.add_section("general")


def ensure_active_model(config: configparser.ConfigParser):
    ensure_general_section(config)
    if not config.has_option("general", "active_model"):
        models = list_models(config)
        if models:
            set_active_model(config, models[0])
        else:
            add_model(config, "default", {})
            set_active_model(config, "default")
