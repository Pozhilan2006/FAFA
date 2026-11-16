import json
from pathlib import Path
from jsonschema import validate

ROOT = Path(__file__).parents[1]
OBSERVATION = {"match_id": "match_001", "track_id": "track_007", "global_player_id": None, "team_id": "team_a", "timestamp": 125.5, "frame_number": 3762, "class_name": "player", "confidence": 0.94, "bounding_box": {"x1": 410, "y1": 180, "x2": 470, "y2": 330}, "image_position": {"x": 440, "y": 330}, "pitch_position": None}

def test_observation_contract_example_is_valid() -> None:
    validate(OBSERVATION, json.loads((ROOT / "shared/data_contracts/observation.schema.json").read_text()))
