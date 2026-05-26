"""
Product Retrieval Agent for AutoSE Platform.

This module implements Agent 2 that matches requirements against the hardcoded
product catalog.
"""

from typing import List, Optional
from .models import Product, StructuredRequirements


class ProductRetriever:
    """Agent 2: Retrieves matching products from the hardcoded catalog."""
    
    def __init__(self):
        """Initialize the product retriever with hardcoded catalog."""
        self.catalog = self._load_catalog()
    
    def _load_catalog(self) -> List[Product]:
        """Load the hardcoded product catalog."""
        return [
            # AI Server X1: 800W, 4xGPU, $15,000, max cameras: 50
            Product(
                name="AI Server X1",
                power_w=800,
                gpu_count=4,
                price=15000,
                max_cameras=50,
                port_count=0,
                capacity_w=0
            ),
            # AI Server X2: 1500W, 8xGPU, $28,000, max cameras: 120
            Product(
                name="AI Server X2",
                power_w=1500,
                gpu_count=8,
                price=28000,
                max_cameras=120,
                port_count=0,
                capacity_w=0
            ),
            # Edge Node: 150W, 1xGPU, $4,000, max cameras: 10
            Product(
                name="Edge Node",
                power_w=150,
                gpu_count=1,
                price=4000,
                max_cameras=10,
                port_count=0,
                capacity_w=0
            ),
            # UPS 5000W: 5000W capacity
            Product(
                name="UPS 5000W",
                power_w=0,
                gpu_count=0,
                price=2000,
                max_cameras=0,
                port_count=0,
                capacity_w=5000
            ),
            # Switch 48P: 400W, 48 ports
            Product(
                name="Switch 48P",
                power_w=400,
                gpu_count=0,
                price=1500,
                max_cameras=0,
                port_count=48,
                capacity_w=0
            )
        ]
    
    async def match(self, requirements: StructuredRequirements) -> List[Product]:
        """
        Match requirements against product catalog.
        
        Args:
            requirements: Structured requirements to match
            
        Returns:
            List of matching products, sorted by relevance
        """
        # Filter products based on requirements
        matching_products = []
        
        for product in self.catalog:
            if self._is_product_relevant(product, requirements):
                matching_products.append(product)
        
        # Sort by relevance:
        # 1. Products that can support camera count (descending max_cameras)
        # 2. Products that match GPU requirements
        # 3. Lower price for similar capabilities
        matching_products.sort(
            key=lambda p: (
                -p.max_cameras if p.max_cameras > 0 else 0,  # Higher camera capacity first
                -int(self._meets_gpu_requirements(p, requirements)),  # GPU match
                p.price  # Lower price for similar capabilities
            )
        )
        
        # Always include UPS if power is significant
        if requirements.estimated_power_w > 1000:
            ups = self._get_ups_product()
            if ups and ups not in matching_products:
                matching_products.append(ups)
        
        # Always include switch if network ports are needed
        if requirements.network_ports > 0:
            switch = self._get_switch_product(requirements.network_ports)
            if switch and switch not in matching_products:
                matching_products.append(switch)
        
        return matching_products
    
    def _is_product_relevant(self, product: Product, requirements: StructuredRequirements) -> bool:
        """Check if a product is relevant to the requirements."""
        # Skip UPS and Switch for primary matching (they're added separately)
        if product.name in ["UPS 5000W", "Switch 48P"]:
            return False
        
        # Check camera support
        if product.max_cameras > 0 and not product.can_support_cameras(requirements.device_count):
            return False
        
        # Check GPU requirements
        if requirements.gpu_required and product.gpu_count == 0:
            return False
        
        # For AI servers, they're always relevant if they support cameras
        # Edge nodes are only relevant for small deployments
        if product.name == "Edge Node" and requirements.device_count > 20:
            return False
        
        return True
    
    def _meets_gpu_requirements(self, product: Product, requirements: StructuredRequirements) -> bool:
        """Check if product meets GPU requirements."""
        if not requirements.gpu_required:
            return True
        
        return product.gpu_count > 0
    
    def _get_ups_product(self) -> Optional[Product]:
        """Get the UPS product from catalog."""
        for product in self.catalog:
            if product.name == "UPS 5000W":
                return product
        return None
    
    def _get_switch_product(self, required_ports: int) -> Optional[Product]:
        """Get appropriate switch product based on port requirements."""
        for product in self.catalog:
            if product.name == "Switch 48P" and product.port_count >= required_ports:
                return product
        return None
    
    def get_catalog(self) -> List[Product]:
        """Get the complete product catalog."""
        return self.catalog.copy()
    
    def get_product_by_name(self, name: str) -> Optional[Product]:
        """Get a product by its name."""
        for product in self.catalog:
            if product.name == name:
                return product
        return None