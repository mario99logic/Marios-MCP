import json
import os
from datetime import datetime, timezone
from typing import Any

DATA_FILE = os.path.join(os.path.dirname(__file__), "uncertainty_data.json")

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

def _unknown(
    key: str,
    question: str,
    context: str,
    area: str,
    priority: str,
) -> dict[str, Any]:
    return {
        "key": key,
        "question": question,
        "context": context,
        "area": area,
        "status": "open",
        "priority": priority,
        "created_at": _now(),
        "resolved_at": None,
        "resolution": None,
        "linked_assumptions": [],
        "linked_decisions": [],
    }


def _assumption(
    key: str,
    belief: str,
    confidence: float,
    consequences: str,
    area: str,
) -> dict[str, Any]:
    return {
        "key": key,
        "belief": belief,
        "confidence": confidence,
        "consequences": consequences,
        "area": area,
        "status": "active",
        "created_at": _now(),
        "last_reviewed": _now(),
        "evidence": [],
        "linked_decisions": [],
    }


def _decision(
    key: str,
    choice: str,
    rationale: str,
    confidence: float,
) -> dict[str, Any]:
    return {
        "key": key,
        "choice": choice,
        "rationale": rationale,
        "confidence": confidence,
        "status": "made",
        "created_at": _now(),
        "linked_unknowns": [],
        "linked_assumptions": [],
    }


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_data() -> dict[str, Any]:
    if not os.path.exists(DATA_FILE):
        return {"unknowns": {}, "assumptions": {}, "decisions": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data: dict[str, Any]) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
