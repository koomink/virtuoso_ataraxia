from maestro.sdk import (
    BaseStrategyPlugin,
    DataBundle,
    DataRequest,
    StrategyContext,
    StrategyManifest,
    TargetAllocationResult,
)

DEFAULT_ALLOCATIONS = {
    "TIGER_NASDAQ100_LEVERAGE": 0.60,
    "KODEX_US_DIVIDEND_DOWJONES": 0.40,
}
DEFAULT_SLEEVE = "KRW"
STRATEGY_ID = "tranquillo"
STRATEGY_VERSION = "0.1.0"


class TranquilloStrategy(BaseStrategyPlugin):
    def manifest(self) -> StrategyManifest:
        return StrategyManifest(
            sdk_contract_version="1.1",
            strategy_id=STRATEGY_ID,
            name="Tranquillo",
            version=STRATEGY_VERSION,
            description="Monthly buy-only KRW ETF target allocation for Maestro.",
            supported_modes=["paper", "live_approval"],
            supported_asset_types=["cash", "etf", "domestic_etf"],
            result_type="target_allocation",
            requires_data=["price"],
            can_run_live=True,
            allow_direct_external_data_calls=False,
            estimated_runtime_seconds=5,
        )

    def build_data_requests(self, context: StrategyContext) -> list[DataRequest]:
        allocations = self._target_allocations(context)
        return [
            DataRequest(
                symbol=symbol,
                asset_type="domestic_etf",
                data_type="price",
                intended_use="tradable",
            )
            for symbol in allocations
        ]

    def run(self, data_bundle: DataBundle, context: StrategyContext) -> TargetAllocationResult:
        del data_bundle
        sleeve = str(context.config.get("sleeve", DEFAULT_SLEEVE))
        allocations = self._target_allocations(context)
        return TargetAllocationResult(
            strategy_id=context.strategy_id,
            strategy_version=STRATEGY_VERSION,
            timestamp=context.timestamp,
            allocations={},
            allocation_sleeves={sleeve: allocations},
            confidence=1.0,
            time_horizon="monthly",
            rationale="Static 60/40 KRW ETF target for Maestro buy-only contribution execution.",
            metadata={"execution_style": "buy_only_contribution"},
        )

    def _target_allocations(self, context: StrategyContext) -> dict[str, float]:
        allocations = context.config.get("allocations", DEFAULT_ALLOCATIONS)
        return {str(symbol): float(weight) for symbol, weight in allocations.items()}
