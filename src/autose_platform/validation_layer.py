"""
Validation Layer for AutoSE Platform.

This module implements deterministic validation of product compatibility.
"""

from typing import List
from .models import Product, StructuredRequirements, ValidationResult
from .config import settings


class ValidationLayer:
    """Deterministic validation of product compatibility."""
    
    def __init__(self):
        """Initialize the validation layer with configuration."""
        self.power_threshold = settings.POWER_THRESHOLD_W
    
    async def validate(self, products: List[Product], 
                      requirements: StructuredRequirements) -> ValidationResult:
        """
        Validate product compatibility with requirements.
        
        Args:
            products: List of selected products
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
    
    def _validate_power(self, products: List[Product], 
                       requirements: StructuredRequirements,
                       validation: ValidationResult):
        """Validate power requirements."""
        # Calculate total power consumption
        total_power = 0
        for product in products:
            total_power += product.power_w
        
        # Add estimated power from requirements
        total_power += requirements.estimated_power_w
        
        # Check against threshold
        if total_power > self.power_threshold:
            validation.power_check = "FAIL"
            validation.power_warning = (
                f"Total power consumption ({total_power}W) exceeds "
                f"UPS capacity ({self.power_threshold}W). "
                f"Consider adding additional UPS units or reducing power requirements."
            )
            validation.warnings.append(validation.power_warning)
        elif total_power > self.power_threshold * 0.8:  # 80% of capacity
            validation.power_check = "WARNING"
            validation.power_warning = (
                f"Total power consumption ({total_power}W) is close to "
                f"UPS capacity ({self.power_threshold}W). "
                f"Consider adding a second UPS for redundancy."
            )
            validation.warnings.append(validation.power_warning)
        
        # Check if UPS is included for significant power
        if total_power > 1000:
            has_ups = any(p.name == "UPS 5000W" for p in products)
            if not has_ups:
                validation.warnings.append(
                    f"Power consumption ({total_power}W) is significant. "
                    f"Consider adding UPS 5000W for power backup."
                )
    
    def _validate_network(self, products: List[Product],
                         requirements: StructuredRequirements,
                         validation: ValidationResult):
        """Validate network requirements."""
        # Calculate total available ports
        total_ports = 0
        for product in products:
            total_ports += product.port_count
        
        # Check if ports meet requirements
        if requirements.network_ports > 0 and total_ports < requirements.network_ports:
            validation.network_check = "FAIL"
            validation.warnings.append(
                f"Insufficient network ports: {total_ports} available, "
                f"{requirements.network_ports} required. "
                f"Consider adding additional switches."
            )
        elif requirements.network_ports > 0 and total_ports == requirements.network_ports:
            validation.network_check = "WARNING"
            validation.warnings.append(
                f"Network ports exactly match requirements ({total_ports} ports). "
                f"No spare ports for expansion. Consider adding extra capacity."
            )
        
        # Check if switch is included for network requirements
        if requirements.network_ports > 0:
            has_switch = any(p.name == "Switch 48P" for p in products)
            if not has_switch:
                validation.warnings.append(
                    f"Network ports required ({requirements.network_ports}), "
                    f"but no switch included. Consider adding Switch 48P."
                )
    
    def _validate_gpu(self, products: List[Product],
                     requirements: StructuredRequirements,
                     validation: ValidationResult):
        """Validate GPU requirements."""
        # Calculate total GPUs
        total_gpus = 0
        for product in products:
            total_gpus += product.gpu_count
        
        # Check GPU requirements
        if requirements.gpu_required and total_gpus == 0:
            validation.gpu_check = "FAIL"
            validation.warnings.append(
                "GPU acceleration required but no GPU-enabled products selected. "
                "Consider adding AI Server X1, AI Server X2, or Edge Node."
            )
        elif requirements.gpu_required and total_gpus < requirements.device_count / 50:
            # Rough heuristic: 1 GPU per 50 cameras for AI processing
            validation.gpu_check = "WARNING"
            validation.warnings.append(
                f"GPU count ({total_gpus}) may be insufficient for "
                f"{requirements.device_count} cameras. "
                f"Consider adding more GPU-enabled products."
            )
        
        # Check if GPU products are appropriate for camera count
        for product in products:
            if product.gpu_count > 0:
                # Edge Node is only suitable for small deployments
                if product.name == "Edge Node" and requirements.device_count > 20:
                    validation.warnings.append(
                        f"Edge Node (max {product.max_cameras} cameras) may be "
                        f"insufficient for {requirements.device_count} cameras. "
                        f"Consider upgrading to AI Server X1 or X2."
                    )
                
                # Check if product can support camera count
                if not product.can_support_cameras(requirements.device_count):
                    validation.warnings.append(
                        f"{product.name} (max {product.max_cameras} cameras) "
                        f"cannot support {requirements.device_count} cameras. "
                        f"Consider alternative products."
                    )
    
    def is_valid(self, validation: ValidationResult) -> bool:
        """Check if validation passed."""
        return validation.is_valid()