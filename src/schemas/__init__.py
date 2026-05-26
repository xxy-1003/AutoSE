"""AutoSE canonical schema package.

All new modules MUST import their data contracts from this package
rather than defining ad-hoc dicts or local models.
"""

from .solution_schema import (
    Product,
    Requirement,
    Solution,
    CapacityMetrics,
    RiskEntry,
    RiskReport,
    SeverityLevel,
    CheckStatus,
)

__all__ = [
    "Product",
    "Requirement",
    "Solution",
    "CapacityMetrics",
    "RiskEntry",
    "RiskReport",
    "SeverityLevel",
    "CheckStatus",
]
