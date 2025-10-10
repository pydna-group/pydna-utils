# settings.py
from pathlib import Path
from platformdirs import user_config_dir
from pydantic import Field, ConfigDict
from confz import BaseConfig, FileSource
import tomli_w

APP_NAME = "pydna"
CONFIG_PATH = Path(user_config_dir(APP_NAME)) / "pydna_config.toml"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

class Settings(BaseConfig):
    # allow attribute assignment
    model_config = ConfigDict(frozen=False)

    # your three persistent strings (defaults as given)
    pydna_ape_url: str = Field(
        default='/usr/bin/tclsh /home/bjorn/.ApE/ApE.tcl'
    )
    pydna_enzymes: str = Field(
        default='/home/bjorn/.ApE/Enzymes/LGM_group.txt'
    )
    pydna_primers: str = Field(
        default='/home/bjorn/myvault/PRIMERS.md'
    )

    # ConfZ v2: use FileSource and mark it optional for first run
    CONFIG_SOURCES = FileSource(file=CONFIG_PATH, optional=True)

def load_settings() -> Settings:
    """Load from file if present; otherwise use defaults in class."""
    return Settings()  # ConfZ loads from CONFIG_SOURCES lazily

def save_settings(cfg: Settings) -> None:
    """Persist current settings to TOML."""
    data = cfg.model_dump()
    with CONFIG_PATH.open("wb") as f:
        tomli_w.dump(data, f)

# Tiny CLI for convenience
if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--ape")
    parser.add_argument("--enzymes")
    parser.add_argument("--primers")
    args = parser.parse_args()

    cfg = load_settings()

    changed = False
    if args.ape is not None:
        cfg.pydna_ape_url = args.ape; changed = True
    if args.enzymes is not None:
        cfg.pydna_enzymes = args.enzymes; changed = True
    if args.primers is not None:
        cfg.pydna_primers = args.primers; changed = True

    if changed or not CONFIG_PATH.exists():
        save_settings(cfg)
        print(f"Saved → {CONFIG_PATH}")

    if args.show or not changed:
        print(json.dumps(cfg.model_dump(), indent=2))
        print(f"(file: {CONFIG_PATH})")
