import json
import uuid
from typing import TextIO, cast
from typing import Any, Dict

def create_routing_hash(hash_path: str) -> None:
    unique_hash: str = uuid.uuid4().hex
    data: dict[str, str] = {
        "routing_hash": unique_hash
    }

    with open(hash_path, 'w') as f:
        writer: TextIO = cast(TextIO, f)
        json.dump(data, writer, indent=4)


def load_json(hash_path: str) -> Dict[str, Any]:
    with open(hash_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data