"""
Proposal Generator for AutoSE Platform.

This module generates proposals with explainable reasoning in markdown and JSON formats.
"""

from datetime import datetime
from typing import List, Dict, Any
from .models import Product, StructuredRequirements, ValidationResult, Proposal


class ProposalGenerator:
    """Generates final proposal with explainable reasoning."""
    
    async def generate(self, requirements: StructuredRequirements,
                      products: List[Product],
                      validation: ValidationResult) -> Proposal:
        """
        Generate comprehensive proposal.
        
        Args:
            requirements: Structured requirements
            products: Selected products
            validation: Validation results
            
        Returns:
            Proposal with markdown and JSON reasoning
        """
        # Generate markdown proposal
        markdown = self._generate_markdown(requirements, products, validation)
        
        # Generate JSON reasoning
        json_reasoning = self._generate_json_reasoning(requirements, products, validation)
        
        # Create and return proposal
        return Proposal(
            markdown=markdown,
            json=json_reasoning,  # Using alias name
            requirements=requirements,
            selected_products=products,
            validation=validation,
            timestamp=datetime.now().isoformat()
        )
    
    def _generate_markdown(self, requirements: StructuredRequirements,
                          products: List[Product],
                          validation: ValidationResult) -> str:
        """Generate markdown formatted proposal."""
        lines = []
        
        # Header
        lines.append("# AutoSE Platform Proposal")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        
        # Requirements Summary
        lines.append("## Requirements Summary")
        lines.append("")
        lines.append(f"- **Device Count**: {requirements.device_count} cameras/devices")
        lines.append(f"- **GPU Required**: {'Yes' if requirements.gpu_required else 'No'}")
        lines.append(f"- **Estimated Power**: {requirements.estimated_power_w}W")
        lines.append(f"- **Network Ports**: {requirements.network_ports} ports")
        lines.append("")
        
        # Recommended Products
        lines.append("## Recommended Products")
        lines.append("")
        
        for product in products:
            lines.append(f"### {product.name}")
            lines.append("")
            
            if product.power_w > 0:
                lines.append(f"- **Power Consumption**: {product.power_w}W")
            if product.gpu_count > 0:
                lines.append(f"- **GPU Count**: {product.gpu_count}")
            if product.price > 0:
                lines.append(f"- **Price**: ${product.price:,}")
            if product.max_cameras > 0:
                lines.append(f"- **Max Cameras Supported**: {product.max_cameras}")
            if product.port_count > 0:
                lines.append(f"- **Network Ports**: {product.port_count}")
            if product.capacity_w > 0:
                lines.append(f"- **Capacity**: {product.capacity_w}W")
            
            lines.append("")
        
        # Total Cost
        total_cost = sum(p.price for p in products)
        lines.append(f"**Total Estimated Cost**: ${total_cost:,}")
        lines.append("")
        
        # Validation Results
        lines.append("## Validation Results")
        lines.append("")
        
        lines.append(f"- **Power Check**: {validation.power_check}")
        if validation.power_warning:
            lines.append(f"  - *{validation.power_warning}*")
        
        lines.append(f"- **Network Check**: {validation.network_check}")
        lines.append(f"- **GPU Check**: {validation.gpu_check}")
        lines.append("")
        
        if validation.warnings:
            lines.append("### Warnings and Recommendations")
            lines.append("")
            for warning in validation.warnings:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")
        
        # Reasoning
        lines.append("## Reasoning")
        lines.append("")
        
        # Product selection reasoning
        lines.append("### Product Selection")
        lines.append("")
        
        ai_servers = [p for p in products if p.name.startswith("AI Server")]
        edge_nodes = [p for p in products if p.name == "Edge Node"]
        
        if ai_servers:
            for server in ai_servers:
                lines.append(f"- **{server.name}** selected because it supports up to {server.max_cameras} cameras")
                if requirements.gpu_required:
                    lines.append(f"  - Provides {server.gpu_count} GPUs for AI acceleration")
                lines.append(f"  - Power consumption: {server.power_w}W")
        
        if edge_nodes:
            for node in edge_nodes:
                lines.append(f"- **{node.name}** selected for edge processing")
                lines.append(f"  - Suitable for up to {node.max_cameras} cameras")
                if requirements.gpu_required:
                    lines.append(f"  - Includes 1 GPU for local AI processing")
        
        # Check for UPS
        ups_products = [p for p in products if p.name == "UPS 5000W"]
        if ups_products:
            lines.append(f"- **UPS 5000W** included for power backup")
            lines.append(f"  - Provides {ups_products[0].capacity_w}W capacity")
            total_power = sum(p.power_w for p in products) + requirements.estimated_power_w
            lines.append(f"  - Total system power: {total_power}W")
        
        # Check for Switch
        switch_products = [p for p in products if p.name == "Switch 48P"]
        if switch_products:
            lines.append(f"- **Switch 48P** included for network connectivity")
            lines.append(f"  - Provides {switch_products[0].port_count} ports")
            lines.append(f"  - Required ports: {requirements.network_ports}")
        
        lines.append("")
        
        # Alternatives Considered
        lines.append("### Alternatives Considered")
        lines.append("")
        
        # Explain why other products weren't selected
        all_products = [
            ("AI Server X1", 50, 15000),
            ("AI Server X2", 120, 28000),
            ("Edge Node", 10, 4000)
        ]
        
        for product_name, max_cameras, price in all_products:
            if not any(p.name == product_name for p in products):
                if requirements.device_count > max_cameras:
                    lines.append(f"- **{product_name}** not selected: Supports only {max_cameras} cameras (need {requirements.device_count})")
                elif any(p.name.startswith("AI Server") and p.max_cameras >= requirements.device_count for p in products):
                    # Another AI server already selected
                    selected_server = next(p for p in products if p.name.startswith("AI Server"))
                    if selected_server.max_cameras >= max_cameras and selected_server.price <= price:
                        lines.append(f"- **{product_name}** not selected: {selected_server.name} provides better value")
        
        lines.append("")
        
        # Risk Analysis
        lines.append("### Risk Analysis")
        lines.append("")
        
        if not validation.is_valid():
            lines.append("⚠️ **High Risk**: Validation checks failed")
            lines.append("  - Address validation warnings before proceeding")
        elif validation.warnings:
            lines.append("⚠️ **Medium Risk**: Validation warnings present")
            lines.append("  - Review warnings and consider recommendations")
        else:
            lines.append("✅ **Low Risk**: All validation checks passed")
            lines.append("  - Configuration is validated and ready for deployment")
        
        lines.append("")
        
        # Optimization Suggestions
        lines.append("### Optimization Suggestions")
        lines.append("")
        
        # Power optimization
        total_power = sum(p.power_w for p in products) + requirements.estimated_power_w
        if total_power > 4000:
            lines.append("- Consider adding a second UPS 5000W for redundancy")
        
        # Network optimization
        if requirements.network_ports > 24:
            lines.append("- Consider adding a second Switch 48P for network redundancy")
        
        # Cost optimization
        if requirements.device_count <= 10 and any(p.name.startswith("AI Server") for p in products):
            lines.append("- Consider Edge Node instead of AI Server for small deployments to reduce cost")
        
        # Future expansion
        lines.append(f"- Plan for {requirements.device_count * 1.2:.0f} cameras to allow 20% growth")
        
        lines.append("")
        
        # Next Steps
        lines.append("## Next Steps")
        lines.append("")
        lines.append("1. Review this proposal with stakeholders")
        lines.append("2. Address any validation warnings")
        lines.append("3. Contact vendors for pricing and availability")
        lines.append("4. Schedule deployment and testing")
        lines.append("5. Monitor system performance after deployment")
        
        return "\n".join(lines)
    
    def _generate_json_reasoning(self, requirements: StructuredRequirements,
                                products: List[Product],
                                validation: ValidationResult) -> Dict[str, Any]:
        """Generate JSON reasoning structure."""
        # Calculate totals
        total_power = sum(p.power_w for p in products) + requirements.estimated_power_w
        total_gpus = sum(p.gpu_count for p in products)
        total_ports = sum(p.port_count for p in products)
        total_cost = sum(p.price for p in products)
        
        # Build JSON structure
        return {
            "requirements": requirements.model_dump(),
            "selected_products": [p.model_dump() for p in products],
            "validation": validation.model_dump(),
            "totals": {
                "power_w": total_power,
                "gpu_count": total_gpus,
                "network_ports": total_ports,
                "cost_usd": total_cost
            },
            "reasoning": {
                "product_selection": self._get_product_selection_reasoning(requirements, products),
                "alternatives_rejected": self._get_rejected_alternatives(requirements, products),
                "risk_analysis": self._get_risk_analysis(validation),
                "optimization_suggestions": self._get_optimization_suggestions(requirements, products, validation)
            },
            "metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "validation_status": "VALID" if validation.is_valid() else "INVALID",
                "has_warnings": len(validation.warnings) > 0
            }
        }
    
    def _get_product_selection_reasoning(self, requirements: StructuredRequirements,
                                        products: List[Product]) -> List[str]:
        """Get reasoning for product selection."""
        reasoning = []
        
        for product in products:
            if product.name.startswith("AI Server"):
                reasoning.append(
                    f"{product.name} selected: Supports {product.max_cameras} cameras "
                    f"(required: {requirements.device_count}), "
                    f"has {product.gpu_count} GPUs "
                    f"(GPU required: {requirements.gpu_required})"
                )
            elif product.name == "Edge Node":
                reasoning.append(
                    f"Edge Node selected: Suitable for {product.max_cameras} cameras "
                    f"(required: {requirements.device_count}), "
                    f"has 1 GPU for edge processing"
                )
            elif product.name == "UPS 5000W":
                total_power = sum(p.power_w for p in products) + requirements.estimated_power_w
                reasoning.append(
                    f"UPS 5000W selected: Provides {product.capacity_w}W capacity "
                    f"(total power: {total_power}W)"
                )
            elif product.name == "Switch 48P":
                reasoning.append(
                    f"Switch 48P selected: Provides {product.port_count} ports "
                    f"(required: {requirements.network_ports})"
                )
        
        return reasoning
    
    def _get_rejected_alternatives(self, requirements: StructuredRequirements,
                                  products: List[Product]) -> List[str]:
        """Get reasoning for rejected alternatives."""
        rejected = []
        
        # Define all available products
        all_products = [
            ("AI Server X1", 50, 15000, 4),
            ("AI Server X2", 120, 28000, 8),
            ("Edge Node", 10, 4000, 1)
        ]
        
        for name, max_cameras, price, gpu_count in all_products:
            if not any(p.name == name for p in products):
                if requirements.device_count > max_cameras:
                    rejected.append(
                        f"{name}: Cannot support {requirements.device_count} cameras "
                        f"(max: {max_cameras})"
                    )
                elif requirements.gpu_required and gpu_count == 0:
                    rejected.append(
                        f"{name}: No GPU support (GPU required)"
                    )
                else:
                    # Check if a better alternative was selected
                    selected_servers = [p for p in products if p.name.startswith("AI Server")]
                    if selected_servers:
                        selected = selected_servers[0]
                        if selected.max_cameras >= max_cameras and selected.price <= price:
                            rejected.append(
                                f"{name}: {selected.name} provides better value "
                                f"({selected.max_cameras} cameras vs {max_cameras}, "
                                f"${selected.price} vs ${price})"
                            )
        
        return rejected
    
    def _get_risk_analysis(self, validation: ValidationResult) -> Dict[str, Any]:
        """Get risk analysis."""
        risk_level = "LOW"
        if not validation.is_valid():
            risk_level = "HIGH"
        elif validation.warnings:
            risk_level = "MEDIUM"
        
        return {
            "level": risk_level,
            "power_risk": validation.power_check,
            "network_risk": validation.network_check,
            "gpu_risk": validation.gpu_check,
            "warnings": validation.warnings
        }
    
    def _get_optimization_suggestions(self, requirements: StructuredRequirements,
                                     products: List[Product],
                                     validation: ValidationResult) -> List[str]:
        """Get optimization suggestions."""
        suggestions = []
        
        # Power optimization
        total_power = sum(p.power_w for p in products) + requirements.estimated_power_w
        if total_power > 4000:
            suggestions.append("Add second UPS 5000W for power redundancy")
        
        # Network optimization
        if requirements.network_ports > 24:
            suggestions.append("Add second Switch 48P for network redundancy")
        
        # Cost optimization
        if requirements.device_count <= 10 and any(p.name.startswith("AI Server") for p in products):
            suggestions.append("Consider Edge Node instead of AI Server for cost savings")
        
        # Future proofing
        suggestions.append(f"Plan for {int(requirements.device_count * 1.2)} cameras (20% growth)")
        
        # Address validation warnings
        for warning in validation.warnings:
            if "insufficient" in warning.lower():
                suggestions.append(f"Address: {warning}")
        
        return suggestions