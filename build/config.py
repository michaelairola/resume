from pathlib import Path
from dataclasses import dataclass, field
try:
    import tomllib
except ImportError:
    # Python < 3.11
    import tomli as tomllib


@dataclass 
class Config:
    templates: Path = field(default="templates")
    static: Path = field(default="static")
    dist: Path = field(default="dist")
    pages: list[Path] = field(default_factory=lambda:["index.html"])

    @classmethod
    def from_(cls, file_path_str: str | None = None):
        file_path = Path(file_path_str) if file_path_str else Path.cwd()
        if file_path.is_dir():
            file_path = file_path / "pyproject.toml"
        pyproject_data = {}
        try:
            with open(file_path, "rb") as f:
                pyproject_data = tomllib.load(f)
        except FileNotFoundError:
            print(f"Error finding file '{file_path}'")
        except tomllib.TOMLDecodeError as e:
            print(f"Error decoding TOML file: {e}")
        config_data = pyproject_data.get("tools", {}).get("build", {})
        dataclass_fields = [ k for k in cls.__dataclass_fields__.keys() ]
        config_data = {
            k: Path(v) if isinstance(v, str) else v for k, v in config_data.items()
            if k in dataclass_fields
        }
        return cls(**config_data)

