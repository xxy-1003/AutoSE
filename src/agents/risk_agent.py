"""
Risk Intelligence Agent for AutoSE Platform.

Analyzes a solution (products + requirements) using deterministic rules
and produces a structured risk report with severity, likelihood, and mitigations.

No LLM is used — all logic is pure Python rule evaluation.
"""

from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Thresholds (tunable constants)
# ---------------------------------------------------------------------------

POWER_OVERLOAD_THRESHOLD_W: int = 5_000       # Total system power ceiling (W)
POWER_WARNING_RATIO: float = 0.80             # Warn when power > 80 % of threshold
THERMAL_DENSITY_THRESHOLD_W: float = 2_000.0  # W per "rack unit" proxy
GPU_CAMERAS_PER_GPU: int = 50                 # Cameras one GPU can handle comfortably
NETWORK_SATURATION_DEVICE_THRESHOLD: int = 80  # Devices that stress a single switch
NETWORK_SATURATION_HIGH_THRESHOLD: int = 150   # Devices that almost certainly saturate


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a float to [lo, hi]."""
    return max(lo, min(hi, value))


def _total_power_w(products: List[Dict[str, Any]]) -> int:
    """Sum power_w across all products."""
    return sum(p.get("power_w", 0) for p in products)


def _ups_capacity_w(products: List[Dict[str, Any]]) -> int:
    """Sum capacity_w for all UPS / power products."""
    return sum(
        p.get("capacity_w", 0)
        for p in products
        if p.get("category") == "power" or p.get("capacity_w", 0) > 0
    )


def _total_gpus(products: List[Dict[str, Any]]) -> int:
    """Sum GPU count across all products (supports both 'gpu' and 'gpu_count' keys)."""
    return sum(p.get("gpu", p.get("gpu_count", 0)) for p in products)


def _total_ports(products: List[Dict[str, Any]]) -> int:
    """Sum network ports across all products (supports 'ports' and 'port_count' keys)."""
    return sum(p.get("ports", p.get("port_count", 0)) for p in products)


def _server_products(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [p for p in products if p.get("category") == "server"]


# ---------------------------------------------------------------------------
# Individual risk detectors
# ---------------------------------------------------------------------------

def _check_power_overload(
    products: List[Dict[str, Any]],
    requirements: Dict[str, Any],
) -> Dict[str, Any] | None:
    """
    Detect power overload risk.

    Compares total system power (products + estimated requirement power) against
    the effective capacity (UPS if present, otherwise the hard threshold).
    """
    total_power = _total_power_w(products) + requirements.get("estimated_power_w", 0)
    ups_capacity = _ups_capacity_w(products)
    effective_limit = ups_capacity if ups_capacity > 0 else POWER_OVERLOAD_THRESHOLD_W

    if total_power <= effective_limit * POWER_WARNING_RATIO:
        return None  # No risk

    over_ratio = total_power / effective_limit  # e.g. 1.2 = 20 % over

    if over_ratio >= 1.0:
        severity = "high"
        likelihood = _clamp(0.5 + (over_ratio - 1.0) * 2.0)
        description = (
            f"Total system power ({total_power} W) exceeds the effective power "
            f"capacity ({effective_limit} W). This will cause UPS overload or "
            f"circuit breaker trips under full load."
        )
        mitigation = (
            "Add a higher-capacity UPS or a second UPS unit. "
            "Consider replacing high-draw servers with more power-efficient models. "
            "Stagger device startup to reduce peak inrush current."
        )
    else:
        severity = "medium"
        likelihood = _clamp(0.3 + (over_ratio - POWER_WARNING_RATIO) * 1.5)
        description = (
            f"Total system power ({total_power} W) is at "
            f"{over_ratio * 100:.0f}% of the effective capacity ({effective_limit} W). "
            f"Headroom is insufficient for load spikes or future expansion."
        )
        mitigation = (
            "Upgrade to a higher-capacity UPS. "
            "Review power budgets for each device and remove non-essential equipment. "
            "Plan for at least 20 % power headroom above peak load."
        )

    return {
        "type": "power_overload",
        "severity": severity,
        "likelihood": round(likelihood, 2),
        "description": description,
        "mitigation": mitigation,
    }


def _check_gpu_bottleneck(
    products: List[Dict[str, Any]],
    requirements: Dict[str, Any],
) -> Dict[str, Any] | None:
    """
    Detect GPU bottleneck risk.

    Compares available GPU count against the number of cameras / devices
    that need AI inference processing.
    """
    if not requirements.get("gpu_required", False):
        return None  # GPU not needed — no bottleneck possible

    device_count: int = requirements.get("device_count", 0)
    total_gpus = _total_gpus(products)

    if total_gpus == 0:
        return {
            "type": "gpu_bottleneck",
            "severity": "high",
            "likelihood": 0.95,
            "description": (
                f"GPU acceleration is required for {device_count} devices, "
                f"but no GPU-enabled products are included in the solution. "
                f"AI inference workloads will fail or fall back to CPU, causing "
                f"severe performance degradation."
            ),
            "mitigation": (
                "Add at least one GPU-enabled server (e.g. AI Server X1 or X2). "
                f"Rule of thumb: 1 GPU per {GPU_CAMERAS_PER_GPU} cameras for real-time inference."
            ),
        }

    cameras_per_gpu = device_count / total_gpus
    ratio = cameras_per_gpu / GPU_CAMERAS_PER_GPU  # > 1.0 means overloaded

    if ratio <= 0.75:
        return None  # Comfortable headroom

    if ratio >= 1.0:
        severity = "high"
        likelihood = _clamp(0.6 + (ratio - 1.0) * 0.4)
        description = (
            f"{device_count} devices require AI inference but only {total_gpus} GPU(s) "
            f"are available ({cameras_per_gpu:.0f} cameras/GPU, recommended ≤ {GPU_CAMERAS_PER_GPU}). "
            f"Inference latency will exceed real-time requirements under full load."
        )
        mitigation = (
            f"Add {int((device_count / GPU_CAMERAS_PER_GPU) - total_gpus + 1)} more GPU(s) "
            f"or upgrade to a higher-GPU server. "
            f"Consider frame-rate reduction or selective AI processing to reduce GPU demand."
        )
    else:
        severity = "medium"
        likelihood = _clamp(0.3 + (ratio - 0.75) * 1.2)
        description = (
            f"{device_count} devices share {total_gpus} GPU(s) "
            f"({cameras_per_gpu:.0f} cameras/GPU). "
            f"GPU utilisation is high; performance may degrade during peak hours."
        )
        mitigation = (
            "Monitor GPU utilisation in production. "
            "Pre-provision an additional GPU-enabled node for failover. "
            "Implement load-balancing across inference workers."
        )

    return {
        "type": "gpu_bottleneck",
        "severity": severity,
        "likelihood": round(likelihood, 2),
        "description": description,
        "mitigation": mitigation,
    }


def _check_thermal_risk(
    products: List[Dict[str, Any]],
    requirements: Dict[str, Any],
) -> Dict[str, Any] | None:
    """
    Detect thermal / cooling risk.

    Uses total power draw as a proxy for heat generation.
    High-density deployments (many watts in a small space) risk overheating
    without adequate cooling infrastructure.
    """
    total_power = _total_power_w(products) + requirements.get("estimated_power_w", 0)
    server_count = len(_server_products(products))

    # Estimate power density: if multiple servers share a rack, density is higher
    density_factor = max(1, server_count)
    effective_density = total_power / density_factor

    if effective_density <= THERMAL_DENSITY_THRESHOLD_W * 0.6:
        return None

    ratio = effective_density / THERMAL_DENSITY_THRESHOLD_W

    if ratio >= 1.0:
        severity = "high"
        likelihood = _clamp(0.55 + (ratio - 1.0) * 0.35)
        description = (
            f"Estimated power density ({effective_density:.0f} W per server unit) "
            f"exceeds the thermal threshold ({THERMAL_DENSITY_THRESHOLD_W:.0f} W). "
            f"Without adequate cooling, hardware may throttle or fail prematurely."
        )
        mitigation = (
            "Ensure the server room has dedicated precision air conditioning (CRAC/CRAH). "
            "Implement hot-aisle/cold-aisle containment. "
            "Add redundant cooling units and temperature monitoring with automated alerts."
        )
    else:
        severity = "medium"
        likelihood = _clamp(0.25 + (ratio - 0.6) * 0.5)
        description = (
            f"Power density ({effective_density:.0f} W per server unit) is approaching "
            f"the thermal threshold ({THERMAL_DENSITY_THRESHOLD_W:.0f} W). "
            f"Cooling capacity should be reviewed before adding more equipment."
        )
        mitigation = (
            "Audit current cooling capacity against projected heat load. "
            "Install in-row cooling if rack density increases. "
            "Deploy temperature sensors and set alerting thresholds."
        )

    return {
        "type": "thermal_risk",
        "severity": severity,
        "likelihood": round(likelihood, 2),
        "description": description,
        "mitigation": mitigation,
    }


def _check_network_saturation(
    products: List[Dict[str, Any]],
    requirements: Dict[str, Any],
) -> Dict[str, Any] | None:
    """
    Detect network saturation risk.

    Large device counts stress switch bandwidth and port availability.
    Also checks whether available ports are sufficient for the device count.
    """
    device_count: int = requirements.get("device_count", 0)
    total_ports = _total_ports(products)

    # Port sufficiency check
    port_deficit = device_count - total_ports if total_ports > 0 else 0

    if device_count <= NETWORK_SATURATION_DEVICE_THRESHOLD * 0.5 and port_deficit <= 0:
        return None

    # Determine severity from device count and port deficit
    if device_count >= NETWORK_SATURATION_HIGH_THRESHOLD or port_deficit > 0:
        severity = "high"
        likelihood = _clamp(
            0.6 + max(
                (device_count - NETWORK_SATURATION_HIGH_THRESHOLD) / 100,
                port_deficit / max(device_count, 1),
            )
        )
        if port_deficit > 0:
            description = (
                f"Only {total_ports} network ports are available for {device_count} devices "
                f"(deficit: {port_deficit} ports). Devices cannot be connected without "
                f"additional switching infrastructure."
            )
            mitigation = (
                f"Add {port_deficit} or more switch ports. "
                "Consider a 48-port managed switch or a stacked switch configuration. "
                "Reserve 10–20 % of ports for future expansion."
            )
        else:
            description = (
                f"{device_count} devices on the network creates high broadcast domain traffic "
                f"and risks switch CPU overload, ARP storms, and increased collision rates."
            )
            mitigation = (
                "Segment the network into VLANs to reduce broadcast domains. "
                "Use managed switches with QoS policies to prioritise video/AI traffic. "
                "Consider a spine-leaf topology for large deployments."
            )
    else:
        severity = "medium"
        likelihood = _clamp(
            0.3 + (device_count - NETWORK_SATURATION_DEVICE_THRESHOLD * 0.5)
            / NETWORK_SATURATION_DEVICE_THRESHOLD
        )
        description = (
            f"{device_count} devices may stress a single-switch network segment. "
            f"Bandwidth contention is possible during peak recording or AI inference bursts."
        )
        mitigation = (
            "Upgrade to a higher-throughput switch (10 GbE uplinks). "
            "Implement traffic shaping and QoS. "
            "Monitor switch CPU and bandwidth utilisation regularly."
        )

    return {
        "type": "network_saturation",
        "severity": severity,
        "likelihood": round(likelihood, 2),
        "description": description,
        "mitigation": mitigation,
    }


# ---------------------------------------------------------------------------
# Severity → numeric weight mapping
# ---------------------------------------------------------------------------

_SEVERITY_WEIGHT: Dict[str, float] = {
    "low": 0.2,
    "medium": 0.5,
    "high": 1.0,
}


def _compute_overall_score(risks: List[Dict[str, Any]]) -> float:
    """
    Compute an overall risk score in [0.0, 1.0].

    Formula: weighted average of (severity_weight × likelihood) for each risk,
    then normalised so that a single high-likelihood high-severity risk scores ~0.8.
    """
    if not risks:
        return 0.0

    weighted_sum = sum(
        _SEVERITY_WEIGHT.get(r["severity"], 0.5) * r["likelihood"]
        for r in risks
    )
    # Normalise: max possible per risk = 1.0 × 1.0 = 1.0
    # We cap at 1.0 and scale so that 2 high risks ≈ 0.9
    raw = weighted_sum / len(risks)
    # Apply a mild amplification so a single high risk is still noticeable
    amplified = _clamp(raw * 1.4)
    return round(amplified, 3)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_risks(
    products: List[Dict[str, Any]],
    requirements: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analyze a solution and return a structured risk report.

    Args:
        products:     List of product dictionaries from the catalog.
                      Each dict may contain keys such as:
                        - name, category, power_w, gpu / gpu_count,
                          ports / port_count, capacity_w, max_cameras, price
        requirements: Dictionary of structured requirements.
                      Expected keys:
                        - device_count (int)
                        - gpu_required (bool)
                        - estimated_power_w (int)
                        - network_ports (int)

    Returns:
        {
            "risks": [
                {
                    "type": str,          # e.g. "power_overload"
                    "severity": str,      # "low" | "medium" | "high"
                    "likelihood": float,  # 0.0 – 1.0
                    "description": str,
                    "mitigation": str,
                }
            ],
            "overall_risk_score": float   # 0.0 – 1.0
        }
    """
    detectors = [
        _check_power_overload,
        _check_gpu_bottleneck,
        _check_thermal_risk,
        _check_network_saturation,
    ]

    risks: List[Dict[str, Any]] = []
    for detector in detectors:
        result = detector(products, requirements)
        if result is not None:
            risks.append(result)

    overall_score = _compute_overall_score(risks)

    return {
        "risks": risks,
        "overall_risk_score": overall_score,
    }


# ---------------------------------------------------------------------------
# Convenience: accept StructuredRequirements Pydantic model directly
# ---------------------------------------------------------------------------

def analyze_risks_from_model(products: List[Dict[str, Any]], requirements_model: Any) -> Dict[str, Any]:
    """
    Thin wrapper that accepts a StructuredRequirements Pydantic model
    (or any object with the same attributes) instead of a plain dict.

    Args:
        products:           List of product dicts.
        requirements_model: StructuredRequirements instance (or compatible object).

    Returns:
        Same structure as analyze_risks().
    """
    if hasattr(requirements_model, "model_dump"):
        requirements_dict = requirements_model.model_dump()
    elif hasattr(requirements_model, "dict"):
        requirements_dict = requirements_model.dict()
    else:
        requirements_dict = dict(requirements_model)

    return analyze_risks(products, requirements_dict)
