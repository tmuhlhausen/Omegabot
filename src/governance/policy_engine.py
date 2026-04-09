from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PolicyContext:
    operation: str
    risk_mode: str
    amount_usd: float
    requires_human_approval: bool = False


class PolicyEngine:
    """Policy-as-code gate for high-risk operations."""

    def evaluate(self, ctx: PolicyContext) -> tuple[bool, str]:
        if ctx.risk_mode == "CRISIS" and ctx.amount_usd > 100:
            return False, "blocked_in_crisis"
        if ctx.requires_human_approval and ctx.amount_usd > 1000:
            return False, "approval_required"
        return True, "allowed"
