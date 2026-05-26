"""
Validation Layer for AutoSE Platform.

This module implements deterministic validation of product compatibility.
"""

from typing import List, Dict, Any
from .models import StructuredRequirements, ValidationResult
from .config import settings


class ValidationLayer:
    """Deterministic validation of product compatibility."""
    
    def __init__(self):
        """Initialize the validation layer with configuration."""
        self.power_threshold = settings.POWER_THRESHOLD_W
    
    async def validate(self, products: List[Dict[str, Any]], 
                      requirements: StructuredRequirements) -> ValidationResult:
        """
        Validate product compatibility with requirements.
        
        Args:
            products: List of selected products as dictionaries
            requirements: Structured requirements
            
        Returns:
            ValidationResult with PASS/FAIL/WARNING statuses
        """
        # Initialize validation result
        validation = ValidationResult(
            power_check="PASS",
            network_check="PASS",
            gpu_check="PASS",
            warnings=[]
        )
        
        # Perform power validation
        self._validate_power(products, requirements, validation)
        
        # Perform network validation
        self._validate_network(products, requirements, validation)
        
        # Perform GPU validation
        self._validate_gpu(products, requirements, validation)
        
        return validation
    
    def _validate_power(self, products: List[Dict[str, Any]], 
                       requirements: StructuredRequirements,
                       validation: ValidationResult):
        """Validate power requirements."""
        # Calculate total power consumption
        total_power = 0
        for product in products:
            total_power += product.get("power_w", 0)
        
        # Add estimated power from requirements
        total_power += requirements.estimated_power_w
        
        # Check if we have UPS capacity
        ups_capacity = 0
        for product in products:
            if product.get("category") == "power":
                ups_capacity += product.get("capacity_w", 0)
        
        # If no UPS, use default threshold
        effective_threshold = ups_capacity if ups_capacity > 0 else self.power_threshold
        
        # Check against threshold
        if total_power > effective_threshold:
            validation.power_check = "FAIL"
            validation.power_warning = (
                f"Total power consumption ({total_power}W) exceeds "
                f"available capacity ({effective_threshold}W). "
                f"Consider adding additional UPS units or reducing power requirements."
            )
            validation.warnings.append(validation.power_warning)
        elif total_power > effective_threshold * 0.8:  # 80% of capacity
            validation.power_check = "WARNING"
            validation.power_warning = (
                f"Total power consumption ({total_power}W) is close to "
                f"available capacity ({effective_threshold}W). "
                f"Consider adding additional power backup for redundancy."
            )
            validation.warnings.append(validation.power_warning)
        
        # Check if power backup is included for significant power
        if total_power > 1000 and ups_capacity == 0:
            validation.warnings.append(
                f"Power consumption ({total_power}W) is significant. "
                f"Consider adding UPS for power backup."
            )
    
    def _validate_network(self, products: List[Dict[str, Any]],
                         requirements: StructuredRequirements,
                         validation: ValidationResult):
        """Validate network requirements."""
        # Calculate total available ports
        total_ports = 0
        for product in products:
            total_ports += product.get("ports", 0)
        
        # Check if ports meet requirements
        if requirements.network_ports > 0 and total_ports < requirements.network_ports:
            validation.network_check = "FAIL"
            validation.warnings.append(
                f"Insufficient network ports: {total_ports} available, "
                f"{requirements.network_ports} required. "
                f"Consider adding additional network equipment."
            )
        elif requirements.network_ports > 0 and total_ports == requirements.network_ports:
            validation.network_check = "WARNING"
            validation.warnings.append(
                f"Network ports exactly match requirements ({total_ports} ports). "
                f"No spare ports for expansion. Consider adding extra capacity."
            )
        
        # Check if network equipment is included for network requirements
        if requirements.network_ports > 0:
            has_network_equipment = any(p.get("category") == "network" for p in products)
            if not has_network_equipment:
                validation.warnings.append(
                    f"Network ports required ({requirements.network_ports}), "
                    f"but no network equipment included. Consider adding switches or routers."
                )
    
    def _validate_gpu(self, products: List[Dict[str, Any]],
                     requirements: StructuredRequirements,
                     validation: ValidationResult):
        """Validate GPU requirements."""
        # Calculate total GPUs
        total_gpus = 0
        for product in products:
            total_gpus += product.get("gpu", 0)
        
        # Check GPU requirements
        if requirements.gpu_required and total_gpus == 0:
            validation.gpu_check = "FAIL"
            validation.warnings.append(
                "GPU acceleration required but no GPU-enabled products selected. "
                "Consider adding server products with GPU support."
            )
        elif requirements.gpu_required and total_gpus < requirements.device_count / 50:
            # Rough heuristic: 1 GPU per 50 cameras for AI processing
            validation.gpu_check = "WARNING"
            validation.warnings.append(
                f"GPU count ({total_gpus}) may be insufficient for "
                f"{requirements.device_count} devices. "
                f"Consider adding more GPU-enabled products."
            )
        
        # Check if products are appropriate for device count
        for product in products:
            category = product.get("category", "")
            name = product.get("name", "")
            
            if category == "server":
                max_cameras = product.get("max_cameras", 0)
                
                # Edge Node is only suitable for small deployments
                if name == "Edge Node" and requirements.device_count > 20:
                    validation.warnings.append(
                        f"Edge Node (max {max_cameras} cameras) may be "
                        f"insufficient for {requirements.device_count} devices. "
                        f"Consider upgrading to more powerful server."
                    )
                
                # Check if product can support camera count
                if max_cameras > 0 and max_cameras < requirements.device_count:
                    validation.warnings.append(
                        f"{name} (max {max_cameras} cameras) "
                        f"cannot support {requirements.device_count} devices. "
                        f"Consider alternative products."
                    )
            
            elif category == "security":
                max_cameras = product.get("max_cameras", 0)
                if max_cameras > 0 and max_cameras < requirements.device_count:
                    validation.warnings.append(
                        f"{name} (max {max_cameras} cameras) "
                        f"cannot support {requirements.device_count} devices. "
                        f"Consider alternative security products."
                    )
    
    def is_valid(self, validation: ValidationResult) -> bool:
        """Check if validation passed."""
        return validation.is_valid()