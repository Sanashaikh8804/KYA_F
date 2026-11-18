from __future__ import annotations

import os
from typing import Any


def apply_shadow_mode(decision: dict[str, Any]) -> dict[str, Any]:
    """Keep the recommendation visible while allowing the transaction in shadow mode."""
    if os.getenv("KYA_SHADOW_MODE", "").lower() not in {"1", "true", "yes"}:
        return decision
    result = dict(decision)
    result["recommended_action"] = decision["action"]
    result["action"] = "allow"
    result["shadow_mode"] = True
    return result
