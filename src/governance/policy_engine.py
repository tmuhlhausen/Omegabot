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


@dataclass
class StopPolicySnapshot:
    """Adaptive stop-loss/take-profit policy resolved per call."""

    stop_loss_pct: float
    take_profit_pct: float
    rationale: str


class StopPolicyController:
    """Self-adjusting stop policy.

    Tightens stops as drawdown grows or volatility spikes; widens stops in
    benign markets so winners can run. Output is deterministic given the input
    so it is safe for use in trade clearance loops.
    """

    def __init__(
        self,
        *,
        base_stop_pct: float = 0.04,
        base_take_profit_pct: float = 0.10,
        min_stop_pct: float = 0.01,
        max_stop_pct: float = 0.08,
    ) -> None:
        self.base_stop_pct = base_stop_pct
        self.base_take_profit_pct = base_take_profit_pct
        self.min_stop_pct = min_stop_pct
        self.max_stop_pct = max_stop_pct

    def resolve(
        self,
        *,
        drawdown_pct: float,
        volatility: float,
        risk_mode: str,
    ) -> StopPolicySnapshot:
        mode = risk_mode.upper()
        # tighten as drawdown deepens (per 1% drawdown shave 5% off stop)
        dd_factor = max(0.5, 1.0 - max(drawdown_pct, 0.0) * 0.05)
        # tighter stop in higher vol
        vol_factor = max(0.5, 1.0 - max(volatility - 0.5, 0.0))
        crisis_factor = 0.6 if mode == "CRISIS" else (0.85 if mode == "DEFENSIVE" else 1.0)

        stop = self.base_stop_pct * dd_factor * vol_factor * crisis_factor
        stop = min(self.max_stop_pct, max(self.min_stop_pct, stop))
        take_profit = max(stop * 1.5, self.base_take_profit_pct * crisis_factor)

        rationale = (
            f"mode={mode} dd={drawdown_pct:.2f} vol={volatility:.2f} "
            f"factors(dd={dd_factor:.2f},vol={vol_factor:.2f},crisis={crisis_factor:.2f})"
        )
        return StopPolicySnapshot(
            stop_loss_pct=round(stop, 4),
            take_profit_pct=round(take_profit, 4),
            rationale=rationale,
        )


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
