# Contract Expansion & Security Upgrade Plan

## Objectives
- Expand executor capabilities without increasing blast radius.
- Keep vault and execution modules compartmentalized by risk domain.
- Introduce additive upgrade paths with strict governance controls.

## Proposed Additions
1. **Executor Modules**
   - `LiqExecutorModule`
   - `ArbExecutorModule`
   - `YieldExecutorModule`
   Each module exposes bounded function surface and isolated role permissions.

2. **Upgrade Governance Layer**
   - Timelocked upgrades.
   - Role-separated proposer/executor.
   - Emergency guardian pause permissions.

3. **Invariant Suite**
   - No unauthorized transfer of user share.
   - Profit split invariants preserved across all code paths.
   - Debt repayment path cannot leave residual unbounded allowances.

4. **Security Monitoring Hooks**
   - Emit structured security events for anomaly watchers.
   - Add event index fields for faster forensic replay.

5. **Progressive Deployment**
   - Stage on testnet with shadow execution.
   - Canary deploy by strategy type.
   - Escalate only after invariant + incident-free windows.
