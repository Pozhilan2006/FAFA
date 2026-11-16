"""JSON export for validated, serializable records."""
import json
from pathlib import Path
from typing import Iterable, Mapping, Any


def export_json(records: Iterable[Mapping[str, Any]], destination: str | Path) -> Path:
    """Write a JSON array, creating only the destination parent directory."""
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(json.dumps(list(records), indent=2), encoding="utf-8")
    except (TypeError, OSError) as exc:
        raise ValueError(f"Cannot export JSON to {target}: {exc}") from exc
    return target
