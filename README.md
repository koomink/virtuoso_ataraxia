# Ataraxia

Ataraxia is a Virtuoso Path A strategy for Maestro. It emits a KRW sleeve target
for a monthly buy-only contribution workflow; Maestro owns data acquisition,
order generation, account state, approval, and execution.

## Strategy

Default allocation:

- `TIGER_NASDAQ100_LEVERAGE`: 60%
- `KODEX_US_DIVIDEND_DOWJONES`: 40%

The strategy requests tradable `price` data for both domestic ETFs and returns a
`TargetAllocationResult` with KRW sleeve allocations. It does not call KIS or any
other broker/data API directly.

The manifest supports `paper` and `live_approval`. Live approval support means
Maestro may run the strategy in a live approval workflow; it does not move broker,
quote, account, or order-submission logic into Ataraxia.

## Maestro Registration

Ataraxia ships an app fragment at
`configs/fragments/ataraxia.yaml`. The fragment owns the strategy entrypoint,
default 60/40 strategy config, KRW sleeve membership, domestic ETF instrument
metadata, Yahoo symbol map hints, and the recommendation that this app is best
used with Maestro's `buy_only_contribution` order generation mode.

Operator profiles still own money-moving choices such as broker account,
approval, risk limits, state/audit paths, `order_posture`, `monthly_budget`, and
`buy_day`. Those values should live in the Maestro operator config or in a
private operator-local overlay, not in the app fragment.

```yaml
app_fragment_paths:
  - /root/projects/Symphony/Virtuoso/Ataraxia/configs/fragments/ataraxia.yaml

strategies:
  - id: ataraxia
    enabled: true
    weight: 1.0
```

Use Maestro's `buy_only_contribution` execution mode to turn this target into
monthly buy-only orders. Set `execution.contribution.monthly_budget` and
`execution.contribution.buy_day` in the operator config.

## Live Approval Preparation

`configs/ataraxia_kis_live_approval.example.yaml` is a safe example for KIS ISA
domestic ETF approval flow:

- It composes `configs/fragments/ataraxia.yaml`.
- KRW sleeve only.
- KIS domestic stock broker product only.
- ETF broker symbols `418660` and `489250`.
- Telegram approval required.
- Market session, reconciliation, broker quote, and broker risk gates enabled.
- Daily and per-order notional caps configured.
- `live_order_enabled: false` and `live_order_dry_run: true` by default.

Use private, uncommitted config for actual operation. Only that private config
should flip to `live_order_enabled: true` and `live_order_dry_run: false`.

Required KIS and approval values must come from environment variables:

```bash
export KIS_ACCOUNT_ID=...
export KIS_APP_KEY=...
export KIS_APP_SECRET=...
export KIS_ACCESS_TOKEN=...
export KIS_APPROVAL_KEY=...
export TELEGRAM_BOT_TOKEN=...
```

Do not commit account numbers, tokens, app keys, or Telegram chat/user IDs.

## Maestro Runtime Install

Install Ataraxia into the Maestro virtualenv before loading the strategy from a
Maestro config:

```bash
cd /root/projects/Symphony/Maestro
uv pip install --python .venv/bin/python /root/projects/Symphony/Virtuoso/Ataraxia
```

Use a normal package install for operator rehearsals so Maestro does not depend
on `PYTHONPATH` or an editable source path. Reinstall with the same command after
Ataraxia code changes.

Then progress through the operational modes:

1. Paper: run the Yahoo paper config and confirm target allocations and
   buy-only contribution orders.
2. Dry-run approval: run the live approval example with
   `live_order_enabled: false` and `live_order_dry_run: true`; confirm Telegram
   approval and live gates block broker submission.
3. Live approval: use a private config with real env vars and explicit operator
   approval before broker submission.
