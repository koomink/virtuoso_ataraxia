from datetime import UTC, datetime
from pathlib import Path

from maestro.config.loader import load_config
from maestro.sdk import BaseStrategyPlugin, DataBundle, StrategyContext, TargetAllocationResult

from ataraxia.strategy import AtaraxiaStrategy


def test_ataraxia_strategy_contract_and_sdk_boundary():
    strategy = AtaraxiaStrategy()
    context = StrategyContext(
        cycle_id="test",
        timestamp=datetime.now(UTC),
        run_mode="paper",
        strategy_id="ataraxia",
        config={
            "sleeve": "KRW",
            "allocations": {
                "TIGER_NASDAQ100_LEVERAGE": 0.60,
                "KODEX_US_DIVIDEND_DOWJONES": 0.40,
            },
        },
    )

    manifest = strategy.manifest()
    requests = strategy.build_data_requests(context)
    result = strategy.run(
        DataBundle(requests=requests, data={}, generated_at=datetime.now(UTC), source="test"),
        context,
    )

    assert isinstance(strategy, BaseStrategyPlugin)
    assert isinstance(result, TargetAllocationResult)
    assert manifest.sdk_contract_version == "1.1"
    assert manifest.supported_modes == ["paper", "live_approval"]
    assert manifest.can_run_live is True
    assert {request.symbol for request in requests} == {
        "TIGER_NASDAQ100_LEVERAGE",
        "KODEX_US_DIVIDEND_DOWJONES",
    }
    assert {request.data_type for request in requests} == {"price"}
    assert {request.asset_type for request in requests} == {"domestic_etf"}
    assert result.allocations == {}
    assert result.allocation_sleeves == {
        "KRW": {
            "TIGER_NASDAQ100_LEVERAGE": 0.60,
            "KODEX_US_DIVIDEND_DOWJONES": 0.40,
        }
    }

    source = Path("src/ataraxia/strategy.py").read_text()
    assert "from maestro.sdk import" in source
    assert "maestro.portfolio" not in source
    assert "maestro.risk" not in source
    assert "maestro.execution" not in source
    assert "maestro.state" not in source
    assert "maestro.datahub" not in source
    assert "maestro.orchestration" not in source
    assert "koreainvestment" not in source.lower()


def test_ataraxia_live_approval_contract_stays_strategy_only():
    strategy = AtaraxiaStrategy()
    context = StrategyContext(
        cycle_id="test-live",
        timestamp=datetime.now(UTC),
        run_mode="live_approval",
        strategy_id="ataraxia",
        config={"sleeve": "KRW"},
    )

    result = strategy.run(
        DataBundle(requests=[], data={}, generated_at=datetime.now(UTC), source="test"),
        context,
    )

    assert result.allocations == {}
    assert result.allocation_sleeves == {
        "KRW": {
            "TIGER_NASDAQ100_LEVERAGE": 0.60,
            "KODEX_US_DIVIDEND_DOWJONES": 0.40,
        }
    }
    assert result.metadata == {"execution_style": "buy_only_contribution"}


def test_live_approval_example_config_loads_with_safe_defaults():
    config = load_config("configs/ataraxia_kis_live_approval.example.yaml")

    assert config.mode == "live_approval"
    assert config.portfolio.base_currency == "KRW"
    assert config.execution.order_generation_mode == "buy_only_contribution"
    assert config.execution.live_order_enabled is False
    assert config.execution.live_order_dry_run is True
    assert config.execution.require_market_session is True
    assert config.execution.require_reconciliation_pass is True
    assert config.execution.require_broker_quote_validation is True
    assert config.execution.require_broker_risk_validation is True
    assert config.approval.enabled is True
    assert config.approval.provider == "telegram"
    assert config.approval.require_approval is True
    assert config.kis.enabled is True
    assert config.kis.provider == "kis"
    assert [item.value for item in config.kis.effective_broker_products()] == ["kis_domestic_stock"]
    assert config.kis.account_id is None
    assert config.kis.account_id_env == "KIS_ACCOUNT_ID"
    assert config.universe.get("TIGER_NASDAQ100_LEVERAGE").broker_symbol == "418660"
    assert config.universe.get("KODEX_US_DIVIDEND_DOWJONES").broker_symbol == "489250"
    assert {
        config.universe.get("TIGER_NASDAQ100_LEVERAGE").broker_product,
        config.universe.get("KODEX_US_DIVIDEND_DOWJONES").broker_product,
    } == {"kis_domestic_stock"}
