"""
Infrastructure Simulation Engine for AutoSE Platform.

Deterministic engineering simulation that models power load, GPU workload,
and thermal behaviour of a proposed infrastructure solution.

Design principles
-----------------
- Pure deterministic Python logic — no LLM calls, no randomness.
- All inputs are validated through schema_guard before processing.
- Invalid inputs are rejected immediately via GuardResult.raise_if_invalid().
- Every simulation stage is logged for auditability.

Usage::

    from src.simulation.infrastructure_sim import run_infrastructure_simulation
    from src.schemas.solution_schema import Solution

    result = run_infrastructure_simulation(solution)
    print(result.to_dict())
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

# ---------------------------------------------------------------------------
# Schema guard — MUST be used before any processing
# ---------------------------------------------------------------------------
try:
    from src.core.schema_guard import validate_solution
    from src.schemas.solution_schema import Solution, Product, Requirement
except ImportError:
    try:
        from core.schema_guard import validate_solution  # type: ignore[no-redef]
        from schemas.solution_schema import Solution, Product, Requirement  # type: ignore[no-redef]
    except ImportError:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from src.core.schema_guard import validate_solution  # type: ignore[no-redef]
        from src.schemas.solution_schema import Solution, Product, Requirement  # type: ignore[no-redef]

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger("autose.infrastructure_sim")

if not logger.handlers:
    logger.addHandler(logging.NullHandler())

# ---------------------------------------------------------------------------
# Simulation thresholds (engineering constants)
# ---------------------------------------------------------------------------

# Power load thresholds (fraction of effective capacity)
POWER_SAFE_RATIO: float = 0.60       # < 60 %  → safe
POWER_WARNING_RATIO: float = 0.85    # 60–85 % → warning
# > 85 % → critical

# Default power ceiling when no UPS is present in the solution
DEFAULT_POWER_CEILING_W: int = 5_000

# GPU workload thresholds (cameras per GPU)
GPU_CAMERAS_PER_GPU_SAFE: int = 30   # <= 30 cameras/GPU → comfortable
GPU_CAMERAS_PER_GPU_WARN: int = 50   # 31–50 cameras/GPU → approaching limit
# > 50 cameras/GPU → bottleneck

# Thermal thresholds — power density proxy (W per server unit)
THERMAL_SAFE_W: float = 1_200.0      # < 1200 W/server → safe
THERMAL_WARNING_W: float = 2_000.0   # 1200–2000 W/server → warning
# > 2000 W/server → critical

# ---------------------------------------------------------------------------
# SimulationResult dataclass
# ---------------------------------------------------------------------------

# Status literals
_STATUS = {"safe", "warning", "critical"}


@dataclass
class SimulationResult:
    """
    Structured output of run_infrastructure_simulation().

    Attributes
    ----------
    power_status : str
        "safe" | "warning" | "critical"
    gpu_bottleneck : bool
        True when GPU demand exceeds comfortable capacity.
    thermal_status : str
        "safe" | "warning" | "critical"
    warnings : List[str]
        Human-readable advisory messages generated during simulation.

    Internal diagnostics (not part of the public contract but useful for
    debugging and downstream agents):
    total_power_w, ups_capacity_w, power_utilisation_pct,
    total_gpus, cameras_per_gpu, thermal_density_w_per_server
    """

    # --- Public contract fields ---
    power_status: str
    gpu_bottleneck: bool
    thermal_status: str
    warnings: List[str] = field(default_factory=list)

    # --- Diagnostic fields ---
    total_power_w: int = 0
    ups_capacity_w: int = 0
    power_utilisation_pct: float = 0.0
    total_gpus: int = 0
    cameras_per_gpu: float = 0.0
    thermal_density_w_per_server: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Return the public contract dict.

        Shape matches the required output format::

            {
                "power_status": "safe|warning|critical",
                "gpu_bottleneck": true|false,
                "thermal_status": "safe|warning|critical",
                "warnings": [...]
            }
        """
        return {
            "power_status": self.power_status,
            "gpu_bottleneck": self.gpu_bottleneck,
            "thermal_status": self.thermal_status,
            "warnings": list(self.warnings),
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """Return the full dict including internal diagnostics."""
        d = self.to_dict()
        d.update({
            "diagnostics": {
                "total_power_w": self.total_power_w,
                "ups_capacity_w": self.ups_capacity_w,
                "power_utilisation_pct": round(self.power_utilisation_pct, 1),
                "total_gpus": self.total_gpus,
                "cameras_per_gpu": round(self.cameras_per_gpu, 1),
                "thermal_density_w_per_server": round(self.thermal_density_w_per_server, 1),
            }
        })
        return d


# ---------------------------------------------------------------------------
# Internal simulation stages
# ---------------------------------------------------------------------------

def _simulate_power(
    products: List[Product],
    requirement: Requirement,
) -> tuple[str, int, int, float, List[str]]:
    """
    Stage 1 — Power simulation.

    Returns
    -------
    (status, total_power_w, ups_capacity_w, utilisation_pct, stage_warnings)
    """
    stage_warnings: List[str] = []

    # Sum product power draw
    product_power_w: int = sum(p.power_w for p in products)

    # Add ancillary power from requirement (cabling, patch panels, etc.)
    total_power_w: int = product_power_w + requirement.estimated_power_w

    # Determine effective power ceiling
    ups_capacity_w: int = sum(
        p.capacity.capacity_w
        for p in products
        if p.category == "power" and p.capacity.capacity_w > 0
    )
    effective_ceiling: int = ups_capacity_w if ups_capacity_w > 0 else DEFAULT_POWER_CEILING_W

    utilisation: float = total_power_w / effective_ceiling if effective_ceiling > 0 else 1.0

    logger.debug(
        "Power simulation | total_power_w=%d | ups_capacity_w=%d | "
        "effective_ceiling_w=%d | utilisation=%.1f%%",
        total_power_w, ups_capacity_w, effective_ceiling, utilisation * 100,
    )

    # Classify
    if utilisation < POWER_SAFE_RATIO:
        status = "safe"
    elif utilisation <= POWER_WARNING_RATIO:
        status = "warning"
        msg = (
            "Power utilisation is {:.1f}% of capacity ({} W / {} W). "
            "Headroom is limited — consider adding UPS capacity or "
            "removing non-essential devices.".format(
                utilisation * 100, total_power_w, effective_ceiling
            )
        )
        stage_warnings.append(msg)
        logger.warning("Power stage WARNING: %s", msg)
    else:
        status = "critical"
        msg = (
            "Power utilisation is {:.1f}% of capacity ({} W / {} W). "
            "System is at risk of overload — add UPS capacity immediately "
            "or reduce device count.".format(
                utilisation * 100, total_power_w, effective_ceiling
            )
        )
        stage_warnings.append(msg)
        logger.warning("Power stage CRITICAL: %s", msg)

    # Additional advisory: no UPS present for significant load
    if ups_capacity_w == 0 and total_power_w > 1_000:
        msg = (
            "No UPS detected in solution. Total power draw is {} W — "
            "power failure will cause immediate system outage.".format(total_power_w)
        )
        stage_warnings.append(msg)
        logger.warning("Power stage advisory: %s", msg)

    logger.info("Power simulation complete | status=%s", status)
    return status, total_power_w, ups_capacity_w, utilisation * 100, stage_warnings


def _simulate_gpu(
    products: List[Product],
    requirement: Requirement,
) -> tuple[bool, int, float, List[str]]:
    """
    Stage 2 — GPU bottleneck simulation.

    Returns
    -------
    (bottleneck, total_gpus, cameras_per_gpu, stage_warnings)
    """
    stage_warnings: List[str] = []

    # GPU is only relevant when AI inference is required
    if not requirement.gpu_required:
        logger.info("GPU simulation skipped | gpu_required=False")
        return False, 0, 0.0, []

    # Count available GPUs across all server products
    total_gpus: int = sum(
        p.capacity.gpu_count
        for p in products
        if p.category == "server"
    )

    # Effective device count for GPU demand
    device_count: int = max(
        requirement.device_count,
        requirement.camera_count,
    )

    logger.debug(
        "GPU simulation | total_gpus=%d | device_count=%d",
        total_gpus, device_count,
    )

    # No GPUs at all
    if total_gpus == 0:
        msg = (
            "GPU acceleration is required for {} devices but no GPU-enabled "
            "server is present in the solution. AI inference will fail.".format(
                device_count
            )
        )
        stage_warnings.append(msg)
        logger.warning("GPU stage CRITICAL: %s", msg)
        logger.info("GPU simulation complete | bottleneck=True | cameras_per_gpu=N/A")
        return True, 0, float("inf"), stage_warnings

    cameras_per_gpu: float = device_count / total_gpus

    logger.debug("GPU simulation | cameras_per_gpu=%.1f", cameras_per_gpu)

    if cameras_per_gpu <= GPU_CAMERAS_PER_GPU_SAFE:
        bottleneck = False
        logger.info(
            "GPU simulation complete | bottleneck=False | cameras_per_gpu=%.1f",
            cameras_per_gpu,
        )
    elif cameras_per_gpu <= GPU_CAMERAS_PER_GPU_WARN:
        bottleneck = False
        msg = (
            "{:.0f} cameras per GPU (threshold: {}). GPU utilisation is high — "
            "monitor inference latency under peak load.".format(
                cameras_per_gpu, GPU_CAMERAS_PER_GPU_WARN
            )
        )
        stage_warnings.append(msg)
        logger.warning("GPU stage WARNING: %s", msg)
        logger.info(
            "GPU simulation complete | bottleneck=False (approaching) | cameras_per_gpu=%.1f",
            cameras_per_gpu,
        )
    else:
        bottleneck = True
        msg = (
            "{:.0f} cameras per GPU exceeds the recommended limit of {}. "
            "GPU bottleneck detected — add {} more GPU(s) to meet demand.".format(
                cameras_per_gpu,
                GPU_CAMERAS_PER_GPU_WARN,
                max(1, int(device_count / GPU_CAMERAS_PER_GPU_WARN) - total_gpus + 1),
            )
        )
        stage_warnings.append(msg)
        logger.warning("GPU stage BOTTLENECK: %s", msg)
        logger.info(
            "GPU simulation complete | bottleneck=True | cameras_per_gpu=%.1f",
            cameras_per_gpu,
        )

    return bottleneck, total_gpus, cameras_per_gpu, stage_warnings


def _simulate_thermal(
    products: List[Product],
    requirement: Requirement,
    total_power_w: int,
) -> tuple[str, float, List[str]]:
    """
    Stage 3 — Thermal simulation.

    Uses total power density (W per server unit) as a proxy for heat
    generation.  More servers spread the heat load; fewer servers
    concentrate it.

    Returns
    -------
    (status, density_w_per_server, stage_warnings)
    """
    stage_warnings: List[str] = []

    server_count: int = sum(1 for p in products if p.category == "server")

    # If no servers, use total product count as denominator (conservative)
    denominator: int = server_count if server_count > 0 else max(1, len(products))
    density: float = total_power_w / denominator

    logger.debug(
        "Thermal simulation | total_power_w=%d | server_count=%d | density=%.1f W/server",
        total_power_w, server_count, density,
    )

    if density < THERMAL_SAFE_W:
        status = "safe"
    elif density <= THERMAL_WARNING_W:
        status = "warning"
        msg = (
            "Thermal density is {:.0f} W per server unit (threshold: {} W). "
            "Ensure adequate rack cooling and airflow management.".format(
                density, THERMAL_WARNING_W
            )
        )
        stage_warnings.append(msg)
        logger.warning("Thermal stage WARNING: %s", msg)
    else:
        status = "critical"
        msg = (
            "Thermal density is {:.0f} W per server unit, exceeding the critical "
            "threshold of {} W. Risk of thermal throttling or hardware failure — "
            "deploy precision cooling (CRAC/CRAH) and hot-aisle containment.".format(
                density, THERMAL_WARNING_W
            )
        )
        stage_warnings.append(msg)
        logger.warning("Thermal stage CRITICAL: %s", msg)

    logger.info("Thermal simulation complete | status=%s | density=%.1f W/server", status, density)
    return status, density, stage_warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_infrastructure_simulation(
    solution: Union[Solution, Dict[str, Any]],
) -> SimulationResult:
    """
    Run a deterministic infrastructure simulation on a proposed solution.

    The function validates the input through schema_guard before any
    processing.  Invalid inputs are rejected immediately.

    Parameters
    ----------
    solution : Solution | dict
        A canonical Solution instance or a dict that can be auto-converted
        to one.  Legacy pipeline-result dicts are accepted.

    Returns
    -------
    SimulationResult
        Structured simulation output with power_status, gpu_bottleneck,
        thermal_status, and warnings.

    Raises
    ------
    ValueError
        If the input cannot be validated as a canonical Solution.

    Examples
    --------
    ::

        from src.simulation.infrastructure_sim import run_infrastructure_simulation
        from src.schemas.solution_schema import Solution, Requirement, Product

        req = Requirement(device_count=100, gpu_required=True, estimated_power_w=500)
        products = [
            Product.from_catalog_dict({
                "name": "AI Server X2", "category": "server",
                "power_w": 1500, "price": 28000, "gpu": 8, "max_cameras": 120,
            }),
        ]
        sol = Solution(requirement=req, selected_products=products)
        result = run_infrastructure_simulation(sol)
        print(result.to_dict())
    """
    # ------------------------------------------------------------------
    # Step 1: Validate input via schema_guard
    # ------------------------------------------------------------------
    logger.info(
        "Infrastructure simulation starting | input_type=%s",
        type(solution).__name__,
    )

    # If already a canonical Solution instance, accept directly without
    # round-tripping through model_dump (which loses nested Product objects).
    # We check by class name + module suffix to handle the case where the same
    # schema is imported via two different sys.path roots (e.g. 'schemas' vs
    # 'src.schemas'), which would make isinstance() return False even for
    # structurally identical objects.
    def _is_solution_instance(obj: object) -> bool:
        cls = type(obj)
        return (
            isinstance(obj, Solution)
            or (
                cls.__name__ == "Solution"
                and cls.__module__.endswith("solution_schema")
            )
        )

    if _is_solution_instance(solution):
        validated: Solution = solution  # type: ignore[assignment]
        logger.debug(
            "Input is already a canonical Solution instance — skipping guard round-trip"
        )
    else:
        guard_result = validate_solution(solution)

        if not guard_result.valid:
            logger.error(
                "Infrastructure simulation REJECTED | validation_errors=%s",
                guard_result.errors,
            )

        # Raises ValueError with full error detail if invalid — never silently passes
        validated = guard_result.raise_if_invalid()

    logger.info(
        "Input validation passed | products=%d | device_count=%d | gpu_required=%s",
        len(validated.selected_products),
        validated.requirement.device_count,
        validated.requirement.gpu_required,
    )

    products = validated.selected_products
    requirement = validated.requirement

    # ------------------------------------------------------------------
    # Step 2: Run simulation stages
    # ------------------------------------------------------------------
    all_warnings: List[str] = []

    # Stage 1 — Power
    logger.info("Running Stage 1: Power simulation")
    (
        power_status,
        total_power_w,
        ups_capacity_w,
        power_utilisation_pct,
        power_warnings,
    ) = _simulate_power(products, requirement)
    all_warnings.extend(power_warnings)

    # Stage 2 — GPU bottleneck
    logger.info("Running Stage 2: GPU bottleneck simulation")
    gpu_bottleneck, total_gpus, cameras_per_gpu, gpu_warnings = _simulate_gpu(
        products, requirement
    )
    all_warnings.extend(gpu_warnings)

    # Stage 3 — Thermal
    logger.info("Running Stage 3: Thermal simulation")
    thermal_status, thermal_density, thermal_warnings = _simulate_thermal(
        products, requirement, total_power_w
    )
    all_warnings.extend(thermal_warnings)

    # ------------------------------------------------------------------
    # Step 3: Assemble result
    # ------------------------------------------------------------------
    result = SimulationResult(
        power_status=power_status,
        gpu_bottleneck=gpu_bottleneck,
        thermal_status=thermal_status,
        warnings=all_warnings,
        # diagnostics
        total_power_w=total_power_w,
        ups_capacity_w=ups_capacity_w,
        power_utilisation_pct=power_utilisation_pct,
        total_gpus=total_gpus,
        cameras_per_gpu=cameras_per_gpu if cameras_per_gpu != float("inf") else -1.0,
        thermal_density_w_per_server=thermal_density,
    )

    logger.info(
        "Infrastructure simulation complete | power=%s | gpu_bottleneck=%s | "
        "thermal=%s | warning_count=%d",
        result.power_status,
        result.gpu_bottleneck,
        result.thermal_status,
        len(result.warnings),
    )

    return result
