"""
Product Retrieval Agent for AutoSE Platform.

This module implements Agent 2 that matches requirements against the dynamic
product catalog loaded from JSON.
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from .models import StructuredRequirements


class ProductRetriever:
    """Agent 2: Retrieves matching products from the dynamic catalog."""
    
    def __init__(self):
        """Initialize the product retriever with JSON catalog."""
        self.catalog = self._load_catalog()
        self.categories = self._extract_categories()
    
    def _load_catalog(self) -> List[Dict[str, Any]]:
        """Load product catalog from JSON file."""
        try:
            # Try to load from project root
            catalog_path = Path(__file__).parent.parent.parent / "product_catalog.json"
            if not catalog_path.exists():
                # Try alternative path
                catalog_path = Path("product_catalog.json")
                if not catalog_path.exists():
                    raise FileNotFoundError("product_catalog.json not found in project root")
            
            with open(catalog_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get("products", [])
            
        except Exception as e:
            print(f"Warning: Failed to load product catalog: {e}")
            print("Using fallback catalog...")
            return self._load_fallback_catalog()
    
    def _load_fallback_catalog(self) -> List[Dict[str, Any]]:
        """Load fallback catalog if JSON file is not available."""
        # Create dictionaries instead of Product objects
        return [
            {"id": "server_x1", "name": "AI Server X1", "category": "server", "price": 15000, "power_w": 800, "gpu": 4, "max_cameras": 50, "port_count": 0, "capacity_w": 0},
            {"id": "server_x2", "name": "AI Server X2", "category": "server", "price": 28000, "power_w": 1500, "gpu": 8, "max_cameras": 120, "port_count": 0, "capacity_w": 0},
            {"id": "edge_node", "name": "Edge Node", "category": "server", "price": 4000, "power_w": 150, "gpu": 1, "max_cameras": 10, "port_count": 0, "capacity_w": 0},
            {"id": "switch48", "name": "Switch 48P", "category": "network", "price": 2000, "power_w": 400, "ports": 48, "port_count": 48},
            {"id": "switch24", "name": "Switch 24P", "category": "network", "price": 1200, "power_w": 200, "ports": 24},
            {"id": "router", "name": "Enterprise Router", "category": "network", "price": 800, "power_w": 50, "ports": 4},
            {"id": "ups5k", "name": "UPS 5000W", "category": "power", "price": 3000, "capacity_w": 5000},
            {"id": "ups3k", "name": "UPS 3000W", "category": "power", "price": 1800, "capacity_w": 3000},
            {"id": "smart_panel", "name": "Smart Control Panel", "category": "smart_home", "price": 500, "power_w": 10},
            {"id": "light_ctrl", "name": "Smart Light Controller", "category": "smart_home", "price": 120, "power_w": 5},
            {"id": "smart_plug", "name": "Smart Plug", "category": "smart_home", "price": 30, "power_w": 1},
            {"id": "motion_sensor", "name": "Motion Sensor", "category": "sensor", "price": 80, "power_w": 2},
            {"id": "door_sensor", "name": "Door Sensor", "category": "sensor", "price": 40, "power_w": 1},
            {"id": "temp_sensor", "name": "Temperature Sensor", "category": "sensor", "price": 60, "power_w": 1},
            {"id": "nvr", "name": "Network Video Recorder", "category": "security", "price": 2000, "power_w": 150, "max_cameras": 64},
            {"id": "camera_bullet", "name": "Bullet Camera", "category": "security", "price": 300, "power_w": 10},
            {"id": "nas", "name": "NAS Storage", "category": "storage", "price": 800, "power_w": 60}
        ]
    
    def _extract_categories(self) -> List[str]:
        """Extract unique categories from catalog."""
        categories = set()
        for product in self.catalog:
            # All products are now dictionaries
            categories.add(product.get("category", "unknown"))
        return sorted(list(categories))
    
    async def match(self, requirements: StructuredRequirements, 
                   project_type: str = None,
                   budget_limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Match requirements against product catalog.
        
        Args:
            requirements: Structured requirements to match
            project_type: Type of project (security_system, smart_home, etc.)
            budget_limit: Optional budget limit for optimization
            
        Returns:
            List of matching products as dictionaries, sorted by relevance
        """
        # Get category-based recommendations
        if project_type:
            matching_products = self._match_by_project_type(project_type, requirements)
        else:
            matching_products = self._match_by_requirements(requirements)
        
        # Apply budget optimization if specified
        if budget_limit:
            matching_products = self._optimize_for_budget(matching_products, budget_limit)
        
        return matching_products
    
    def generate_alternative_solutions(self, current_solution: List[Dict[str, Any]], 
                                      constraints: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate alternative solutions based on constraints.
        
        Args:
            current_solution: Current list of products
            constraints: Dictionary with constraints (budget_limit, device_count, etc.)
            
        Returns:
            Dictionary with alternative solutions: economy, balanced, performance
        """
        alternatives = {
            "economy": [],
            "balanced": [],
            "performance": []
        }
        
        # Calculate current totals
        current_cost = sum(p.get("price", 0) for p in current_solution)
        budget_limit = constraints.get("budget_limit", 0)
        device_count = constraints.get("device_count")
        
        # If no specific constraints, create variations based on current solution
        if budget_limit == 0 and device_count is None:
            # Create economy version (cheaper alternatives)
            alternatives["economy"] = self._create_economy_version(current_solution)
            
            # Balanced version is the current solution
            alternatives["balanced"] = current_solution.copy()
            
            # Create performance version (upgraded alternatives)
            alternatives["performance"] = self._create_performance_version(current_solution)
        
        else:
            # Apply budget constraint
            if budget_limit > 0:
                alternatives["economy"] = self._optimize_for_budget(current_solution, budget_limit)
                alternatives["balanced"] = self._create_balanced_version(current_solution, budget_limit)
                alternatives["performance"] = self._create_performance_within_budget(current_solution, budget_limit)
            
            # Apply device count constraint
            if device_count is not None:
                # Adjust solution for fewer devices
                alternatives["economy"] = self._adjust_for_fewer_devices(current_solution, device_count)
                alternatives["balanced"] = self._adjust_balanced_for_devices(current_solution, device_count)
                alternatives["performance"] = self._adjust_performance_for_devices(current_solution, device_count)
        
        return alternatives
    
    def _create_economy_version(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create economy version with cheaper alternatives."""
        economy_products = []
        
        for product in products:
            category = product.get("category", "")
            name = product.get("name", "")
            
            # Find cheaper alternatives for each product
            if category == "server":
                # For servers, try to find cheaper options
                server_alternatives = self.get_products_by_category("server")
                server_alternatives.sort(key=lambda p: p.get("price", 0))
                
                # Find the cheapest server that still meets basic requirements
                if server_alternatives:
                    # Skip if already the cheapest
                    if product.get("price", 0) > server_alternatives[0].get("price", 0):
                        economy_products.append(server_alternatives[0])
                    else:
                        economy_products.append(product)
            
            elif category == "network":
                # For network, use smaller switch if possible
                network_alternatives = self.get_products_by_category("network")
                network_alternatives.sort(key=lambda p: p.get("price", 0))
                
                if network_alternatives:
                    # Skip if already the cheapest
                    if product.get("price", 0) > network_alternatives[0].get("price", 0):
                        economy_products.append(network_alternatives[0])
                    else:
                        economy_products.append(product)
            
            elif category == "power":
                # For power, use smaller UPS if possible
                power_alternatives = self.get_products_by_category("power")
                power_alternatives.sort(key=lambda p: p.get("price", 0))
                
                if power_alternatives:
                    # Skip if already the cheapest
                    if product.get("price", 0) > power_alternatives[0].get("price", 0):
                        economy_products.append(power_alternatives[0])
                    else:
                        economy_products.append(product)
            
            else:
                # For other categories, keep as is or find cheaper
                category_alternatives = self.get_products_by_category(category)
                if category_alternatives:
                    category_alternatives.sort(key=lambda p: p.get("price", 0))
                    if product.get("price", 0) > category_alternatives[0].get("price", 0):
                        economy_products.append(category_alternatives[0])
                    else:
                        economy_products.append(product)
                else:
                    economy_products.append(product)
        
        return economy_products
    
    def _create_performance_version(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create performance version with upgraded alternatives."""
        performance_products = []
        
        for product in products:
            category = product.get("category", "")
            name = product.get("name", "")
            
            # Find upgraded alternatives for each product
            if category == "server":
                # For servers, try to find more powerful options
                server_alternatives = self.get_products_by_category("server")
                server_alternatives.sort(key=lambda p: p.get("price", 0), reverse=True)
                
                # Find the most powerful server
                if server_alternatives:
                    # Skip if already the most expensive
                    if product.get("price", 0) < server_alternatives[0].get("price", 0):
                        performance_products.append(server_alternatives[0])
                    else:
                        performance_products.append(product)
            
            elif category == "network":
                # For network, use larger switch
                network_alternatives = self.get_products_by_category("network")
                network_alternatives.sort(key=lambda p: p.get("price", 0), reverse=True)
                
                if network_alternatives:
                    # Skip if already the most expensive
                    if product.get("price", 0) < network_alternatives[0].get("price", 0):
                        performance_products.append(network_alternatives[0])
                    else:
                        performance_products.append(product)
            
            elif category == "power":
                # For power, use larger UPS
                power_alternatives = self.get_products_by_category("power")
                power_alternatives.sort(key=lambda p: p.get("price", 0), reverse=True)
                
                if power_alternatives:
                    # Skip if already the most expensive
                    if product.get("price", 0) < power_alternatives[0].get("price", 0):
                        performance_products.append(power_alternatives[0])
                    else:
                        performance_products.append(product)
            
            else:
                # For other categories, keep as is
                performance_products.append(product)
        
        return performance_products
    
    def _create_balanced_version(self, products: List[Dict[str, Any]], budget_limit: int) -> List[Dict[str, Any]]:
        """Create balanced version within budget."""
        # Start with economy version
        balanced_products = self._create_economy_version(products)
        
        # Calculate total cost
        total_cost = sum(p.get("price", 0) for p in balanced_products)
        
        # If we have budget room, upgrade some components
        if total_cost < budget_limit * 0.8:  # If using less than 80% of budget
            budget_room = budget_limit - total_cost
            
            # Try to upgrade server first
            for i, product in enumerate(balanced_products):
                if product.get("category") == "server":
                    server_alternatives = self.get_products_by_category("server")
                    server_alternatives.sort(key=lambda p: p.get("price", 0))
                    
                    # Find a better server that fits within remaining budget
                    for alternative in server_alternatives:
                        if alternative.get("price", 0) > product.get("price", 0) and \
                           alternative.get("price", 0) - product.get("price", 0) <= budget_room:
                            balanced_products[i] = alternative
                            budget_room -= (alternative.get("price", 0) - product.get("price", 0))
                            break
        
        return balanced_products
    
    def _create_performance_within_budget(self, products: List[Dict[str, Any]], budget_limit: int) -> List[Dict[str, Any]]:
        """Create performance version within budget."""
        # Start with current solution
        performance_products = products.copy()
        total_cost = sum(p.get("price", 0) for p in performance_products)
        
        # If over budget, downgrade non-essential components
        if total_cost > budget_limit:
            # Sort products by price (descending) to downgrade most expensive first
            performance_products.sort(key=lambda p: p.get("price", 0), reverse=True)
            
            for i, product in enumerate(performance_products):
                if total_cost <= budget_limit:
                    break
                
                category = product.get("category", "")
                if category in ["sensor", "smart_home"]:  # Downgrade non-essential first
                    category_alternatives = self.get_products_by_category(category)
                    if category_alternatives:
                        category_alternatives.sort(key=lambda p: p.get("price", 0))
                        if category_alternatives[0].get("price", 0) < product.get("price", 0):
                            old_price = product.get("price", 0)
                            performance_products[i] = category_alternatives[0]
                            total_cost -= (old_price - category_alternatives[0].get("price", 0))
        
        return performance_products
    
    def _adjust_for_fewer_devices(self, products: List[Dict[str, Any]], device_count: int) -> List[Dict[str, Any]]:
        """Adjust solution for fewer devices."""
        adjusted_products = []
        
        for product in products:
            category = product.get("category", "")
            max_cameras = product.get("max_cameras", 0)
            
            # If this is a server and it's overkill for the device count, downgrade
            if category == "server" and max_cameras > device_count * 2:  # If server supports more than 2x needed
                server_alternatives = self.get_products_by_category("server")
                server_alternatives.sort(key=lambda p: p.get("price", 0))
                
                # Find a server that better matches the device count
                for alternative in server_alternatives:
                    alt_max_cameras = alternative.get("max_cameras", 0)
                    if device_count <= alt_max_cameras <= device_count * 1.5:  # Reasonable match
                        adjusted_products.append(alternative)
                        break
                else:
                    # Keep original if no better match found
                    adjusted_products.append(product)
            else:
                adjusted_products.append(product)
        
        return adjusted_products
    
    def _adjust_balanced_for_devices(self, products: List[Dict[str, Any]], device_count: int) -> List[Dict[str, Any]]:
        """Create balanced adjustment for device count."""
        # Start with economy adjustment
        adjusted_products = self._adjust_for_fewer_devices(products, device_count)
        
        # Ensure we have all necessary categories
        required_categories = set(p.get("category") for p in products)
        current_categories = set(p.get("category") for p in adjusted_products)
        
        # Add missing categories from original
        for product in products:
            if product.get("category") not in current_categories:
                adjusted_products.append(product)
        
        return adjusted_products
    
    def _adjust_performance_for_devices(self, products: List[Dict[str, Any]], device_count: int) -> List[Dict[str, Any]]:
        """Create performance adjustment for device count."""
        # Keep original but ensure server can handle the devices
        adjusted_products = products.copy()
        
        for i, product in enumerate(adjusted_products):
            if product.get("category") == "server":
                max_cameras = product.get("max_cameras", 0)
                if max_cameras < device_count:
                    # Need to upgrade server
                    server_alternatives = self.get_products_by_category("server")
                    server_alternatives.sort(key=lambda p: p.get("max_cameras", 0), reverse=True)
                    
                    for alternative in server_alternatives:
                        if alternative.get("max_cameras", 0) >= device_count:
                            adjusted_products[i] = alternative
                            break
        
        return adjusted_products
    
    def _match_by_requirements(self, requirements: StructuredRequirements) -> List[Dict[str, Any]]:
        """Match products based on traditional requirements."""
        matching_products = []
        
        for product in self.catalog:
            if self._is_product_relevant(product, requirements):
                matching_products.append(product)
        
        # Sort by relevance
        matching_products.sort(
            key=lambda p: (
                -p.get("max_cameras", 0) if p.get("max_cameras", 0) > 0 else 0,
                -p.get("gpu", p.get("gpu_count", 0)) if requirements.gpu_required else 0,
                p.get("price", 0)
            )
        )
        
        # Add power backup if needed
        if requirements.estimated_power_w > 1000:
            ups = self._get_product_by_category("power")
            if ups and ups not in matching_products:
                matching_products.append(ups)
        
        # Add network equipment if needed
        if requirements.network_ports > 0:
            network_products = self._get_network_products(requirements.network_ports)
            for network_product in network_products:
                if network_product not in matching_products:
                    matching_products.append(network_product)
        
        return matching_products
    
    def _match_by_project_type(self, project_type: str, requirements: StructuredRequirements) -> List[Dict[str, Any]]:
        """Match products based on project type."""
        category_mapping = {
            "security_system": ["server", "security", "network", "power", "storage"],
            "smart_home": ["smart_home", "sensor", "network", "power"],
            "office_network": ["network", "server", "power", "storage"],
            "data_center": ["server", "network", "power", "storage"],
            "retail_surveillance": ["security", "server", "network", "storage"]
        }
        
        categories = category_mapping.get(project_type, [])
        matching_products = []
        
        for product in self.catalog:
            if product.get("category") in categories:
                # Additional filtering based on requirements
                if self._is_product_suitable_for_project(product, project_type, requirements):
                    matching_products.append(product)
        
        # Ensure we have at least one product from each required category
        for category in categories:
            if not any(p.get("category") == category for p in matching_products):
                category_product = self._get_product_by_category(category)
                if category_product:
                    matching_products.append(category_product)
        
        return matching_products
    
    def _is_product_relevant(self, product: Dict[str, Any], requirements: StructuredRequirements) -> bool:
        """Check if a product is relevant to the requirements."""
        category = product.get("category", "")
        
        # Skip power and network for primary matching (they're added separately)
        if category in ["power", "network"]:
            return False
        
        # Check camera support for servers/security
        if category in ["server", "security"]:
            max_cameras = product.get("max_cameras", 0)
            if max_cameras > 0 and max_cameras < requirements.device_count:
                return False
        
        # Check GPU requirements
        if requirements.gpu_required and category == "server":
            gpu_count = product.get("gpu", 0)
            if gpu_count == 0:
                return False
        
        # Edge nodes only for small deployments
        if product.get("name") == "Edge Node" and requirements.device_count > 20:
            return False
        
        return True
    
    def _is_product_suitable_for_project(self, product: Dict[str, Any], project_type: str, 
                                        requirements: StructuredRequirements) -> bool:
        """Check if product is suitable for specific project type."""
        category = product.get("category", "")
        
        if project_type == "security_system":
            if category == "server":
                max_cameras = product.get("max_cameras", 0)
                return max_cameras >= requirements.device_count
            elif category == "security":
                return True  # All security products are relevant
        
        elif project_type == "smart_home":
            if category == "smart_home":
                return True  # All smart home products are relevant
            elif category == "sensor":
                return True  # All sensors are relevant
        
        elif project_type == "office_network":
            if category == "network":
                ports = product.get("ports", 0)
                return ports >= requirements.network_ports if requirements.network_ports > 0 else True
        
        return True
    
    def _get_product_by_category(self, category: str) -> Optional[Dict[str, Any]]:
        """Get a representative product from a category."""
        for product in self.catalog:
            if product.get("category") == category:
                return product
        return None
    
    def _get_network_products(self, required_ports: int) -> List[Dict[str, Any]]:
        """Get appropriate network products based on port requirements."""
        network_products = []
        
        # Sort network products by port count
        network_items = [p for p in self.catalog if p.get("category") == "network"]
        network_items.sort(key=lambda p: p.get("ports", 0), reverse=True)
        
        # Select the smallest switch that meets requirements
        for product in network_items:
            if product.get("ports", 0) >= required_ports:
                network_products.append(product)
                break
        
        # Always include a router for network connectivity
        router = next((p for p in self.catalog if p.get("name") == "Enterprise Router"), None)
        if router and router not in network_products:
            network_products.append(router)
        
        return network_products
    
    def _optimize_for_budget(self, products: List[Dict[str, Any]], budget_limit: int) -> List[Dict[str, Any]]:
        """Optimize product selection for budget constraints."""
        total_cost = sum(p.get("price", 0) for p in products)
        
        if total_cost <= budget_limit:
            return products
        
        # Try to reduce cost by selecting cheaper alternatives
        optimized_products = []
        remaining_budget = budget_limit
        
        # Sort products by cost-effectiveness (price per feature)
        products_with_score = []
        for product in products:
            score = self._calculate_cost_effectiveness(product)
            products_with_score.append((product, score))
        
        products_with_score.sort(key=lambda x: x[1])  # Lower score = more cost-effective
        
        for product, _ in products_with_score:
            price = product.get("price", 0)
            if price <= remaining_budget:
                optimized_products.append(product)
                remaining_budget -= price
            else:
                # Try to find cheaper alternative
                alternative = self._find_cheaper_alternative(product, remaining_budget)
                if alternative:
                    optimized_products.append(alternative)
                    remaining_budget -= alternative.get("price", 0)
        
        return optimized_products
    
    def _calculate_cost_effectiveness(self, product: Dict[str, Any]) -> float:
        """Calculate cost-effectiveness score (lower is better)."""
        price = product.get("price", 1)
        features = 0
        
        # Count features
        if product.get("max_cameras", 0) > 0:
            features += product.get("max_cameras", 0) / 10
        if product.get("gpu", 0) > 0:
            features += product.get("gpu", 0) * 1000
        if product.get("ports", 0) > 0:
            features += product.get("ports", 0) * 10
        if product.get("capacity_w", 0) > 0:
            features += product.get("capacity_w", 0) / 100
        
        return price / max(features, 1)
    
    def _find_cheaper_alternative(self, product: Dict[str, Any], max_price: int) -> Optional[Dict[str, Any]]:
        """Find cheaper alternative for a product."""
        category = product.get("category", "")
        alternatives = [p for p in self.catalog if p.get("category") == category and p.get("price", 0) <= max_price]
        
        if alternatives:
            # Return the most feature-rich alternative within budget
            alternatives.sort(key=lambda p: (
                p.get("max_cameras", 0),
                p.get("gpu", 0),
                p.get("ports", 0),
                p.get("capacity_w", 0)
            ), reverse=True)
            return alternatives[0]
        
        return None
    
    def get_catalog(self) -> List[Dict[str, Any]]:
        """Get the complete product catalog."""
        return self.catalog.copy()
    
    def get_categories(self) -> List[str]:
        """Get list of available product categories."""
        return self.categories.copy()
    
    def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all products in a specific category."""
        return [p for p in self.catalog if p.get("category") == category]
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a product by its ID."""
        for product in self.catalog:
            if product.get("id") == product_id:
                return product
        return None
    
    def get_product_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a product by its name."""
        for product in self.catalog:
            if product.get("name") == name:
                return product
        return None
    
    def find_exact_match(self, product_name: str) -> Optional[Dict[str, Any]]:
        """
        Find exact match for a product name in the catalog.
        
        Args:
            product_name: Name of product to find
            
        Returns:
            Product dictionary if exact match found, None otherwise
        """
        # Try exact name match first
        for product in self.catalog:
            if product.get("name", "").lower() == product_name.lower():
                return product
        
        # Try partial name match
        for product in self.catalog:
            if product_name.lower() in product.get("name", "").lower():
                return product
        
        # Try keyword matching in description
        for product in self.catalog:
            description = product.get("description", "").lower()
            if product_name.lower() in description:
                return product
        
        return None
    
    def find_semantic_matches(self, product_type: str, category: str = None) -> List[Dict[str, Any]]:
        """
        Find semantic matches for a product type.
        
        Args:
            product_type: Type of product to find
            category: Optional category to filter by
            
        Returns:
            List of matching products
        """
        matches = []
        product_type_lower = product_type.lower()
        
        for product in self.catalog:
            # Skip if category filter doesn't match
            if category and product.get("category", "").lower() != category.lower():
                continue
            
            # Check name
            name = product.get("name", "").lower()
            if product_type_lower in name:
                matches.append(product)
                continue
            
            # Check description
            description = product.get("description", "").lower()
            if product_type_lower in description:
                matches.append(product)
                continue
            
            # Check category
            product_category = product.get("category", "").lower()
            if product_type_lower in product_category:
                matches.append(product)
                continue
        
        return matches
    
    def get_products_in_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all products in a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of products in the category
        """
        return [p for p in self.catalog if p.get("category", "").lower() == category.lower()]
    
    def generate_no_match_response(self, product_name: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate response when no exact match is found.
        
        Args:
            product_name: Product name that was requested
            analysis: Intelligent analysis from requirement analyzer
            
        Returns:
            Dictionary with response options
        """
        response = {
            "no_exact_match": True,
            "requested_product": product_name,
            "message": f"I don't have an exact match for '{product_name}' in my catalog.",
            "options": []
        }
        
        # Add option A: Suggest closest alternative
        closest_alternative = self._find_closest_alternative(product_name, analysis)
        if closest_alternative:
            response["options"].append({
                "type": "closest_alternative",
                "product": closest_alternative,
                "description": f"Closest alternative: {closest_alternative.get('name')} (${closest_alternative.get('price')})"
            })
        
        # Add option B: List specifications for custom solution
        response["options"].append({
            "type": "custom_solution",
            "description": "List specifications so I can help design a custom solution",
            "questions": analysis.get("missing_info", [])
        })
        
        # Add option C: Show products in relevant category
        relevant_categories = self._get_relevant_categories(analysis)
        for category in relevant_categories:
            category_products = self.get_products_in_category(category)
            if category_products:
                response["options"].append({
                    "type": "category_products",
                    "category": category,
                    "products": category_products[:3],  # Show top 3
                    "description": f"Show you what I have in {category}"
                })
        
        return response
    
    def _find_closest_alternative(self, product_name: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find the closest alternative to a requested product.
        
        Args:
            product_name: Requested product name
            analysis: Intelligent analysis
            
        Returns:
            Closest alternative product or None
        """
        # Get core products from analysis
        core_products = analysis.get("core_products", [])
        
        # Try to find matches for core product types
        for core_product in core_products:
            matches = self.find_semantic_matches(core_product)
            if matches:
                # Return the cheapest match
                matches.sort(key=lambda p: p.get("price", 0))
                return matches[0]
        
        # If no core product matches, try required components
        required_components = analysis.get("required_components", [])
        for component in required_components:
            matches = self.find_semantic_matches(component)
            if matches:
                matches.sort(key=lambda p: p.get("price", 0))
                return matches[0]
        
        return None
    
    def _get_relevant_categories(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Get relevant categories based on analysis.
        
        Args:
            analysis: Intelligent analysis
            
        Returns:
            List of relevant category names
        """
        categories = set()
        
        # Map product types to categories
        category_mapping = {
            "sensor": "sensor",
            "gateway": "network",
            "notification": "software",
            "siren": "security",
            "camera": "security",
            "server": "server",
            "network": "network",
            "storage": "storage",
            "power": "power"
        }
        
        # Add categories for core products
        for product_type in analysis.get("core_products", []):
            for key, category in category_mapping.items():
                if key in product_type.lower():
                    categories.add(category)
        
        # Add categories for required components
        for component in analysis.get("required_components", []):
            for key, category in category_mapping.items():
                if key in component.lower():
                    categories.add(category)
        
        return list(categories)
    
    def match_intelligently(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match products intelligently based on analysis.
        
        Args:
            analysis: Intelligent analysis from requirement analyzer
            
        Returns:
            Dictionary with matching results
        """
        result = {
            "analysis": analysis,
            "exact_matches": [],
            "required_components": [],
            "optional_components": [],
            "missing_products": [],
            "total_cost": 0,
            "explanations": []
        }
        
        # Try to find exact matches for core products
        core_products = analysis.get("core_products", [])
        for product_type in core_products:
            match = self.find_exact_match(product_type)
            if match:
                result["exact_matches"].append(match)
                result["explanations"].append(
                    f"Found exact match: {match.get('name')} (${match.get('price')}) - {match.get('description', '')}"
                )
            else:
                result["missing_products"].append(product_type)
        
        # Find required components
        required_components = analysis.get("required_components", [])
        for component in required_components:
            match = self.find_exact_match(component)
            if match:
                result["required_components"].append(match)
                result["explanations"].append(
                    f"Required component: {match.get('name')} (${match.get('price')}) - {match.get('description', '')}"
                )
            else:
                # Try semantic match
                matches = self.find_semantic_matches(component)
                if matches:
                    # Pick the most relevant match
                    matches.sort(key=lambda p: p.get("price", 0))
                    result["required_components"].append(matches[0])
                    result["explanations"].append(
                        f"Found similar component: {matches[0].get('name')} (${matches[0].get('price')}) - {matches[0].get('description', '')}"
                    )
                else:
                    result["missing_products"].append(component)
        
        # Find optional components
        optional_components = analysis.get("optional_components", [])
        for component in optional_components:
            match = self.find_exact_match(component)
            if match:
                result["optional_components"].append(match)
                result["explanations"].append(
                    f"Optional component: {match.get('name')} (${match.get('price')}) - {match.get('description', '')}"
                )
        
        # Calculate total cost
        all_products = result["exact_matches"] + result["required_components"] + result["optional_components"]
        result["total_cost"] = sum(p.get("price", 0) for p in all_products)
        
        return result