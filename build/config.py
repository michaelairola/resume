from pathlib import Path
from dataclasses import dataclass, field
try:
    import tomllib
except ImportError:
    # Python < 3.11
    import tomli as tomllib


@dataclass 
class Config:
    templates: Path
    static: Path
    dist: Path
    pages: list[Path]

def get_config(project_path=Path.cwd()):
    """
    Reads the pyproject.toml file and returns a dictionary.
    """
    data = {}
    try:
        with open(project_path / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        pass
    except tomllib.TOMLDecodeError as e:
        print(f"Error decoding TOML file: {e}")
    jinja_configs = data.get("tools", {}).get("build", {})
    templates = jinja_configs.get("templates", None) or project_path / "templates"
    static = jinja_configs.get("static", None) or project_path / "static"
    dist = jinja_configs.get("dist", None) or project_path / "dist"
    pages = jinja_configs.get("pages", ["index.html"])
    return Config(
        templates=Path(templates),
        static=Path(static),
        dist=Path(dist),
        pages=pages,
    )

