import json
import os
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP

DATA_FILE = os.path.join(os.path.dirname(__file__), "uncertainty_data.json")

mcp = FastMCP("UncertaintyEngine", json_response=True)

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


def _age_days(iso_timestamp: str) -> float:
    created = datetime.fromisoformat(iso_timestamp)
    now = datetime.now(timezone.utc)
    return (now - created).total_seconds() / 86400


# ---------------------------------------------------------------------------
# Unknown tools
# ---------------------------------------------------------------------------

@mcp.tool()
def save_unknown(key: str, question: str, context: str, area: str, priority: str) -> dict:
    """Log a new open question / unknown. priority: low | medium | high | critical."""
    data = load_data()
    data["unknowns"][key] = _unknown(key, question, context, area, priority)
    save_data(data)
    return data["unknowns"][key]


@mcp.tool()
def resolve_unknown(key: str, resolution: str) -> dict:
    """Mark an unknown as resolved and record the answer."""
    data = load_data()
    if key not in data["unknowns"]:
        raise KeyError(f"Unknown '{key}' not found")
    u = data["unknowns"][key]
    u["status"] = "resolved"
    u["resolved_at"] = _now()
    u["resolution"] = resolution
    save_data(data)
    return u


@mcp.tool()
def defer_unknown(key: str, reason: str) -> dict:
    """Park an unknown as deferred — not urgent right now."""
    data = load_data()
    if key not in data["unknowns"]:
        raise KeyError(f"Unknown '{key}' not found")
    u = data["unknowns"][key]
    u["status"] = "deferred"
    u["resolution"] = f"Deferred: {reason}"
    save_data(data)
    return u


@mcp.tool()
def list_unknowns(area: str = "", status: str = "", priority: str = "") -> list:
    """List unknowns, optionally filtered by area, status, or priority."""
    data = load_data()
    results = list(data["unknowns"].values())
    if area:
        results = [u for u in results if u["area"] == area]
    if status:
        results = [u for u in results if u["status"] == status]
    if priority:
        results = [u for u in results if u["priority"] == priority]
    return results


@mcp.tool()
def search_unknowns(query: str) -> list:
    """Keyword search across question and context of all unknowns."""
    data = load_data()
    q = query.lower()
    return [
        u for u in data["unknowns"].values()
        if q in u["question"].lower() or q in u["context"].lower()
    ]


@mcp.tool()
def link_unknown_to_assumption(unknown_key: str, assumption_key: str) -> dict:
    """Link an unknown to an assumption, building the graph."""
    data = load_data()
    if unknown_key not in data["unknowns"]:
        raise KeyError(f"Unknown '{unknown_key}' not found")
    if assumption_key not in data["assumptions"]:
        raise KeyError(f"Assumption '{assumption_key}' not found")
    u = data["unknowns"][unknown_key]
    if assumption_key not in u["linked_assumptions"]:
        u["linked_assumptions"].append(assumption_key)
    a = data["assumptions"][assumption_key]
    # back-link not in spec but useful
    save_data(data)
    return u


# ---------------------------------------------------------------------------
# Assumption tools
# ---------------------------------------------------------------------------

@mcp.tool()
def save_assumption(key: str, belief: str, confidence: float, consequences: str, area: str) -> dict:
    """Log an assumption you're acting on. confidence: 0.0–1.0."""
    data = load_data()
    data["assumptions"][key] = _assumption(key, belief, confidence, consequences, area)
    save_data(data)
    return data["assumptions"][key]


@mcp.tool()
def challenge_assumption(key: str, evidence: str) -> dict:
    """Add a piece of challenging evidence to an assumption."""
    data = load_data()
    if key not in data["assumptions"]:
        raise KeyError(f"Assumption '{key}' not found")
    a = data["assumptions"][key]
    a["evidence"].append(f"[CHALLENGE] {evidence}")
    a["status"] = "challenged"
    a["last_reviewed"] = _now()
    save_data(data)
    return a


@mcp.tool()
def validate_assumption(key: str, evidence: str) -> dict:
    """Add confirming evidence to an assumption."""
    data = load_data()
    if key not in data["assumptions"]:
        raise KeyError(f"Assumption '{key}' not found")
    a = data["assumptions"][key]
    a["evidence"].append(f"[VALIDATE] {evidence}")
    a["status"] = "validated"
    a["last_reviewed"] = _now()
    save_data(data)
    return a


@mcp.tool()
def invalidate_assumption(key: str, reason: str) -> dict:
    """Mark an assumption as proven wrong."""
    data = load_data()
    if key not in data["assumptions"]:
        raise KeyError(f"Assumption '{key}' not found")
    a = data["assumptions"][key]
    a["status"] = "invalidated"
    a["evidence"].append(f"[INVALIDATED] {reason}")
    a["last_reviewed"] = _now()
    save_data(data)
    return a


@mcp.tool()
def list_assumptions(area: str = "", min_risk: float = 0.0) -> list:
    """List assumptions, optionally filtered by area or minimum risk score."""
    data = load_data()
    results = list(data["assumptions"].values())
    if area:
        results = [a for a in results if a["area"] == area]
    if min_risk > 0.0:
        results = [a for a in results if _assumption_risk(a) >= min_risk]
    return results


@mcp.tool()
def search_assumptions(query: str) -> list:
    """Keyword search across belief and consequences of all assumptions."""
    data = load_data()
    q = query.lower()
    return [
        a for a in data["assumptions"].values()
        if q in a["belief"].lower() or q in a["consequences"].lower()
    ]


# ---------------------------------------------------------------------------
# Decision tools
# ---------------------------------------------------------------------------

@mcp.tool()
def log_decision(key: str, choice: str, rationale: str, confidence: float) -> dict:
    """Record a decision made under uncertainty. confidence: 0.0–1.0."""
    data = load_data()
    data["decisions"][key] = _decision(key, choice, rationale, confidence)
    save_data(data)
    return data["decisions"][key]


@mcp.tool()
def link_decision(decision_key: str, unknown_keys: list[str] = [], assumption_keys: list[str] = []) -> dict:
    """Connect a decision to the unknowns and assumptions that existed when it was made."""
    data = load_data()
    if decision_key not in data["decisions"]:
        raise KeyError(f"Decision '{decision_key}' not found")
    d = data["decisions"][decision_key]
    for k in unknown_keys:
        if k not in data["unknowns"]:
            raise KeyError(f"Unknown '{k}' not found")
        if k not in d["linked_unknowns"]:
            d["linked_unknowns"].append(k)
        if decision_key not in data["unknowns"][k]["linked_decisions"]:
            data["unknowns"][k]["linked_decisions"].append(decision_key)
    for k in assumption_keys:
        if k not in data["assumptions"]:
            raise KeyError(f"Assumption '{k}' not found")
        if k not in d["linked_assumptions"]:
            d["linked_assumptions"].append(k)
        if decision_key not in data["assumptions"][k]["linked_decisions"]:
            data["assumptions"][k]["linked_decisions"].append(decision_key)
    save_data(data)
    return d


@mcp.tool()
def revisit_decision(key: str, new_context: str) -> dict:
    """Flag a decision for re-evaluation given new context."""
    data = load_data()
    if key not in data["decisions"]:
        raise KeyError(f"Decision '{key}' not found")
    d = data["decisions"][key]
    d["status"] = "revisited"
    d["rationale"] += f"\n\n[REVISIT] {new_context}"
    save_data(data)
    return d


@mcp.tool()
def list_decisions(status: str = "") -> list:
    """List all decisions, optionally filtered by status: pending | made | revisited | regretted."""
    data = load_data()
    results = list(data["decisions"].values())
    if status:
        results = [d for d in results if d["status"] == status]
    return results


# ---------------------------------------------------------------------------
# Risk scoring helpers
# ---------------------------------------------------------------------------

_PRIORITY_WEIGHT = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
_CONSEQUENCE_WEIGHT = {
    "low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0,
}


def _assumption_risk(a: dict) -> float:
    # Heuristic: consequence severity from keyword scan
    c = a["consequences"].lower()
    if any(w in c for w in ["break", "fail", "crash", "corrupt", "block", "critical"]):
        cw = 1.0
    elif any(w in c for w in ["slow", "degrade", "wrong", "bad", "poor"]):
        cw = 0.6
    else:
        cw = 0.3
    return (1 - a["confidence"]) * cw


def _unknown_risk(u: dict) -> float:
    pw = _PRIORITY_WEIGHT.get(u["priority"], 0.5)
    age = _age_days(u["created_at"])
    return pw * age


# ---------------------------------------------------------------------------
# Intelligence Layer
# ---------------------------------------------------------------------------

@mcp.tool()
def get_risk_radar() -> dict:
    """Return a ranked view of your most dangerous unknowns and assumptions right now."""
    data = load_data()

    risky_unknowns = [
        {**u, "_risk_score": _unknown_risk(u)}
        for u in data["unknowns"].values()
        if u["status"] == "open"
    ]
    risky_unknowns.sort(key=lambda x: x["_risk_score"], reverse=True)

    risky_assumptions = [
        {**a, "_risk_score": _assumption_risk(a)}
        for a in data["assumptions"].values()
        if a["status"] in ("active", "challenged")
    ]
    risky_assumptions.sort(key=lambda x: x["_risk_score"], reverse=True)

    return {
        "top_unknown_risks": risky_unknowns[:5],
        "top_assumption_risks": risky_assumptions[:5],
    }


@mcp.tool()
def get_blind_spots() -> list:
    """Return assumptions that haven't been reviewed or challenged in 30+ days."""
    data = load_data()
    stale = []
    for a in data["assumptions"].values():
        if a["status"] in ("active", "challenged") and _age_days(a["last_reviewed"]) >= 30:
            stale.append({**a, "_days_since_review": _age_days(a["last_reviewed"])})
    stale.sort(key=lambda x: x["_days_since_review"], reverse=True)
    return stale


@mcp.tool()
def get_stale_unknowns(older_than_days: int = 14) -> list:
    """Return open unknowns with no update for N days (default 14)."""
    data = load_data()
    stale = []
    for u in data["unknowns"].values():
        if u["status"] == "open" and _age_days(u["created_at"]) >= older_than_days:
            stale.append({**u, "_age_days": _age_days(u["created_at"])})
    stale.sort(key=lambda x: x["_age_days"], reverse=True)
    return stale


@mcp.tool()
def get_assumption_chain(assumption_key: str) -> dict:
    """Show which decisions depend on this assumption being true."""
    data = load_data()
    if assumption_key not in data["assumptions"]:
        raise KeyError(f"Assumption '{assumption_key}' not found")
    a = data["assumptions"][assumption_key]
    dependent_decisions = [
        data["decisions"][k]
        for k in a.get("linked_decisions", [])
        if k in data["decisions"]
    ]
    return {
        "assumption": a,
        "dependent_decisions": dependent_decisions,
        "total_decisions_at_risk": len(dependent_decisions),
    }


@mcp.tool()
def surface_uncertainties(context_text: str) -> dict:
    """Given a topic or context string, return related open unknowns and risky assumptions."""
    data = load_data()
    words = set(context_text.lower().split())

    def _matches(text: str) -> bool:
        return bool(words & set(text.lower().split()))

    matched_unknowns = [
        u for u in data["unknowns"].values()
        if u["status"] == "open" and (_matches(u["question"]) or _matches(u["context"]) or _matches(u["area"]))
    ]
    matched_assumptions = [
        a for a in data["assumptions"].values()
        if a["status"] in ("active", "challenged") and (_matches(a["belief"]) or _matches(a["consequences"]) or _matches(a["area"]))
    ]

    matched_unknowns.sort(key=_unknown_risk, reverse=True)
    matched_assumptions.sort(key=_assumption_risk, reverse=True)

    return {
        "context": context_text,
        "related_unknowns": matched_unknowns,
        "related_assumptions": matched_assumptions,
        "warning": (
            "No related uncertainties found — either you're well-informed or nothing is logged yet."
            if not matched_unknowns and not matched_assumptions
            else None
        ),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
