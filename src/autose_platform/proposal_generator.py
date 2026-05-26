"""
Proposal Generator for AutoSE Platform.

This module generates proposals with explainable reasoning in markdown and JSON formats.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from .models import StructuredRequirements, ValidationResult, Proposal


class ProposalGenerator:
    """Generates final proposal with explainable reasoning."""
    
    async def generate(self, requirements: StructuredRequirements,
                      products: List[Dict[str, Any]],
                      validation: ValidationResult,
                      additional_info: Optional[Dict[str, Any]] = None) -> Proposal:
        """
        Generate comprehensive proposal.
        
        Args:
            requirements: Structured requirements
            products: Selected products as dictionaries
            validation: Validation results
            additional_info: Additional information from requirement analyzer
            
        Returns:
            Proposal with markdown and JSON reasoning
        """
        # Generate markdown proposal
        markdown = self._generate_markdown(requirements, products, validation, additional_info)
        
        # Generate JSON reasoning
        json_reasoning = self._generate_json_reasoning(requirements, products, validation, additional_info)
        
        # Create and return proposal
        return Proposal(
            markdown=markdown,
            json=json_reasoning,  # Using alias name
            requirements=requirements,
            selected_products=[],  # Empty list since we're using dictionaries
            validation=validation,
            timestamp=datetime.now().isoformat()
        )
    
    def generate_negotiation_response(self, 
                                     current_solution: Dict[str, Any],
                                     negotiation_intent: Dict[str, bool],
                                     constraints: Dict[str, Any],
                                     alternative_solutions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Generate negotiation response with clarifying questions and alternatives.
        
        Args:
            current_solution: Current solution dictionary
            negotiation_intent: Negotiation intent flags
            constraints: Extracted constraints
            alternative_solutions: Dictionary with alternative solutions
            
        Returns:
            Dictionary with negotiation response
        """
        response = {
            "is_negotiation": True,
            "intent": negotiation_intent,
            "constraints": constraints,
            "current_solution_summary": self._summarize_solution(current_solution),
            "clarifying_questions": [],
            "alternative_options": {},
            "recommended_action": ""
        }
        
        # Generate clarifying questions based on intent
        if negotiation_intent.get("is_complaining", False):
            response["clarifying_questions"].extend([
                "What feels wrong? Is it the price, performance, or number of devices?",
                "Would you like me to: A) Lower total price B) Reduce device count C) Replace with cheaper models?",
                "Can you specify which part doesn't match your needs?"
            ])
        
        if negotiation_intent.get("is_rejecting", False) or negotiation_intent.get("wants_lower_price", False):
            response["clarifying_questions"].extend([
                f"Your current budget is ${constraints.get('budget_limit', 0):,}. How much lower would you like the price to be?",
                "Would you prefer to reduce features or find cheaper alternatives?",
                "Should I focus on reducing the most expensive items first?"
            ])
        
        if negotiation_intent.get("wants_fewer_devices", False):
            response["clarifying_questions"].extend([
                f"How many devices/cameras would you prefer? (Current: {current_solution.get('requirements', {}).get('device_count', 'N/A')})",
                "Should I remove optional features or reduce quantities?",
                "Would you like to keep core functionality with fewer devices?"
            ])
        
        if negotiation_intent.get("wants_alternative", False):
            response["clarifying_questions"].extend([
                "What type of alternative are you looking for? Cheaper, more powerful, or different approach?",
                "Should I focus on specific product categories for alternatives?",
                "Do you have any specific requirements for the alternative solution?"
            ])
        
        # If no specific intent detected, ask general clarifying questions
        if not response["clarifying_questions"]:
            response["clarifying_questions"] = [
                "I understand you're not satisfied. Can you tell me what specifically needs adjustment?",
                "Is it about the budget, features, scalability, or something else?",
                "How can I help improve this solution for you?"
            ]
        
        # Add alternative solutions if available
        if alternative_solutions:
            response["alternative_options"] = {
                "economy": self._summarize_solution_with_cost(alternative_solutions.get("economy", [])),
                "balanced": self._summarize_solution_with_cost(alternative_solutions.get("balanced", [])),
                "performance": self._summarize_solution_with_cost(alternative_solutions.get("performance", []))
            }
            
            # Add comparison of alternatives
            response["alternative_comparison"] = self._compare_alternatives(alternative_solutions)
        
        # Generate recommended action
        response["recommended_action"] = self._generate_recommended_action(negotiation_intent, constraints, current_solution)
        
        return response
    
    def _summarize_solution(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize a solution for display."""
        if not solution:
            return {}
        
        products = solution.get("products", [])
        requirements = solution.get("requirements", {})
        
        total_cost = sum(p.get("price", 0) for p in products)
        total_power = sum(p.get("power_w", 0) for p in products)
        
        # Get most expensive items
        expensive_items = sorted(products, key=lambda p: p.get("price", 0), reverse=True)[:3]
        
        return {
            "total_cost": total_cost,
            "total_power": total_power,
            "device_count": requirements.get("device_count", 0),
            "most_expensive_items": [
                {"name": item.get("name", ""), "price": item.get("price", 0), "category": item.get("category", "")}
                for item in expensive_items
            ],
            "product_count": len(products)
        }
    
    def _summarize_solution_with_cost(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize a list of products with cost analysis."""
        if not products:
            return {"total_cost": 0, "product_count": 0, "products": []}
        
        total_cost = sum(p.get("price", 0) for p in products)
        total_power = sum(p.get("power_w", 0) for p in products)
        
        return {
            "total_cost": total_cost,
            "total_power": total_power,
            "product_count": len(products),
            "products": [
                {"name": p.get("name", ""), "price": p.get("price", 0), "category": p.get("category", "")}
                for p in products[:5]  # Limit to top 5 products
            ]
        }
    
    def _compare_alternatives(self, alternatives: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Compare alternative solutions."""
        comparison = {}
        
        for alt_type, products in alternatives.items():
            if products:
                total_cost = sum(p.get("price", 0) for p in products)
                comparison[alt_type] = {
                    "total_cost": total_cost,
                    "product_count": len(products),
                    "key_features": self._extract_key_features(products, alt_type)
                }
        
        return comparison
    
    def _extract_key_features(self, products: List[Dict[str, Any]], alt_type: str) -> List[str]:
        """Extract key features for alternative solution."""
        features = []
        
        for product in products:
            category = product.get("category", "")
            name = product.get("name", "")
            
            if category == "server":
                max_cameras = product.get("max_cameras", 0)
                gpu = product.get("gpu", 0)
                features.append(f"{name}: Supports {max_cameras} cameras, {gpu} GPUs")
            
            elif category == "network":
                ports = product.get("ports", 0)
                features.append(f"{name}: {ports} network ports")
            
            elif category == "power":
                capacity = product.get("capacity_w", 0)
                features.append(f"{name}: {capacity}W backup power")
        
        # Add type-specific features
        if alt_type == "economy":
            features.insert(0, "💰 **Most cost-effective solution**")
            features.append("✅ Best for tight budgets")
        elif alt_type == "balanced":
            features.insert(0, "⚖️ **Balanced cost vs performance**")
            features.append("✅ Good value for money")
        elif alt_type == "performance":
            features.insert(0, "🚀 **Highest performance solution**")
            features.append("✅ Best for demanding applications")
        
        return features[:5]  # Limit to 5 features
    
    def _generate_recommended_action(self, 
                                    negotiation_intent: Dict[str, bool],
                                    constraints: Dict[str, Any],
                                    current_solution: Dict[str, Any]) -> str:
        """Generate recommended action based on negotiation context."""
        products = current_solution.get("products", [])
        current_cost = sum(p.get("price", 0) for p in products)
        budget_limit = constraints.get("budget_limit", 0)
        
        if negotiation_intent.get("wants_lower_price", False) and budget_limit > 0:
            if current_cost > budget_limit:
                return f"Reduce total cost from ${current_cost:,} to under ${budget_limit:,} by selecting cheaper alternatives"
            else:
                return "Optimize solution to provide better value within your budget"
        
        elif negotiation_intent.get("wants_fewer_devices", False):
            device_count = constraints.get("device_count")
            if device_count:
                return f"Adjust solution for {device_count} devices instead of {current_solution.get('requirements', {}).get('device_count', 'N/A')}"
            else:
                return "Simplify solution by reducing device count and optional features"
        
        elif negotiation_intent.get("wants_alternative", False):
            return "Provide 3 alternative options: Economy (cheapest), Balanced (value), Performance (best)"
        
        elif negotiation_intent.get("is_complaining", False):
            return "Identify and address the specific concern (price, features, compatibility)"
        
        else:
            return "Review the solution and suggest improvements based on your feedback"
    
    def _generate_markdown(self, requirements: StructuredRequirements,
                          products: List[Dict[str, Any]],
                          validation: ValidationResult,
                          additional_info: Optional[Dict[str, Any]] = None) -> str:
        """Generate markdown formatted proposal."""
        lines = []
        
        # Header
        lines.append("# AutoSE Platform Proposal")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        
        # Project Information
        if additional_info and additional_info.get("project_type") != "unknown":
            lines.append(f"## Project Type: {additional_info['project_type'].replace('_', ' ').title()}")
            lines.append("")
        
        # Requirements Summary
        lines.append("## Requirements Summary")
        lines.append("")
        lines.append(f"- **Device Count**: {requirements.device_count} cameras/devices")
        lines.append(f"- **GPU Required**: {'Yes' if requirements.gpu_required else 'No'}")
        lines.append(f"- **Estimated Power**: {requirements.estimated_power_w}W")
        lines.append(f"- **Network Ports**: {requirements.network_ports} ports")
        
        # Additional requirements if available
        if additional_info:
            if additional_info.get("camera_count", 0) > 0:
                lines.append(f"- **Camera Count**: {additional_info['camera_count']}")
            if additional_info.get("room_count", 0) > 0:
                lines.append(f"- **Room Count**: {additional_info['room_count']}")
            if additional_info.get("user_count", 0) > 0:
                lines.append(f"- **User Count**: {additional_info['user_count']}")
            if additional_info.get("budget_limit", 0) > 0:
                lines.append(f"- **Budget Limit**: ${additional_info['budget_limit']:,}")
        
        lines.append("")
        
        # Recommended Products by Category
        lines.append("## Recommended Products")
        lines.append("")
        
        # Group products by category
        products_by_category = {}
        for product in products:
            category = product.get("category", "unknown")
            if category not in products_by_category:
                products_by_category[category] = []
            products_by_category[category].append(product)
        
        # Display products by category
        for category, category_products in products_by_category.items():
            category_name = category.replace("_", " ").title()
            lines.append(f"### {category_name}")
            lines.append("")
            
            for product in category_products:
                lines.append(f"#### {product.get('name', 'Unknown Product')}")
                lines.append("")
                
                # Display product attributes
                if product.get("price", 0) > 0:
                    lines.append(f"- **Price**: ${product['price']:,}")
                
                if product.get("power_w", 0) > 0:
                    lines.append(f"- **Power Consumption**: {product['power_w']}W")
                
                if product.get("gpu", 0) > 0:
                    lines.append(f"- **GPU Count**: {product['gpu']}")
                
                if product.get("max_cameras", 0) > 0:
                    lines.append(f"- **Max Cameras Supported**: {product['max_cameras']}")
                
                if product.get("ports", 0) > 0:
                    lines.append(f"- **Network Ports**: {product['ports']}")
                
                if product.get("capacity_w", 0) > 0:
                    lines.append(f"- **Capacity**: {product['capacity_w']}W")
                
                # Display other attributes
                for key, value in product.items():
                    if key not in ["id", "name", "category", "price", "power_w", "gpu", "max_cameras", "ports", "capacity_w"]:
                        if isinstance(value, (int, float)) and value > 0:
                            lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
                        elif isinstance(value, str) and value:
                            lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
                
                lines.append("")
        
        # Totals
        lines.append("## Totals")
        lines.append("")
        
        total_cost = sum(p.get("price", 0) for p in products)
        total_power = sum(p.get("power_w", 0) for p in products)
        total_gpus = sum(p.get("gpu", 0) for p in products)
        total_ports = sum(p.get("ports", 0) for p in products)
        
        lines.append(f"- **Total Cost**: ${total_cost:,}")
        lines.append(f"- **Total Power Consumption**: {total_power}W")
        if total_gpus > 0:
            lines.append(f"- **Total GPUs**: {total_gpus}")
        if total_ports > 0:
            lines.append(f"- **Total Network Ports**: {total_ports}")
        
        # Power budget analysis
        if additional_info and additional_info.get("budget_limit", 0) > 0:
            budget_utilization = (total_cost / additional_info["budget_limit"]) * 100
            lines.append(f"- **Budget Utilization**: {budget_utilization:.1f}%")
            if budget_utilization > 100:
                lines.append(f"  - ⚠️ **Over budget by**: ${total_cost - additional_info['budget_limit']:,}")
            elif budget_utilization > 90:
                lines.append(f"  - ⚠️ **Close to budget limit**")
            else:
                lines.append(f"  - ✅ **Within budget**")
        
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
        
        # Smart Home Specific Logic
        if additional_info and additional_info.get("project_type") == "smart_home":
            lines.append("## Smart Home Configuration")
            lines.append("")
            
            room_count = additional_info.get("room_count", 0)
            if room_count > 0:
                lines.append(f"### For a {room_count}-bedroom house:")
                lines.append("")
                
                # Count smart home products
                smart_home_products = [p for p in products if p.get("category") == "smart_home"]
                sensor_products = [p for p in products if p.get("category") == "sensor"]
                
                if smart_home_products:
                    lines.append("**Smart Home Devices:**")
                    for product in smart_home_products:
                        lines.append(f"- {product.get('name')}")
                
                if sensor_products:
                    lines.append("")
                    lines.append("**Sensors:**")
                    for product in sensor_products:
                        lines.append(f"- {product.get('name')}")
                
                lines.append("")
                lines.append("**Typical Placement:**")
                lines.append(f"- 1 Smart Control Panel in living room")
                lines.append(f"- {room_count + 1} Smart Light Controllers ({room_count} bedrooms + living room)")
                lines.append(f"- {room_count * 2} Smart Plugs (2 per room)")
                lines.append(f"- {room_count} Motion Sensors (1 per bedroom)")
                lines.append(f"- {room_count + 1} Door Sensors (front door + {room_count} bedrooms)")
                lines.append("")
        
        # Reasoning
        lines.append("## Reasoning")
        lines.append("")
        
        # Product selection reasoning
        lines.append("### Product Selection")
        lines.append("")
        
        for product in products:
            category = product.get("category", "")
            name = product.get("name", "")
            
            if category == "server":
                max_cameras = product.get("max_cameras", 0)
                gpu_count = product.get("gpu", 0)
                
                lines.append(f"- **{name}** selected because:")
                if max_cameras > 0:
                    lines.append(f"  - Supports up to {max_cameras} cameras (required: {requirements.device_count})")
                if gpu_count > 0 and requirements.gpu_required:
                    lines.append(f"  - Provides {gpu_count} GPUs for AI acceleration")
                if product.get("power_w", 0) > 0:
                    lines.append(f"  - Power consumption: {product['power_w']}W")
            
            elif category == "network":
                ports = product.get("ports", 0)
                lines.append(f"- **{name}** selected:")
                if ports > 0:
                    lines.append(f"  - Provides {ports} network ports (required: {requirements.network_ports})")
            
            elif category == "power":
                capacity = product.get("capacity_w", 0)
                lines.append(f"- **{name}** selected:")
                if capacity > 0:
                    total_system_power = total_power + requirements.estimated_power_w
                    lines.append(f"  - Provides {capacity}W capacity (total system power: {total_system_power}W)")
            
            elif category == "smart_home":
                lines.append(f"- **{name}** selected for home automation")
            
            elif category == "sensor":
                lines.append(f"- **{name}** selected for environmental monitoring")
            
            elif category == "security":
                lines.append(f"- **{name}** selected for security system")
            
            elif category == "storage":
                lines.append(f"- **{name}** selected for data storage")
        
        lines.append("")
        
        # Alternatives Considered
        lines.append("### Alternatives Considered")
        lines.append("")
        
        # Explain budget-based decisions
        if additional_info and additional_info.get("budget_limit", 0) > 0:
            if total_cost > additional_info["budget_limit"]:
                lines.append(f"- **Budget constraint**: Solution exceeds budget by ${total_cost - additional_info['budget_limit']:,}")
                lines.append("  - Consider removing optional features or selecting lower-tier products")
            else:
                lines.append(f"- **Budget optimization**: Solution optimized for ${additional_info['budget_limit']:,} budget")
                lines.append(f"  - ${additional_info['budget_limit'] - total_cost:,} remaining for additional features")
        
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
        total_system_power = total_power + requirements.estimated_power_w
        if total_system_power > 4000:
            lines.append("- Consider adding a second UPS for power redundancy")
        
        # Network optimization
        if requirements.network_ports > 24:
            lines.append("- Consider adding a second switch for network redundancy")
        
        # Cost optimization
        if requirements.device_count <= 10 and any(p.get("category") == "server" for p in products):
            lines.append("- Consider Edge Node instead of AI Server for small deployments to reduce cost")
        
        # Future expansion
        lines.append(f"- Plan for {requirements.device_count * 1.2:.0f} devices to allow 20% growth")
        
        # Smart home specific suggestions
        if additional_info and additional_info.get("project_type") == "smart_home":
            lines.append("- Consider adding temperature sensors for climate control")
            lines.append("- Add smart plugs for energy monitoring")
        
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
                                products: List[Dict[str, Any]],
                                validation: ValidationResult,
                                additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate JSON reasoning structure."""
        # Calculate totals
        total_power = sum(p.get("power_w", 0) for p in products)
        total_gpus = sum(p.get("gpu", 0) for p in products)
        total_ports = sum(p.get("ports", 0) for p in products)
        total_cost = sum(p.get("price", 0) for p in products)
        
        # Group products by category
        products_by_category = {}
        for product in products:
            category = product.get("category", "unknown")
            if category not in products_by_category:
                products_by_category[category] = []
            products_by_category[category].append(product)
        
        # Build JSON structure
        result = {
            "requirements": requirements.model_dump(),
            "selected_products": products,  # Already dictionaries
            "products_by_category": products_by_category,
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
        
        # Add additional info if available
        if additional_info:
            result["additional_info"] = additional_info
            
            # Add budget analysis
            if additional_info.get("budget_limit", 0) > 0:
                budget_utilization = (total_cost / additional_info["budget_limit"]) * 100
                result["budget_analysis"] = {
                    "budget_limit": additional_info["budget_limit"],
                    "total_cost": total_cost,
                    "remaining_budget": max(0, additional_info["budget_limit"] - total_cost),
                    "utilization_percentage": budget_utilization,
                    "is_within_budget": total_cost <= additional_info["budget_limit"]
                }
        
        return result
    
    def _get_product_selection_reasoning(self, requirements: StructuredRequirements,
                                        products: List[Dict[str, Any]]) -> List[str]:
        """Get reasoning for product selection."""
        reasoning = []
        
        for product in products:
            category = product.get("category", "")
            name = product.get("name", "")
            
            if category == "server":
                max_cameras = product.get("max_cameras", 0)
                gpu_count = product.get("gpu", 0)
                
                reason = f"{name}: "
                if max_cameras > 0:
                    reason += f"Supports {max_cameras} cameras (required: {requirements.device_count}), "
                if gpu_count > 0:
                    reason += f"has {gpu_count} GPUs (GPU required: {requirements.gpu_required})"
                reasoning.append(reason.strip(", "))
            
            elif category == "network":
                ports = product.get("ports", 0)
                reasoning.append(f"{name}: Provides {ports} ports (required: {requirements.network_ports})")
            
            elif category == "power":
                capacity = product.get("capacity_w", 0)
                reasoning.append(f"{name}: Provides {capacity}W power backup")
            
            elif category == "smart_home":
                reasoning.append(f"{name}: Selected for home automation system")
            
            elif category == "sensor":
                reasoning.append(f"{name}: Selected for monitoring and sensing")
            
            elif category == "security":
                reasoning.append(f"{name}: Selected for security system")
            
            elif category == "storage":
                reasoning.append(f"{name}: Selected for data storage")
        
        return reasoning
    
    def _get_rejected_alternatives(self, requirements: StructuredRequirements,
                                  products: List[Dict[str, Any]]) -> List[str]:
        """Get reasoning for rejected alternatives."""
        rejected = []
        
        # Check for server alternatives
        server_products = [p for p in products if p.get("category") == "server"]
        if server_products:
            selected_server = server_products[0]
            selected_max_cameras = selected_server.get("max_cameras", 0)
            selected_gpu = selected_server.get("gpu", 0)
            selected_price = selected_server.get("price", 0)
            
            # Compare with other potential servers
            potential_servers = [
                {"name": "AI Server X1", "max_cameras": 50, "gpu": 4, "price": 15000},
                {"name": "AI Server X2", "max_cameras": 120, "gpu": 8, "price": 28000},
                {"name": "Edge Node", "max_cameras": 10, "gpu": 1, "price": 4000}
            ]
            
            for server in potential_servers:
                if server["name"] != selected_server.get("name"):
                    if requirements.device_count > server["max_cameras"]:
                        rejected.append(
                            f"{server['name']}: Cannot support {requirements.device_count} cameras "
                            f"(max: {server['max_cameras']})"
                        )
                    elif requirements.gpu_required and server["gpu"] == 0:
                        rejected.append(
                            f"{server['name']}: No GPU support (GPU required)"
                        )
                    elif selected_max_cameras >= server["max_cameras"] and selected_price <= server["price"]:
                        rejected.append(
                            f"{server['name']}: {selected_server.get('name')} provides better value "
                            f"({selected_max_cameras} cameras vs {server['max_cameras']}, "
                            f"${selected_price} vs ${server['price']})"
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
                                     products: List[Dict[str, Any]],
                                     validation: ValidationResult) -> List[str]:
        """Get optimization suggestions."""
        suggestions = []
        
        # Calculate totals
        total_power = sum(p.get("power_w", 0) for p in products)
        total_system_power = total_power + requirements.estimated_power_w
        
        # Power optimization
        if total_system_power > 4000:
            suggestions.append("Add second UPS for power redundancy")
        
        # Network optimization
        if requirements.network_ports > 24:
            suggestions.append("Add second switch for network redundancy")
        
        # Cost optimization
        if requirements.device_count <= 10 and any(p.get("category") == "server" for p in products):
            suggestions.append("Consider Edge Node instead of AI Server for cost savings")
        
        # Future proofing
        suggestions.append(f"Plan for {int(requirements.device_count * 1.2)} devices (20% growth)")
        
        # Address validation warnings
        for warning in validation.warnings:
            if "insufficient" in warning.lower():
                suggestions.append(f"Address: {warning}")
        
        return suggestions
    
    def generate_intelligent_proposal(self, 
                                     analysis: Dict[str, Any],
                                     matching_results: Dict[str, Any],
                                     requirements: StructuredRequirements,
                                     validation: ValidationResult) -> Dict[str, Any]:
        """
        Generate intelligent proposal with detailed explanations.
        
        Args:
            analysis: Intelligent analysis from requirement analyzer
            matching_results: Results from intelligent product matching
            requirements: Structured requirements
            validation: Validation results
            
        Returns:
            Dictionary with intelligent proposal
        """
        # Combine all products
        all_products = (
            matching_results.get("exact_matches", []) +
            matching_results.get("required_components", []) +
            matching_results.get("optional_components", [])
        )
        
        # Generate explanations for each product
        explanations = self._generate_product_explanations(all_products, analysis, requirements)
        
        # Check if we have missing products
        missing_products = matching_results.get("missing_products", [])
        
        # Generate alert system questions if relevant
        alert_questions = self._generate_alert_system_questions(analysis, matching_results)
        
        # Build the proposal
        proposal = {
            "intelligent_analysis": analysis,
            "matching_results": matching_results,
            "requirements": requirements.model_dump(),
            "selected_products": all_products,
            "validation": validation.model_dump(),
            "explanations": explanations,
            "total_cost": matching_results.get("total_cost", 0),
            "has_missing_products": len(missing_products) > 0,
            "missing_products": missing_products,
            "alert_system_questions": alert_questions,
            "recommendation_summary": self._generate_recommendation_summary(analysis, matching_results, explanations)
        }
        
        # Add no-match response if needed
        if missing_products:
            proposal["no_match_response"] = self._generate_no_match_response(missing_products[0], analysis)
        
        return proposal
    
    def _generate_product_explanations(self, products: List[Dict[str, Any]], 
                                      analysis: Dict[str, Any],
                                      requirements: StructuredRequirements) -> List[Dict[str, Any]]:
        """
        Generate detailed explanations for each product.
        
        Args:
            products: List of products
            analysis: Intelligent analysis
            requirements: Structured requirements
            
        Returns:
            List of explanation dictionaries
        """
        explanations = []
        
        for product in products:
            explanation = {
                "product_name": product.get("name", ""),
                "product_price": product.get("price", 0),
                "product_category": product.get("category", ""),
                "why_fits": "",
                "problem_solves": "",
                "cheaper_alternatives": [],
                "explanation": ""
            }
            
            # Generate why it fits explanation
            explanation["why_fits"] = self._explain_why_product_fits(product, analysis, requirements)
            
            # Generate what problem it solves
            explanation["problem_solves"] = self._explain_problem_solved(product, analysis)
            
            # Find cheaper alternatives
            explanation["cheaper_alternatives"] = self._find_cheaper_alternatives(product)
            
            # Combine into full explanation
            explanation["explanation"] = self._format_product_explanation(explanation)
            
            explanations.append(explanation)
        
        return explanations
    
    def _explain_why_product_fits(self, product: Dict[str, Any], 
                                 analysis: Dict[str, Any],
                                 requirements: StructuredRequirements) -> str:
        """Explain why this product fits the user's request."""
        product_name = product.get("name", "")
        product_category = product.get("category", "")
        goal = analysis.get("goal", "")
        
        explanations = []
        
        # Check if it's a core product
        core_products = analysis.get("core_products", [])
        for core_product in core_products:
            if core_product.lower() in product_name.lower():
                explanations.append(f"Directly matches your request for a {core_product}")
                break
        
        # Check if it's a required component
        required_components = analysis.get("required_components", [])
        for component in required_components:
            if component.lower() in product_name.lower() or component.lower() in product.get("description", "").lower():
                explanations.append(f"Required for a complete system: {component}")
                break
        
        # Check if it's an optional component
        optional_components = analysis.get("optional_components", [])
        for component in optional_components:
            if component.lower() in product_name.lower():
                explanations.append(f"Optional enhancement: {component}")
                break
        
        # Generic explanations based on category
        if not explanations:
            if product_category == "sensor":
                explanations.append(f"Sensor for detecting {goal.split('detect')[-1] if 'detect' in goal else 'environmental conditions'}")
            elif product_category == "network":
                explanations.append("Provides connectivity for your system")
            elif product_category == "security":
                explanations.append("Enhances security and monitoring")
            elif product_category == "software":
                explanations.append("Software component for system management")
        
        return " ".join(explanations) if explanations else "Completes your system requirements"
    
    def _explain_problem_solved(self, product: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Explain what problem this product solves."""
        product_name = product.get("name", "")
        product_description = product.get("description", "")
        goal = analysis.get("goal", "")
        
        # Map product types to problems they solve
        problem_map = {
            "flood": "detects water presence and prevents flood damage",
            "water": "monitors water levels and detects leaks",
            "sensor": "monitors environmental conditions",
            "gateway": "connects devices to the internet for remote access",
            "siren": "provides audible alerts for immediate notification",
            "alert": "sends notifications to your phone or email",
            "camera": "provides visual monitoring and recording",
            "server": "processes data and manages the system",
            "network": "enables device communication and internet access",
            "power": "provides backup power during outages",
            "storage": "stores data and recordings"
        }
        
        # Check product name and description for keywords
        product_text = f"{product_name} {product_description}".lower()
        for keyword, problem in problem_map.items():
            if keyword in product_text:
                return f"Solves the problem of {problem}"
        
        # Check analysis goal
        if "detect" in goal.lower() and "sensor" in product_text:
            return f"Solves the problem of detecting {goal.split('detect')[-1].strip()}"
        if "alert" in goal.lower() and any(kw in product_text for kw in ["alert", "notification", "siren"]):
            return "Solves the problem of getting timely notifications"
        
        return "Addresses a key requirement of your system"
    
    def _find_cheaper_alternatives(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find cheaper alternatives for a product."""
        # This would need access to the full catalog
        # For now, return empty list - will be implemented in integration
        return []
    
    def _format_product_explanation(self, explanation: Dict[str, Any]) -> str:
        """Format the complete product explanation."""
        parts = []
        
        # Add main explanation
        if explanation["why_fits"]:
            parts.append(f"I recommend {explanation['product_name']} (${explanation['product_price']}) because {explanation['why_fits'].lower()}")
        
        # Add problem solving
        if explanation["problem_solves"]:
            parts.append(f"It solves the problem of {explanation['problem_solves'].lower()}")
        
        # Add cheaper alternatives if available
        if explanation["cheaper_alternatives"]:
            alt = explanation["cheaper_alternatives"][0]
            parts.append(f"If you prefer a cheaper option, {alt.get('name')} (${alt.get('price')}) {alt.get('difference', 'offers similar functionality')}.")
        
        return " ".join(parts)
    
    def _generate_alert_system_questions(self, analysis: Dict[str, Any], 
                                        matching_results: Dict[str, Any]) -> List[str]:
        """
        Generate alert system questions based on analysis.
        
        Args:
            analysis: Intelligent analysis
            matching_results: Product matching results
            
        Returns:
            List of questions to ask about alert preferences
        """
        questions = []
        goal = analysis.get("goal", "").lower()
        
        # Check if this is an alert system request
        if any(word in goal for word in ["alert", "notify", "alarm", "warning"]):
            questions.append("Would you like SMS/email alerts, audible siren, or both?")
        
        # Check if we have sensor but no notification method
        has_sensor = any("sensor" in p.get("name", "").lower() for p in matching_results.get("exact_matches", []))
        has_notification = any(word in str(matching_results).lower() for word in ["alert", "notification", "siren", "gateway"])
        
        if has_sensor and not has_notification:
            questions.append("How would you like to receive alerts? (SMS, email, app notification, audible siren)")
        
        # Check for missing notification components
        required_components = analysis.get("required_components", [])
        if any("notification" in comp.lower() for comp in required_components):
            if not any(word in str(matching_results).lower() for word in ["alert", "notification"]):
                questions.append("What type of notification system do you prefer?")
        
        return questions
    
    def _generate_recommendation_summary(self, analysis: Dict[str, Any],
                                        matching_results: Dict[str, Any],
                                        explanations: List[Dict[str, Any]]) -> str:
        """Generate a summary of recommendations."""
        total_cost = matching_results.get("total_cost", 0)
        exact_matches = matching_results.get("exact_matches", [])
        required_components = matching_results.get("required_components", [])
        missing_products = matching_results.get("missing_products", [])
        
        summary_parts = []
        
        # Start with goal
        goal = analysis.get("goal", "")
        if goal:
            summary_parts.append(f"Based on your goal to {goal}:")
        
        # Add exact matches
        if exact_matches:
            match_names = [p.get("name") for p in exact_matches]
            summary_parts.append(f"• Found exact matches: {', '.join(match_names)}")
        
        # Add required components
        if required_components:
            comp_names = [p.get("name") for p in required_components]
            summary_parts.append(f"• Added required components: {', '.join(comp_names)}")
        
        # Add missing products warning
        if missing_products:
            summary_parts.append(f"• Note: Could not find: {', '.join(missing_products)}")
        
        # Add total cost
        summary_parts.append(f"• Total estimated cost: ${total_cost:,}")
        
        # Add key explanations
        if explanations:
            key_explanation = explanations[0].get("explanation", "") if explanations else ""
            if key_explanation:
                summary_parts.append(f"• Key recommendation: {key_explanation}")
        
        return "\n".join(summary_parts)
    
    def _generate_no_match_response(self, product_name: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response when no exact match is found."""
        return {
            "message": f"I don't have an exact match for '{product_name}' in my catalog.",
            "options": [
                "A) Suggest the closest alternative",
                "B) List specifications so I can help design a custom solution",
                f"C) Show you what I have in {analysis.get('core_products', ['relevant categories'])[0]}"
            ],
            "suggested_action": "Please clarify your requirements or ask for alternatives."
        }