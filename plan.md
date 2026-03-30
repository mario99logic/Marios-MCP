# The Uncertainty Engine — Implementation Plan

## Concept
Most tools track what you know. This tracks what you *don't* know.
A new MCP module (`uncertainty.py`) that stores open questions, load-bearing assumptions,
and decisions made under uncertainty — then surfaces your riskiest blind spots when relevant.

---

## Data Model

### Unknowns
Things you know you don't know. Open questions that block or affect your work.
```
{
  key: str,
  question: str,
  context: str,          # why this matters, what depends on it
  area: str,             # e.g. "architecture", "product", "personal"
  status: open | resolved | deferred,
  priority: low | medium | high | critical,
  created_at: ISO8601,
  resolved_at: ISO8601 | null,
  resolution: str | null,
  linked_assumptions: [key, ...],
  linked_decisions: [key, ...]
}
```

### Assumptions
Beliefs you're acting on without full proof. The riskier, the more important to track.
```
{
  key: str,
  belief: str,           # "I assume that X is true"
  confidence: 0.0–1.0,   # how sure are you
  consequences: str,     # what breaks if this is wrong
  area: str,
  status: active | validated | invalidated | challenged,
  created_at: ISO8601,
  last_reviewed: ISO8601,
  evidence: [str, ...],  # things that support or challenge this
  linked_decisions: [key, ...]
}
```

### Decisions
Choices made under uncertainty, linked to what you didn't know at the time.
```
{
  key: str,
  choice: str,           # what you decided
  rationale: str,        # why
  confidence: 0.0–1.0,   # how confident you were
  status: pending | made | revisited | regretted,
  created_at: ISO8601,
  linked_unknowns: [key, ...],    # what you didn't know when you decided
  linked_assumptions: [key, ...]  # what you were assuming when you decided
}
```

---

## Tools (MCP Endpoints)

### Unknowns
- `save_unknown(key, question, context, area, priority)` — log a new open question
- `resolve_unknown(key, resolution)` — mark as resolved with answer
- `defer_unknown(key, reason)` — park it, not urgent
- `list_unknowns(area?, status?, priority?)` — filtered list
- `search_unknowns(query)` — keyword search across question + context
- `link_unknown_to_assumption(unknown_key, assumption_key)` — build the graph

### Assumptions
- `save_assumption(key, belief, confidence, consequences, area)` — log an assumption
- `challenge_assumption(key, evidence)` — add a piece of challenging evidence
- `validate_assumption(key, evidence)` — add confirming evidence
- `invalidate_assumption(key, reason)` — mark as proven wrong
- `list_assumptions(area?, min_risk?)` — filter by area or risk score
- `search_assumptions(query)`

### Decisions
- `log_decision(key, choice, rationale, confidence)` — record a decision
- `link_decision(decision_key, unknown_keys?, assumption_keys?)` — connect to context
- `revisit_decision(key, new_context)` — flag for re-evaluation
- `list_decisions(status?)` — see all decisions

### Intelligence Layer (the novel part)
- `get_risk_radar()` — ranked list of your most dangerous unknowns + assumptions right now
  - Ranks by: high priority unknowns + low-confidence assumptions with severe consequences
- `get_blind_spots()` — assumptions that haven't been reviewed or challenged in 30+ days
- `get_stale_unknowns()` — open questions older than N days with no update
- `get_assumption_chain(assumption_key)` — what decisions depend on this assumption being true?
- `surface_uncertainties(context_text)` — given a topic/context string, return related open unknowns and risky assumptions

---

## Risk Score Formula
Used internally to rank items in `get_risk_radar()`:

```
assumption_risk = (1 - confidence) * consequence_weight
unknown_risk = priority_weight * age_in_days
```

consequence_weight and priority_weight are mapped from string fields to floats.

---

## File Structure
```
uncertainty.py          # new MCP module
uncertainty_data.json   # persistent storage
```

Storage structure:
```json
{
  "unknowns": {},
  "assumptions": {},
  "decisions": {}
}
```

---

## Implementation Steps

1. Define data structures and storage helpers (load/save JSON)
2. Build Unknowns tools
3. Build Assumptions tools
4. Build Decisions tools
5. Build Intelligence Layer (risk_radar, blind_spots, stale_unknowns, assumption_chain)
6. Build surface_uncertainties (keyword match across all three collections)
7. Register as FastMCP server
8. Add to claude_desktop_config.json

---

## What Makes This New
- No MCP server tracks uncertainty as a first-class concept
- The graph between unknowns → assumptions → decisions is unique
- `get_risk_radar()` gives Claude a live view of your blind spots
- `surface_uncertainties(context)` means Claude can proactively warn you when you're about to act on a risky assumption
- Over time this becomes a personal epistemics log — a record of what you didn't know and how it affected your choices
