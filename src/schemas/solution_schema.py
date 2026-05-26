"""
Canonical data contract for the AutoSE Platform.

All future modules MUST import and use these schemas instead of defining
their own ad-hoc dicts or local Pydantic models.

Compatibility notes
-------------------
- ``Product`` field names align with the existing catalog dicts used by
  ``ProductRetriever`` (``power_w``, ``gpu_count`` / ``gpu``, ``ports`` /
  ``port_count``, ``capacity_w``, ``max_cameras``).  Aliases are provided
  so both the old snake-case keys and the canonical names are accepted.
- ``Requirement`` extends the fields already present in
  ``autose_platform.models.StructuredRequirements`` with the higher-level
  business fields (``use_case``, ``users``, ``budget``, ``constraints``).
- ``Solution`` is the single envelope that travels between agents.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class SeverityLevel(str, Enum):
    """Risk severity levels used by the Risk Intelligence Agent."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CheckStatus(str, Enum):
    """Validation check outcomes used by the Validation Layer."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


# ---------------------------------------------------------------------------
# CapacityMetrics — generic product capability bag
# ---------------------------------------------------------------------------


class CapacityMetrics(BaseModel):
    """
    Generic capacity / capability metrics for a product.

    All fields are optional so that the same model covers servers, switches,
    UPS units, sensors, and any future product category without requiring
    schema changes.
    """

    # Compute
    gpu_count: int = Field(
        default=0,
        ge=0,
        description="Number of discrete GPUs in this product.",
        alias="gpu",
    )
    max_cameras: int = Field(
        default=0,
        ge=0,
        description="Maximum IP cameras / AI streams this product can handle.",
    )

    # Power
    capacity_w: int = Field(
        default=0,
        ge=0,
        description="Power backup capacity in watts (UPS / PDU products).",
    )

    # Network
    port_count: int = Field(
        default=0,
        ge=0,
        description="Number of network ports (switches / routers).",
        alias="ports",
    )

    # Storage
    storage_tb: float = Field(
        default=0.0,
        ge=0.0,
        description="Usable storage capacity in terabytes.",
    )

    # Extensible: any extra vendor-specific metrics
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Catch-all dict for vendor-specific or category-specific metrics "
            "not covered by the fields above (e.g. PoE budget, VRAM, IOPS)."
        ),
    )

    model_config = {
        "populate_by_name": True,  # accept both field name and alias
        "json_schema_extra": {
            "example": {
                "gpu_count": 8,
                "max_cameras": 120,
                "capacity_w": 0,
                "port_count": 0,
                "storage_tb": 0.0,
                "extra": {"vram_gb": 80},
            }
        },
    }


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------


class Product(BaseModel):
    """
    Canonical product representation.

    Covers every product category in the AutoSE catalog (servers, switches,
    UPS units, sensors, smart-home devices, storage, etc.).
    """

    # Identity
    id: Optional[str] = Field(
        default=None,
        description="Unique catalog identifier (e.g. 'server_x2').",
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Human-readable product name.",
    )
    category: str = Field(
        ...,
        min_length=1,
        description=(
            "Product category: 'server' | 'network' | 'power' | 'security' | "
            "'storage' | 'sensor' | 'smart_home' | …"
        ),
    )

    # Power
    power_w: int = Field(
        default=0,
        ge=0,
        description="Idle / typical power draw of this product in watts.",
    )

    # Cost
    price: int = Field(
        default=0,
        ge=0,
        description="Unit price in USD.",
    )

    # Capacity metrics (compute, network, power backup, storage, …)
    capacity: CapacityMetrics = Field(
        default_factory=CapacityMetrics,
        description="All capacity / capability metrics for this product.",
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "server_x2",
                "name": "AI Server X2",
                "category": "server",
                "power_w": 1500,
                "price": 28000,
                "capacity": {
                    "gpu_count": 8,
                    "max_cameras": 120,
                    "capacity_w": 0,
                    "port_count": 0,
                    "storage_tb": 0.0,
                    "extra": {},
                },
            }
        },
    }

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_catalog_dict(cls, d: Dict[str, Any]) -> "Product":
        """
        Build a ``Product`` from a raw catalog dictionary.

        Handles the dual key names used in the existing catalog
        (``gpu`` / ``gpu_count``, ``ports`` / ``port_count``).
        """
        capacity = CapacityMetrics(
            gpu=d.get("gpu", d.get("gpu_count", 0)),
            max_cameras=d.get("max_cameras", 0),
            capacity_w=d.get("capacity_w", 0),
            ports=d.get("ports", d.get("port_count", 0)),
            storage_tb=d.get("storage_tb", 0.0),
            extra={
                k: v
                for k, v in d.items()
                if k
                not in {
                    "id", "name", "category", "power_w", "price",
                    "gpu", "gpu_count", "max_cameras", "capacity_w",
                    "ports", "port_count", "storage_tb",
                }
            },
        )
        return cls(
            id=d.get("id"),
            name=d["name"],
            category=d.get("category", "unknown"),
            power_w=d.get("power_w", 0),
            price=d.get("price", 0),
            capacity=capacity,
        )

    def to_catalog_dict(self) -> Dict[str, Any]:
        """
        Serialise back to the flat dict format expected by existing agents
        (``ValidationLayer``, ``ProposalGenerator``, ``risk_agent``, etc.).
        """
        d: Dict[str, Any] = {
            "name": self.name,
            "category": self.category,
            "power_w": self.power_w,
            "price": self.price,
            "gpu": self.capacity.gpu_count,
            "gpu_count": self.capacity.gpu_count,
            "max_cameras": self.capacity.max_cameras,
            "capacity_w": self.capacity.capacity_w,
            "ports": self.capacity.port_count,
            "port_count": self.capacity.port_count,
            "storage_tb": self.capacity.storage_tb,
        }
        if self.id is not None:
            d["id"] = self.id
        d.update(self.capacity.extra)
        return d


# ---------------------------------------------------------------------------
# Requirement
# ---------------------------------------------------------------------------


class Requirement(BaseModel):
    """
    Canonical requirement model.

    Combines the high-level business context (use_case, users, budget,
    constraints) with the low-level technical fields already extracted by
    the Requirement Analyzer Agent (device_count, gpu_required, etc.).
    """

    # --- Business / high-level fields ---

    use_case: str = Field(
        default="",
        description=(
            "Short description of the deployment scenario, e.g. "
            "'AI surveillance for 50-employee smart office'."
        ),
    )
    users: int = Field(
        default=0,
        ge=0,
        description="Number of end-users or employees the solution must serve.",
    )
    budget: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "Maximum total budget in USD. "
            "0 means no explicit budget constraint."
        ),
    )
    constraints: List[str] = Field(
        default_factory=list,
        description=(
            "Free-text list of hard constraints, e.g. "
            "['must support PoE', 'rack-mount only', 'NDAA compliant']."
        ),
    )

    # --- Technical / low-level fields (from StructuredRequirements) ---

    device_count: int = Field(
        default=1,
        ge=1,
        description="Number of cameras / IoT devices to be connected.",
    )
    gpu_required: bool = Field(
        default=False,
        description="Whether GPU-accelerated AI inference is required.",
    )
    estimated_power_w: int = Field(
        default=0,
        ge=0,
        description=(
            "Estimated additional power draw (W) not covered by the product list, "
            "e.g. cabling, patch panels, ancillary devices."
        ),
    )
    network_ports: int = Field(
        default=0,
        ge=0,
        description="Minimum number of network switch ports required.",
    )

    # --- Optional enrichment fields ---

    project_type: str = Field(
        default="unknown",
        description=(
            "Detected project category: 'security_system' | 'smart_home' | "
            "'office_network' | 'data_center' | 'retail_surveillance' | 'unknown'."
        ),
    )
    camera_count: int = Field(
        default=0,
        ge=0,
        description="Explicit camera count when different from device_count.",
    )
    room_count: int = Field(
        default=0,
        ge=0,
        description="Number of rooms / zones (relevant for smart-home projects).",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "use_case": "AI surveillance for 50-employee smart office",
                "users": 50,
                "budget": 80000.0,
                "constraints": ["rack-mount only", "NDAA compliant"],
                "device_count": 30,
                "gpu_required": True,
                "estimated_power_w": 500,
                "network_ports": 48,
                "project_type": "security_system",
                "camera_count": 30,
                "room_count": 0,
            }
        }
    }

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_structured(cls, structured: Any, additional_info: Optional[Dict[str, Any]] = None) -> "Requirement":
        """
        Build a ``Requirement`` from a ``StructuredRequirements`` Pydantic model
        and the ``additional_info`` dict returned by the Requirement Analyzer.
        """
        if hasattr(structured, "model_dump"):
            base = structured.model_dump()
        elif hasattr(structured, "dict"):
            base = structured.dict()
        else:
            base = dict(structured)

        extra = additional_info or {}
        return cls(
            use_case=extra.get("use_case", ""),
            users=extra.get("user_count", 0),
            budget=float(extra.get("budget_limit", 0)),
            constraints=extra.get("constraints", []),
            device_count=base.get("device_count", 1),
            gpu_required=base.get("gpu_required", False),
            estimated_power_w=base.get("estimated_power_w", 0),
            network_ports=base.get("network_ports", 0),
            project_type=extra.get("project_type", "unknown"),
            camera_count=extra.get("camera_count", 0),
            room_count=extra.get("room_count", 0),
        )

    def to_structured_dict(self) -> Dict[str, Any]:
        """
        Return the subset of fields that map to ``StructuredRequirements``
        (for backward-compatibility with existing agents).
        """
        return {
            "device_count": self.device_count,
            "gpu_required": self.gpu_required,
            "estimated_power_w": self.estimated_power_w,
            "network_ports": self.network_ports,
        }

    def to_additional_info_dict(self) -> Dict[str, Any]:
        """
        Return the subset of fields that map to the ``additional_info`` dict
        used by ``ProductRetriever`` and ``ProposalGenerator``.
        """
        return {
            "project_type": self.project_type,
            "camera_count": self.camera_count,
            "room_count": self.room_count,
            "user_count": self.users,
            "budget_limit": int(self.budget),
        }


# ---------------------------------------------------------------------------
# Solution
# ---------------------------------------------------------------------------


class Solution(BaseModel):
    """
    Canonical solution envelope.

    Carries the full context of a proposed infrastructure solution as it
    flows through the agent pipeline:

        Requirement Analyzer
            → Product Retriever  (populates selected_products)
            → Validation Layer   (populates validation_status / warnings)
            → Risk Agent         (populates risk_report)
            → Proposal Generator (populates proposal_markdown / proposal_json)
    """

    # --- Core fields ---

    requirement: Requirement = Field(
        ...,
        description="The canonical requirement this solution addresses.",
    )
    selected_products: List[Product] = Field(
        default_factory=list,
        description="Ordered list of products chosen for this solution.",
    )

    # --- Derived / computed fields ---

    estimated_power: int = Field(
        default=0,
        ge=0,
        description=(
            "Total estimated power draw in watts "
            "(sum of product power_w + requirement.estimated_power_w)."
        ),
    )
    estimated_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Total estimated cost in USD (sum of product prices).",
    )

    # --- Reasoning / narrative ---

    assumptions: List[str] = Field(
        default_factory=list,
        description=(
            "List of assumptions made during solution design, e.g. "
            "['Single-site deployment', 'Existing fibre backbone available']."
        ),
    )

    # --- Validation outcomes ---

    validation_status: CheckStatus = Field(
        default=CheckStatus.PASS,
        description="Overall validation outcome for this solution.",
    )
    validation_warnings: List[str] = Field(
        default_factory=list,
        description="Human-readable validation warnings (empty when status is PASS).",
    )

    # --- Risk report (populated by Risk Agent) ---

    risk_report: Optional["RiskReport"] = Field(
        default=None,
        description="Structured risk report produced by the Risk Intelligence Agent.",
    )

    # --- Proposal output (populated by Proposal Generator) ---

    proposal_markdown: str = Field(
        default="",
        description="Markdown-formatted proposal document.",
    )
    proposal_json: Dict[str, Any] = Field(
        default_factory=dict,
        description="Machine-readable proposal with full reasoning structure.",
    )

    # --- Metadata ---

    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO-8601 UTC timestamp when this solution was created.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Conversation session ID (for multi-turn interactions).",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "requirement": {
                    "use_case": "AI surveillance for 50-employee smart office",
                    "users": 50,
                    "budget": 80000.0,
                    "constraints": [],
                    "device_count": 30,
                    "gpu_required": True,
                    "estimated_power_w": 500,
                    "network_ports": 48,
                    "project_type": "security_system",
                },
                "selected_products": [],
                "estimated_power": 2000,
                "estimated_cost": 31500.0,
                "assumptions": ["Single-site deployment"],
                "validation_status": "PASS",
                "validation_warnings": [],
                "risk_report": None,
                "proposal_markdown": "",
                "proposal_json": {},
                "created_at": "2026-05-27T00:00:00Z",
                "session_id": None,
            }
        }
    }

    # ------------------------------------------------------------------
    # Auto-compute derived fields
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _compute_derived(self) -> "Solution":
        """Recompute estimated_power and estimated_cost from selected_products."""
        if self.selected_products:
            self.estimated_power = (
                sum(p.power_w for p in self.selected_products)
                + self.requirement.estimated_power_w
            )
            self.estimated_cost = float(sum(p.price for p in self.selected_products))
        return self

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def product_dicts(self) -> List[Dict[str, Any]]:
        """
        Return selected_products as a list of flat catalog dicts.

        Use this when passing products to existing agents that expect the
        legacy dict format (ValidationLayer, ProposalGenerator, risk_agent).
        """
        return [p.to_catalog_dict() for p in self.selected_products]

    @classmethod
    def from_pipeline_result(
        cls,
        requirement: Requirement,
        products: List[Dict[str, Any]],
        validation_status: str = "PASS",
        validation_warnings: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> "Solution":
        """
        Convenience constructor that wraps the output of the existing pipeline
        (list of catalog dicts + validation strings) into a canonical Solution.
        """
        canonical_products = [Product.from_catalog_dict(d) for d in products]
        return cls(
            requirement=requirement,
            selected_products=canonical_products,
            validation_status=CheckStatus(validation_status),
            validation_warnings=validation_warnings or [],
            assumptions=assumptions or [],
            session_id=session_id,
        )


# ---------------------------------------------------------------------------
# RiskEntry & RiskReport  (mirrors risk_agent output format)
# ---------------------------------------------------------------------------


class RiskEntry(BaseModel):
    """A single identified risk within a risk report."""

    type: str = Field(
        ...,
        description=(
            "Machine-readable risk type: 'power_overload' | 'gpu_bottleneck' | "
            "'thermal_risk' | 'network_saturation' | …"
        ),
    )
    severity: SeverityLevel = Field(
        ...,
        description="Severity classification: low | medium | high.",
    )
    likelihood: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated probability that this risk materialises (0.0 – 1.0).",
    )
    description: str = Field(
        ...,
        description="Human-readable explanation of the risk.",
    )
    mitigation: str = Field(
        ...,
        description="Recommended action(s) to reduce or eliminate the risk.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "power_overload",
                "severity": "high",
                "likelihood": 0.85,
                "description": "Total system power exceeds UPS capacity.",
                "mitigation": "Add a second UPS unit or upgrade to higher capacity.",
            }
        }
    }

    @field_validator("likelihood")
    @classmethod
    def _round_likelihood(cls, v: float) -> float:
        return round(v, 3)


class RiskReport(BaseModel):
    """
    Structured risk report produced by the Risk Intelligence Agent.

    Mirrors the JSON output format of ``src/agents/risk_agent.py``.
    """

    risks: List[RiskEntry] = Field(
        default_factory=list,
        description="List of identified risks, ordered by severity (high → low).",
    )
    overall_risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Aggregate risk score in [0.0, 1.0]. "
            "0.0 = no risks detected; 1.0 = critical risk level."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "risks": [
                    {
                        "type": "gpu_bottleneck",
                        "severity": "medium",
                        "likelihood": 0.62,
                        "description": "30 cameras share 4 GPUs (7 cameras/GPU).",
                        "mitigation": "Add one more GPU-enabled server.",
                    }
                ],
                "overall_risk_score": 0.435,
            }
        }
    }

    @field_validator("overall_risk_score")
    @classmethod
    def _round_score(cls, v: float) -> float:
        return round(v, 3)

    @classmethod
    def from_agent_output(cls, agent_output: Dict[str, Any]) -> "RiskReport":
        """
        Build a ``RiskReport`` from the raw dict returned by ``risk_agent.analyze_risks()``.
        """
        return cls(
            risks=[RiskEntry(**r) for r in agent_output.get("risks", [])],
            overall_risk_score=agent_output.get("overall_risk_score", 0.0),
        )
