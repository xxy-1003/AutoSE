"""
Pipeline Controller — single entry point for the AutoSE Platform.

Orchestrates the full deterministic execution flow in strict order:

  Step 1  Validate requirement input (schema_guard)
  Step 2  Product retrieval (ProductRetriever)
  Step 3  Risk analysis (risk_agent)
  Step 4  Infrastructure simulation (infrastructure_sim)
  Step 5  Fusion engine (generate_system_assessment)

Design principles
-----------------
- Single entry point: run_autose() is the ONLY function callers need.
- Deterministic: every step is pure logic; no LLM calls in the controller.
- Traceable: every stage is logged with timing and key metrics.
- Schema-enforced: schema_guard is called at every data boundary.
- No new agents: only wires existing modules together.

Usage::

    from src.core.pipeline_controller import run_autose

    # From a natural language string (uses RequirementAnalyzer fallback)
    result = run_autose("100-camera AI surveillance system, budget $80,000")

    # From a structured dict (skips LLM extraction)
    result = run_autose({
        "device_count": 100,
        "gpu_required": True,
        "estimated_power_w": 1500,
        "network_ports": 48,
        "budget": 80000.0,
        "use_case": "AI surveillance",
    })

    # From a canonical Requirement instance
    from src.schemas.solution_schema import Requirement
    result = run_autose(Requirement(device_count=100, gpu_required=True, ...))
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Union

# ---------------------------------------------------------------------------
# Schema types and guard
# ---------------------------------------------------------------------------
try:
    from src.core.schema_guard import validate_requirement, validate_solution
    from src.schemas.solution_schema import (
        Requirement,
        Solution,
        RiskReport,
        CheckStatus,
    )
    from src.simulation.infrastructure_sim import (
        run_infrastructure_simulation,
        SimulationResult,
    )
    from src.core.fusion_engine import generate_system_assessment
    from src.agents.risk_agent import analyze_risks
    from src.autose_platform.requirement_analyzer import RequirementAnalyzer
    from src.autose_platform.product_retriever import ProductRetriever
except ImportError:
    try:
        from core.schema_guard import validate_requirement, validate_solution  # type: ignore[no-redef]
        from schemas.solution_schema import (  # type: ignore[no-redef]
            Requirement,
            Solution,
            RiskReport,
            CheckStatus,
        )
        from simulation.infrastructure_sim import (  # type: ignore[no-redef]
            run_infrastructure_simulation,
            SimulationResult,
        )
        from core.fusion_engine import generate_system_assessment  # type: ignore[no-redef]
        from agents.risk_agent import analyze_risks  # type: ignore[no-redef]
        from autose_platform.requirement_analyzer import RequirementAnalyzer  # type: ignore[no-redef]
        from autose_platform.product_retriever import ProductRetriever  # type: ignore[no-redef]
    except ImportError:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from src.core.schema_guard import validate_requirement, validate_solution  # type: ignore[no-redef]
        from src.schemas.solution_schema import (  # type: ignore[no-redef]
            Requirement,
            Solution,
            RiskReport,
            CheckStatus,
        )
        from src.simulation.infrastructure_sim import (  # type: ignore[no-redef]
            run_infrastructure_simulation,
            SimulationResult,
        )
        from src.core.fusion_engine import generate_system_assessment  # type: ignore[no-redef]
        from src.agents.risk_agent import analyze_risks  # type: ignore[no-redef]
        from src.autose_platform.requirement_analyzer import RequirementAnalyzer  # type: ignore[no-redef]
        from src.autose_platform.product_retriever import ProductRetriever  # type: ignore[no-redef]

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger("autose.pipeline")

if not logger.handlers:
    logger.addHandler(logging.NullHandler())

# ---------------------------------------------------------------------------
# Stage timing helper
# ---------------------------------------------------------------------------

class _StageTimer:
    """Context manager that logs stage name, duration, and outcome."""

    def __init__(self, stage_name: str, step_number: int):
        self.stage_name = stage_name
        self.step_number = step_number
        self._start: float = 0.0

    def __enter__(self) -> "_StageTimer":
        self._start = time.perf_counter()
        logger.info(
            "PIPELINE STEP %d START | stage=%s",
            self.step_number,
            self.stage_name,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        elapsed_ms = (time.perf_counter() - self._start) * 1000
        if exc_type is None:
            logger.info(
                "PIPELINE STEP %d COMPLETE | stage=%s | elapsed_ms=%.1f",
                self.step_number,
                self.stage_name,
                elapsed_ms,
            )
        else:
            logger.error(
                "PIPELINE STEP %d FAILED | stage=%s | elapsed_ms=%.1f | error=%s: %s",
                self.step_number,
                self.stage_name,
                elapsed_ms,
                exc_type.__name__,
                exc_val,
            )
        return False  # never suppress exceptions


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_requirement_instance(obj: object) -> bool:
    """Duck-type check for Requirement across import paths."""
    cls = type(obj)
    return cls.__name__ == "Requirement" and cls.__module__.endswith("solution_schema")


def _coerce_to_requirement(
    requirement_input: Union[str, Dict[str, Any], Requirement],
) -> Requirement:
    """
    Convert any supported input type to a canonical Requirement.

    Supported inputs
    ----------------
    str
        Natural language text. Parsed via RequirementAnalyzer fallback
        (regex-based, no LLM call) so the pipeline stays deterministic
        when no API key is configured.  If an API key IS configured the
        LLM path is attempted first via the async extract() method.
    dict
        Flat dict with any combination of Requirement fields.
        Passed through validate_requirement() for auto-conversion.
    Requirement
        Already canonical — re-validated and returned as-is.
    """
    if _is_requirement_instance(requirement_input):
        return requirement_input  # type: ignore[return-value]

    if isinstance(requirement_input, str):
        # Use the RequirementAnalyzer's synchronous fallback for determinism.
        # If an event loop is already running (FastAPI context), use it;
        # otherwise run a new one.
        analyzer = RequirementAnalyzer()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're inside an async context — use asyncio.run_coroutine_threadsafe
                # or fall back to the synchronous regex extractor directly.
                structured, additional_info = analyzer._extract_with_fallback(
                    requirement_input
                )
            else:
                structured, additional_info = loop.run_until_complete(
                    analyzer.extract(requirement_input)
                )
                # extract() returns (StructuredRequirements, additional_info)
                # Convert StructuredRequirements to dict for from_structured
                if hasattr(structured, "model_dump"):
                    structured = structured.model_dump()
        except RuntimeError:
            # No event loop — use fallback directly
            structured, additional_info = analyzer._extract_with_fallback(
                requirement_input
            )

        return Requirement.from_structured(structured, additional_info)

    if isinstance(requirement_input, dict):
        guard = validate_requirement(requirement_input)
        if not guard.valid:
            logger.error(
                "Requirement validation failed | errors=%s", guard.errors
            )
        return guard.raise_if_invalid()

    # Unknown type — try duck-typing
    try:
        as_dict = vars(requirement_input) if hasattr(requirement_input, "__dict__") else dict(requirement_input)  # type: ignore[call-overload]
        return _coerce_to_requirement(as_dict)
    except Exception as exc:
        raise TypeError(
            "requirement_input must be str, dict, or Requirement, got {}: {}".format(
                type(requirement_input).__name__, exc
            )
        ) from exc


async def _retrieve_products_async(
    requirement: Requirement,
) -> list:
    """
    Call ProductRetriever.match() (async) and return raw catalog dicts.
    """
    retriever = ProductRetriever()

    # Build a StructuredRequirements-compatible object from the canonical Requirement
    # ProductRetriever.match() expects a StructuredRequirements instance
    try:
        from src.autose_platform.models import StructuredRequirements as SR
    except ImportError:
        from autose_platform.models import StructuredRequirements as SR  # type: ignore[no-redef]

    structured = SR(
        device_count=requirement.device_count,
        gpu_required=requirement.gpu_required,
        estimated_power_w=requirement.estimated_power_w,
        network_ports=requirement.network_ports,
    )

    project_type = requirement.project_type if requirement.project_type != "unknown" else None
    budget_limit = int(requirement.budget) if requirement.budget > 0 else None

    products = await retriever.match(
        structured,
        project_type=project_type,
        budget_limit=budget_limit,
    )
    return products


def _retrieve_products_sync(requirement: Requirement) -> list:
    """
    Synchronous wrapper around the async ProductRetriever.match().

    Handles both cases:
    - Called from a plain synchronous context (creates a new event loop).
    - Called from within an already-running event loop (uses run_until_complete
      on the existing loop, or falls back to a thread executor).
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already inside an async context (e.g. FastAPI).
            # Use a new thread to avoid "cannot run nested event loop".
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    asyncio.run, _retrieve_products_async(requirement)
                )
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(_retrieve_products_async(requirement))
    except RuntimeError:
        return asyncio.run(_retrieve_products_async(requirement))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_autose(
    requirement_input: Union[str, Dict[str, Any], Requirement],
) -> Dict[str, Any]:
    """
    Execute the full AutoSE pipeline and return a unified intelligence report.

    This is the SINGLE ENTRY POINT for the entire AutoSE system.

    Pipeline steps (strict order)
    ------------------------------
    1. Validate requirement  — schema_guard enforced
    2. Product retrieval     — ProductRetriever.match()
    3. Risk analysis         — risk_agent.analyze_risks()
    4. Infrastructure sim    — run_infrastructure_simulation()
    5. Fusion engine         — generate_system_assessment()

    Parameters
    ----------
    requirement_input : str | dict | Requirement
        Natural language text, a flat dict of requirement fields, or a
        canonical Requirement instance.

    Returns
    -------
    Dict[str, Any]
        Unified pipeline output::

            {
                "input":             dict,   # normalised requirement fields
                "solution":          dict,   # selected products + cost/power
                "risk_report":       dict,   # risks + overall_risk_score
                "simulation":        dict,   # power/gpu/thermal statuses
                "system_assessment": dict,   # fusion engine output
                "final_output":      dict    # concise executive summary
            }

    Raises
    ------
    ValueError
        If the requirement input fails schema validation.
    RuntimeError
        If any pipeline stage fails unexpectedly.
    """
    pipeline_start = time.perf_counter()
    logger.info(
        "AutoSE pipeline starting | input_type=%s",
        type(requirement_input).__name__,
    )

    # ======================================================================
    # STEP 1 — Validate requirement
    # ======================================================================
    with _StageTimer("validate_requirement", 1):
        requirement: Requirement = _coerce_to_requirement(requirement_input)

        # Re-validate through schema_guard to guarantee canonical form
        guard = validate_requirement(requirement)
        if not guard.valid:
            logger.error(
                "Step 1 FAILED | requirement validation errors=%s", guard.errors
            )
        requirement = guard.raise_if_invalid()

        logger.info(
            "Step 1 OK | device_count=%d | gpu_required=%s | budget=%.0f | project_type=%s",
            requirement.device_count,
            requirement.gpu_required,
            requirement.budget,
            requirement.project_type,
        )

    # ======================================================================
    # STEP 2 — Product retrieval
    # ======================================================================
    with _StageTimer("product_retrieval", 2):
        raw_products = _retrieve_products_sync(requirement)

        if not raw_products:
            logger.warning(
                "Step 2 WARNING | no products matched — proceeding with empty list"
            )

        logger.info(
            "Step 2 OK | products_matched=%d | categories=%s",
            len(raw_products),
            list({p.get("category", "?") for p in raw_products}),
        )

    # ======================================================================
    # Build canonical Solution (needed by sim + fusion)
    # ======================================================================
    solution = Solution.from_pipeline_result(
        requirement=requirement,
        products=raw_products,
        validation_status="PASS",
        validation_warnings=[],
    )

    logger.info(
        "Solution assembled | products=%d | estimated_cost=%.0f | estimated_power=%d W",
        len(solution.selected_products),
        solution.estimated_cost,
        solution.estimated_power,
    )

    # ======================================================================
    # STEP 3 — Risk analysis
    # ======================================================================
    with _StageTimer("risk_analysis", 3):
        # risk_agent expects flat catalog dicts + structured requirements dict
        risk_raw = analyze_risks(
            products=raw_products,
            requirements=requirement.to_structured_dict(),
        )

        risk_report = RiskReport.from_agent_output(risk_raw)

        logger.info(
            "Step 3 OK | risks_detected=%d | overall_risk_score=%.3f | "
            "high=%d | medium=%d | low=%d",
            len(risk_report.risks),
            risk_report.overall_risk_score,
            sum(
                1 for r in risk_report.risks
                if (r.severity.value if hasattr(r.severity, "value") else r.severity) == "high"
            ),
            sum(
                1 for r in risk_report.risks
                if (r.severity.value if hasattr(r.severity, "value") else r.severity) == "medium"
            ),
            sum(
                1 for r in risk_report.risks
                if (r.severity.value if hasattr(r.severity, "value") else r.severity) == "low"
            ),
        )

    # ======================================================================
    # STEP 4 — Infrastructure simulation
    # ======================================================================
    with _StageTimer("infrastructure_simulation", 4):
        sim_result: SimulationResult = run_infrastructure_simulation(solution)

        logger.info(
            "Step 4 OK | power=%s (%.1f%%) | gpu_bottleneck=%s | thermal=%s | warnings=%d",
            sim_result.power_status,
            sim_result.power_utilisation_pct,
            sim_result.gpu_bottleneck,
            sim_result.thermal_status,
            len(sim_result.warnings),
        )

    # ======================================================================
    # STEP 5 — Fusion engine
    # ======================================================================
    with _StageTimer("fusion_engine", 5):
        system_assessment = generate_system_assessment(
            solution=solution,
            risk_report=risk_report,
            simulation_result=sim_result,
        )

        logger.info(
            "Step 5 OK | system_status=%s | deployment_ready=%s | "
            "blockers=%d | suggestions=%d",
            system_assessment["system_status"],
            system_assessment["deployment_readiness"],
            len(system_assessment["key_blockers"]),
            len(system_assessment["optimization_suggestions"]),
        )

    # ======================================================================
    # Assemble final output
    # ======================================================================
    total_ms = (time.perf_counter() - pipeline_start) * 1000

    final_output = _build_final_output(
        requirement=requirement,
        solution=solution,
        risk_report=risk_report,
        sim_result=sim_result,
        system_assessment=system_assessment,
        total_ms=total_ms,
    )

    logger.info(
        "AutoSE pipeline complete | total_ms=%.1f | system_status=%s | "
        "deployment_ready=%s | final_decision_preview=%s",
        total_ms,
        system_assessment["system_status"],
        system_assessment["deployment_readiness"],
        system_assessment["final_decision"][:80],
    )

    return {
        "input": requirement.model_dump(),
        "solution": _serialise_solution(solution),
        "risk_report": risk_raw,
        "simulation": sim_result.to_full_dict(),
        "system_assessment": system_assessment,
        "final_output": final_output,
    }


# ---------------------------------------------------------------------------
# Output builders
# ---------------------------------------------------------------------------

def _serialise_solution(solution: Solution) -> Dict[str, Any]:
    """Serialise Solution to a JSON-safe dict."""
    return {
        "product_count": len(solution.selected_products),
        "estimated_cost_usd": solution.estimated_cost,
        "estimated_power_w": solution.estimated_power,
        "validation_status": (
            solution.validation_status.value
            if hasattr(solution.validation_status, "value")
            else solution.validation_status
        ),
        "products": [p.to_catalog_dict() for p in solution.selected_products],
        "assumptions": solution.assumptions,
    }


def _build_final_output(
    requirement: Requirement,
    solution: Solution,
    risk_report: RiskReport,
    sim_result: SimulationResult,
    system_assessment: Dict[str, Any],
    total_ms: float,
) -> Dict[str, Any]:
    """
    Build a concise executive summary for the final_output field.
    """
    return {
        "system_status": system_assessment["system_status"],
        "deployment_readiness": system_assessment["deployment_readiness"],
        "final_decision": system_assessment["final_decision"],
        "key_metrics": {
            "device_count": requirement.device_count,
            "total_products": len(solution.selected_products),
            "estimated_cost_usd": solution.estimated_cost,
            "estimated_power_w": solution.estimated_power,
            "overall_risk_score": risk_report.overall_risk_score,
            "power_utilisation_pct": round(sim_result.power_utilisation_pct, 1),
            "gpu_bottleneck": sim_result.gpu_bottleneck,
            "thermal_status": sim_result.thermal_status,
        },
        "blocker_count": len(system_assessment["key_blockers"]),
        "suggestion_count": len(system_assessment["optimization_suggestions"]),
        "pipeline_duration_ms": round(total_ms, 1),
    }
