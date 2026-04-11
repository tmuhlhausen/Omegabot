from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PolicyContext:
    operation: str
    risk_mode: str
    amount_usd: float
    requires_human_approval: bool = False
    actor_tier: str = "default"


@dataclass(frozen=True)
class TierThreshold:
    max_amount_usd: float
    crisis_max_amount_usd: float


@dataclass(frozen=True)
class ApprovalWorkflow:
    operation: str
    min_amount_usd: float
    approvers_required: int


@dataclass(frozen=True)
class PolicyConfig:
    tiers: dict[str, TierThreshold] = field(default_factory=dict)
    workflows: tuple[ApprovalWorkflow, ...] = ()


class PolicyEngine:
    """Policy-as-code gate with tier thresholds and approval workflow routing.

    Engine interface contract (from ``src/core/engine.py`` call sites):
      - ``evaluate(PolicyContext) -> tuple[bool, str]`` where bool is allowed/blocked.
      - Reason strings are machine-readable for HUD/API surfaces.
      - Failure semantics are fail-closed: any limit/workflow violation returns blocked.
    """

    def __init__(self, config: PolicyConfig | None = None):
        self._config = config or self._default_config()

    @staticmethod
    def _default_config() -> PolicyConfig:
        return PolicyConfig(
            tiers={
                "default": TierThreshold(max_amount_usd=1_000, crisis_max_amount_usd=100),
                "operator": TierThreshold(max_amount_usd=10_000, crisis_max_amount_usd=500),
                "admin": TierThreshold(max_amount_usd=50_000, crisis_max_amount_usd=2_500),
            },
            workflows=(
                ApprovalWorkflow(operation="expand_chain", min_amount_usd=200, approvers_required=1),
                ApprovalWorkflow(operation="deploy_capital", min_amount_usd=1_500, approvers_required=2),
            ),
        )

    def evaluate(self, ctx: PolicyContext) -> tuple[bool, str]:
        tier = self._config.tiers.get(ctx.actor_tier, self._config.tiers["default"])
        risk_mode = ctx.risk_mode.upper()

        if risk_mode == "CRISIS" and ctx.amount_usd > tier.crisis_max_amount_usd:
            return False, "blocked_in_crisis"

        if ctx.amount_usd > tier.max_amount_usd:
            return False, "tier_limit_exceeded"

        if ctx.requires_human_approval:
            return False, "approval_required"

        for wf in self._config.workflows:
            if wf.operation == ctx.operation and ctx.amount_usd >= wf.min_amount_usd:
                return False, f"approval_required:{wf.approvers_required}"

        return True, "allowed"
