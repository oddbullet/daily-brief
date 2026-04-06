import yaml

def _load_config() -> dict:
    with open("daily_brief/config.yaml", 'r') as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"Failed to load config file: {exc}")
