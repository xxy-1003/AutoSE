"""
Fusion Engine for AutoSE Platform.

Combines the outputs of the Risk Intelligence Agent and the Infrastructure
Simulation Engine into a single unified enterprise intelligence assessment.

Design principles
-----------------
- Pure deterministic logic — no LLM calls, no randomness.
- All Solution inputs are validated through schema_guard.
- RiskReport and SimulationResult are accepted as-is (already produced by
  validated agents) or as plain dicts (auto-normalised internally).
- Decision rules are explicit, auditable, and logged at every branch.

Decision rule summary
---------------------
system_status:
  critical  — any risk.severity == "high"  AND  any sim status == "critical"
  degraded  — any sim status == "warning"  OR   any risk.severity == "medium"
  healthy   — all sim statuses == "safe"   AND  no risk severity above "low"

deployment_readiness:
  False when system_status == "critical"
  True  otherwise

key_blockers:
  Populated from high-severity risks and critical simulation statuses.

optimization_suggestions:
  Generated deterministically from risk types and simulation statuses.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Union

# ---------------------------------------------------------------------------
# Imports — schema types and guard
# ---------------------------------------------------------------------------
try:
    from src.core.schema_guard import validate_solution
    from src.schemas.solution_schema import (
        Solution,
        RiskReport,
        RiskEntry,
        SeverityLevel,
    )
    from src.simulation.infrastructure_sim import SimulationResult
except ImportError:
    try:
        from core.schema_guard import validate_solution  # type: ignore[no-redef]
        from schemas.solution_schema import (  # type: ignore[no-redef]
            Solution,
            RiskReport,
            RiskEntry,
            SeverityLevel,
        )
        from simulation.infrastructure_sim import SimulationResult  # type: ignore[no-redef]
    except ImportError:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from src.core.schema_guard import validate_solution  # type: ignore[no-redef]
        from src.schemas.solution_schema import (  # type: ignore[no-redef]
            Solution,
            RiskReport,
            RiskEntry,
            SeverityLevel,
        )
        from src.simulation.infrastructure_sim import SimulationResult  # type: ignore[no-redef]

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger("autose.fusion_engine")

if not logger.handlers:
    logger.addHandler(logging.NullHandler())

# ---------------------------------------------------------------------------
# Internal normalisation helpers
# ---------------------------------------------------------------------------

def _is_instance_by_name(obj: object, class_name: str, module_suffix: str) -> bool:
    """
    Duck-type check by class name + module suffix.

    Handles the case where the same class is imported via two different
    sys.path roots (e.g. 'schemas' vs 'src.schemas').
    """
    cls = type(obj)
    return cls.__name__ == class_name and cls.__module__.endswith(module_suffix)


def _normalise_solution(
    solution: Union[Solution, Dict[str, Any]],
) -> Solution:
    """
    Validate and return a canonical Solution.

    Accepts a Solution instance (any import path) or a dict.
    Raises ValueError via raise_if_invalid() on failure.
    """
    if _is_instance_by_name(solution, "Solution", "solution_schema"):
        logger.debug("Solution input accepted as canonical instance")
        return solution  # type: ignore[return-value]

    logger.debug("Solution input is a dict — running schema_guard validation")
    guard = validate_solution(solution)
    if not guard.valid:
        logger.error(
            "Fusion engine rejected invalid Solution | errors=%s", guard.errors
        )
    return guard.raise_if_invalid()


def _normalise_risk_report(
    risk_report: Union[RiskReport, Dict[str, Any]],
) -> RiskReport:
    """
    Normalise a RiskReport from either a canonical instance or a raw dict.

    The raw dict shape is the output of risk_agent.analyze_risks()::

        {
            "risks": [{"type": ..., "severity": ..., "likelihood": ...,
                       "description": ..., "mitigation": ...}],
            "overall_risk_score": float
        }
    """
    if _is_instance_by_name(risk_report, "RiskReport", "solution_schema"):
        return risk_report  # type: ignore[return-value]

    if isinstance(risk_report, dict):
        try:
            return RiskReport.from_agent_output(risk_report)
        except Exception as exc:
            raise ValueError(
                "Cannot normalise RiskReport from dict: {}".format(exc)
            ) from exc

    raise TypeError(
        "risk_report must be a RiskReport instance or dict, got {}".format(
            type(risk_report).__name__
        )
    )


def _normalise_simulation_result(
    simulation_result: Union[SimulationResult, Dict[str, Any]],
) -> SimulationResult:
    """
    Normalise a SimulationResult from either a dataclass instance or a dict.

    The dict shape is the output of SimulationResult.to_dict()::

        {
            "power_status": "safe|warning|critical",
            "gpu_bottleneck": bool,
            "thermal_status": "safe|warning|critical",
            "warnings": [...]
        }
    """
    if isinstance(simulation_result, SimulationResult):
        return simulation_result

    # Also accept by class name for cross-import-path compatibility
    if _is_instance_by_name(simulation_result, "SimulationResult", "infrastructure_sim"):
        return simulation_result  # type: ignore[return-value]

    if isinstance(simulation_result, dict):
        try:
            return SimulationResult(
                power_status=simulation_result.get("power_status", "safe"),
                gpu_bottleneck=bool(simulation_result.get("gpu_bottleneck", False)),
                thermal_status=simulation_result.get("thermal_status", "safe"),
                warnings=list(simulation_result.get("warnings", [])),
                total_power_w=simulation_result.get(
                    "diagnostics", {}
                ).get("total_power_w", 0),
                ups_capacity_w=simulation_result.get(
                    "diagnostics", {}
                ).get("ups_capacity_w", 0),
                power_utilisation_pct=simulation_result.get(
                    "diagnostics", {}
                ).get("power_utilisation_pct", 0.0),
                total_gpus=simulation_result.get(
                    "diagnostics", {}
                ).get("total_gpus", 0),
                cameras_per_gpu=simulation_result.get(
                    "diagnostics", {}
                ).get("cameras_per_gpu", 0.0),
                thermal_density_w_per_server=simulation_result.get(
                    "diagnostics", {}
                ).get("thermal_density_w_per_server", 0.0),
            )
        except Exception as exc:
            raise ValueError(
                "Cannot normalise SimulationResult from dict: {}".format(exc)
            ) from exc

    raise TypeError(
        "simulation_result must be a SimulationResult instance or dict, got {}".format(
            type(simulation_result).__name__
        )
    )


# ---------------------------------------------------------------------------
# Decision logic helpers
# ---------------------------------------------------------------------------

def _has_severity(risks: List[RiskEntry], level: str) -> bool:
    """Return True if any risk entry has the given severity level."""
    return any(
        (r.severity.value if hasattr(r.severity, "value") else r.severity) == level
        for r in risks
    )


def _sim_has_status(sim: SimulationResult, status: str) -> bool:
    """Return True if any simulation dimension has the given status."""
    return sim.power_status == status or sim.thermal_status == status


def _determine_system_status(
    risks: List[RiskEntry],
    sim: SimulationResult,
) -> tuple[str, List[str]]:
    """
    Apply decision rules and return (system_status, triggered_rules).

    Rules (evaluated in priority order — first match wins):
    1. critical  — any high-severity risk  AND  any sim status == critical
    2. degraded  — any sim status == warning  OR  any medium-severity risk
    3. healthy   — all sim statuses safe  AND  no risk above low severity
    """
    triggered: List[str] = []

    has_high = _has_severity(risks, "high")
    has_medium = _has_severity(risks, "medium")
    sim_critical = _sim_has_status(sim, "critical")
    sim_warning = _sim_has_status(sim, "warning")

    # Rule 1 — critical
    if has_high and sim_critical:
        triggered.append(
            "RULE_CRITICAL: high-severity risk detected AND simulation critical status"
        )
        logger.info(
            "Decision rule triggered | rule=CRITICAL | has_high_risk=%s | sim_critical=%s",
            has_high, sim_critical,
        )
        return "critical", triggered

    # Rule 2 — degraded
    if sim_warning or has_medium:
        if sim_warning:
            triggered.append("RULE_DEGRADED: simulation warning status present")
        if has_medium:
            triggered.append("RULE_DEGRADED: medium-severity risk present")
        logger.info(
            "Decision rule triggered | rule=DEGRADED | sim_warning=%s | has_medium=%s",
            sim_warning, has_medium,
        )
        return "degraded", triggered

    # Rule 3 — healthy (also catches: high risk but sim not critical → degraded
    #           via the implicit else below)
    if has_high and not sim_critical:
        # High risk exists but simulation is not critical — still degraded
        triggered.append(
            "RULE_DEGRADED: high-severity risk present (simulation not critical)"
        )
        logger.info(
            "Decision rule triggered | rule=DEGRADED | has_high_risk=True | sim_critical=False"
        )
        return "degraded", triggered

    triggered.append("RULE_HEALTHY: no high/medium risks and all simulation statuses safe")
    logger.info("Decision rule triggered | rule=HEALTHY")
    return "healthy", triggered


def _build_key_blockers(
    risks: List[RiskEntry],
    sim: SimulationResult,
) -> List[str]:
    """
    Collect blockers from high-severity risks and critical simulation statuses.
    """
    blockers: List[str] = []

    # High-severity risks
    for risk in risks:
        sev = risk.severity.value if hasattr(risk.severity, "value") else risk.severity
        if sev == "high":
            blockers.append(
                "[RISK] {} (severity=high, likelihood={:.0%}): {}".format(
                    risk.type, risk.likelihood, risk.description
                )
            )

    # Critical simulation dimensions
    if sim.power_status == "critical":
        blockers.append(
            "[SIM] Power utilisation critical ({:.1f}% of capacity)".format(
                sim.power_utilisation_pct
            )
        )
    if sim.thermal_status == "critical":
        blockers.append(
            "[SIM] Thermal density critical ({:.0f} W/server)".format(
                sim.thermal_density_w_per_server
            )
        )
    if sim.gpu_bottleneck:
        blockers.append(
            "[SIM] GPU bottleneck detected ({:.0f} cameras/GPU)".format(
                sim.cameras_per_gpu if sim.cameras_per_gpu >= 0 else 0
            )
        )

    logger.info("Key blockers identified | count=%d | blockers=%s", len(blockers), blockers)
    return blockers


def _build_optimization_suggestions(
    risks: List[RiskEntry],
    sim: SimulationResult,
    solution: Solution,
) -> List[str]:
    """
    Generate deterministic optimization suggestions from risk types and
    simulation statuses.

    Rules:
    - power_overload risk OR power sim warning/critical → UPS / load reduction
    - gpu_bottleneck risk OR gpu_bottleneck sim flag    → GPU cluster scaling
    - thermal_risk risk OR thermal sim warning/critical → cooling improvement
    - network_saturation risk                           → network segmentation
    - budget headroom available                         → upgrade opportunity
    """
    suggestions: List[str] = []
    risk_types = {
        (r.type if isinstance(r.type, str) else r.type)
        for r in risks
    }

    # Power
    if "power_overload" in risk_types or sim.power_status in ("warning", "critical"):
        if sim.ups_capacity_w > 0:
            suggestions.append(
                "Upgrade UPS capacity: current {ups}W is insufficient for "
                "{load}W load. Consider a {rec}W UPS or add a second unit.".format(
                    ups=sim.ups_capacity_w,
                    load=sim.total_power_w,
                    rec=int(sim.total_power_w * 1.3),
                )
            )
        else:
            suggestions.append(
                "Add a UPS unit: no power backup detected for a {load}W system. "
                "Minimum recommended capacity: {rec}W.".format(
                    load=sim.total_power_w,
                    rec=int(sim.total_power_w * 1.3),
                )
            )
        suggestions.append(
            "Reduce power load: audit high-draw devices and replace with "
            "energy-efficient alternatives or stagger startup sequences."
        )

    # GPU
    if "gpu_bottleneck" in risk_types or sim.gpu_bottleneck:
        device_count = solution.requirement.device_count
        current_gpus = sim.total_gpus
        recommended_gpus = max(1, int(device_count / 30))  # 30 cameras/GPU target
        additional = max(0, recommended_gpus - current_gpus)
        suggestions.append(
            "Scale GPU cluster: add {add} GPU(s) to reach the recommended "
            "{rec} GPU(s) for {dev} devices (target: 30 cameras/GPU).".format(
                add=additional,
                rec=recommended_gpus,
                dev=device_count,
            )
        )
        suggestions.append(
            "Implement GPU load balancing: distribute inference workloads "
            "across available GPUs using a model-serving framework "
            "(e.g. Triton Inference Server, TorchServe)."
        )

    # Thermal
    if "thermal_risk" in risk_types or sim.thermal_status in ("warning", "critical"):
        suggestions.append(
            "Improve cooling infrastructure: thermal density is {density:.0f} W/server. "
            "Deploy precision air conditioning (CRAC/CRAH) and implement "
            "hot-aisle/cold-aisle containment.".format(
                density=sim.thermal_density_w_per_server
            )
        )
        suggestions.append(
            "Add temperature monitoring: deploy rack-level sensors with "
            "automated alerts at 35°C inlet and 45°C exhaust thresholds."
        )

    # Network
    if "network_saturation" in risk_types:
        suggestions.append(
            "Segment network into VLANs to reduce broadcast domains and "
            "isolate AI inference traffic from management traffic."
        )
        suggestions.append(
            "Upgrade to 10 GbE switching fabric with QoS policies to "
            "prioritise real-time video and AI inference streams."
        )

    # Budget headroom — suggest proactive upgrades if budget allows
    budget = solution.requirement.budget
    cost = solution.estimated_cost
    if budget > 0 and cost > 0 and cost < budget * 0.80:
        headroom = budget - cost
        suggestions.append(
            "Budget headroom available: ${headroom:,.0f} remaining "
            "({pct:.0f}% of budget). Consider proactive upgrades to "
            "redundant power, additional GPU capacity, or expanded storage.".format(
                headroom=headroom,
                pct=(headroom / budget) * 100,
            )
        )

    # Deduplicate while preserving order
    seen: set = set()
    unique: List[str] = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    return unique


def _build_risk_summary(
    risk_report: RiskReport,
) -> Dict[str, Any]:
    """Compact summary of the risk report for the output envelope."""
    severity_counts: Dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for risk in risk_report.risks:
        sev = risk.severity.value if hasattr(risk.severity, "value") else risk.severity
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "overall_risk_score": risk_report.overall_risk_score,
        "total_risks": len(risk_report.risks),
        "severity_counts": severity_counts,
        "risk_types": [r.type for r in risk_report.risks],
        "top_risks": [
            {
                "type": r.type,
                "severity": r.severity.value if hasattr(r.severity, "value") else r.severity,
                "likelihood": r.likelihood,
                "mitigation": r.mitigation,
            }
            for r in sorted(
                risk_report.risks,
                key=lambda x: (
                    {"high": 2, "medium": 1, "low": 0}.get(
                        x.severity.value if hasattr(x.severity, "value") else x.severity, 0
                    ),
                    x.likelihood,
                ),
                reverse=True,
            )[:3]
        ],
    }


def _build_simulation_summary(sim: SimulationResult) -> Dict[str, Any]:
    """Compact summary of the simulation result for the output envelope."""
    return {
        "power_status": sim.power_status,
        "gpu_bottleneck": sim.gpu_bottleneck,
        "thermal_status": sim.thermal_status,
        "total_power_w": sim.total_power_w,
        "power_utilisation_pct": round(sim.power_utilisation_pct, 1),
        "total_gpus": sim.total_gpus,
        "cameras_per_gpu": round(sim.cameras_per_gpu, 1) if sim.cameras_per_gpu >= 0 else None,
        "thermal_density_w_per_server": round(sim.thermal_density_w_per_server, 1),
        "warning_count": len(sim.warnings),
    }


def _build_final_decision(
    system_status: str,
    deployment_ready: bool,
    blockers: List[str],
    suggestions: List[str],
    solution: Solution,
) -> str:
    """
    Compose a concise, deterministic final decision statement.
    """
    use_case = solution.requirement.use_case or "the proposed infrastructure"
    device_count = solution.requirement.device_count
    cost = solution.estimated_cost

    if system_status == "critical":
        return (
            "DEPLOYMENT BLOCKED: {use_case} ({devices} devices, ${cost:,.0f}) "
            "cannot proceed. {blocker_count} critical blocker(s) must be resolved: "
            "{blockers}. Address all blockers before re-evaluation.".format(
                use_case=use_case,
                devices=device_count,
                cost=cost,
                blocker_count=len(blockers),
                blockers="; ".join(b.split(": ", 1)[-1] for b in blockers[:2]),
            )
        )
    elif system_status == "degraded":
        return (
            "CONDITIONAL APPROVAL: {use_case} ({devices} devices, ${cost:,.0f}) "
            "may proceed with caution. {suggestion_count} optimization(s) recommended "
            "to improve reliability before production deployment.".format(
                use_case=use_case,
                devices=device_count,
                cost=cost,
                suggestion_count=len(suggestions),
            )
        )
    else:
        return (
            "APPROVED FOR DEPLOYMENT: {use_case} ({devices} devices, ${cost:,.0f}) "
            "meets all engineering requirements. System is healthy with no critical "
            "risks or simulation failures detected.".format(
                use_case=use_case,
                devices=device_count,
                cost=cost,
            )
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_system_assessment(
    solution: Union[Solution, Dict[str, Any]],
    risk_report: Union[RiskReport, Dict[str, Any]],
    simulation_result: Union[SimulationResult, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Generate a unified enterprise intelligence assessment.

    Combines the Risk Intelligence Agent output and the Infrastructure
    Simulation Engine output into a single structured decision object.

    Parameters
    ----------
    solution : Solution | dict
        Canonical Solution or a dict that can be auto-converted.
        Validated through schema_guard before processing.
    risk_report : RiskReport | dict
        Output of risk_agent.analyze_risks() or a RiskReport instance.
    simulation_result : SimulationResult | dict
        Output of run_infrastructure_simulation() or a SimulationResult instance.

    Returns
    -------
    Dict[str, Any]
        Unified assessment with the following keys::

            {
                "system_status":          "healthy|degraded|critical",
                "deployment_readiness":   bool,
                "key_blockers":           List[str],
                "optimization_suggestions": List[str],
                "risk_summary":           Dict,
                "simulation_summary":     Dict,
                "final_decision":         str
            }

    Raises
    ------
    ValueError
        If the Solution input fails schema_guard validation.
    TypeError
        If risk_report or simulation_result cannot be normalised.
    """
    logger.info(
        "Fusion engine starting | solution_type=%s | risk_type=%s | sim_type=%s",
        type(solution).__name__,
        type(risk_report).__name__,
        type(simulation_result).__name__,
    )

    # ------------------------------------------------------------------
    # Step 1: Normalise all inputs
    # ------------------------------------------------------------------
    validated_solution = _normalise_solution(solution)
    validated_risk = _normalise_risk_report(risk_report)
    validated_sim = _normalise_simulation_result(simulation_result)

    logger.info(
        "All inputs normalised | risks=%d | overall_risk_score=%.3f | "
        "power=%s | gpu_bottleneck=%s | thermal=%s",
        len(validated_risk.risks),
        validated_risk.overall_risk_score,
        validated_sim.power_status,
        validated_sim.gpu_bottleneck,
        validated_sim.thermal_status,
    )

    # ------------------------------------------------------------------
    # Step 2: Determine system status
    # ------------------------------------------------------------------
    system_status, triggered_rules = _determine_system_status(
        validated_risk.risks, validated_sim
    )

    logger.info(
        "System status determined | status=%s | triggered_rules=%s",
        system_status, triggered_rules,
    )

    # ------------------------------------------------------------------
    # Step 3: Deployment readiness
    # ------------------------------------------------------------------
    deployment_ready: bool = system_status != "critical"

    logger.info(
        "Deployment readiness | ready=%s | system_status=%s",
        deployment_ready, system_status,
    )

    # ------------------------------------------------------------------
    # Step 4: Key blockers
    # ------------------------------------------------------------------
    key_blockers = _build_key_blockers(validated_risk.risks, validated_sim)

    # ------------------------------------------------------------------
    # Step 5: Optimization suggestions
    # ------------------------------------------------------------------
    optimization_suggestions = _build_optimization_suggestions(
        validated_risk.risks, validated_sim, validated_solution
    )

    logger.info(
        "Optimization suggestions generated | count=%d",
        len(optimization_suggestions),
    )

    # ------------------------------------------------------------------
    # Step 6: Summaries
    # ------------------------------------------------------------------
    risk_summary = _build_risk_summary(validated_risk)
    simulation_summary = _build_simulation_summary(validated_sim)

    # ------------------------------------------------------------------
    # Step 7: Final decision statement
    # ------------------------------------------------------------------
    final_decision = _build_final_decision(
        system_status,
        deployment_ready,
        key_blockers,
        optimization_suggestions,
        validated_solution,
    )

    logger.info("Final decision | %s", final_decision[:120])

    # ------------------------------------------------------------------
    # Step 8: Assemble output
    # ------------------------------------------------------------------
    assessment: Dict[str, Any] = {
        "system_status": system_status,
        "deployment_readiness": deployment_ready,
        "key_blockers": key_blockers,
        "optimization_suggestions": optimization_suggestions,
        "risk_summary": risk_summary,
        "simulation_summary": simulation_summary,
        "final_decision": final_decision,
    }

    logger.info(
        "Fusion engine complete | system_status=%s | deployment_ready=%s | "
        "blockers=%d | suggestions=%d",
        system_status,
        deployment_ready,
        len(key_blockers),
        len(optimization_suggestions),
    )

    return assessment
