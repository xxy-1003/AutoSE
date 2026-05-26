"""
Streamlit Frontend for AutoSE Platform.

Simple chat-style interface for the AutoSE Platform.
"""

import streamlit as st
import requests
import json
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="AutoSE Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #FF9800;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #FFEBEE;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #F44336;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #2196F3;
        margin: 1rem 0;
    }
    .product-card {
        background-color: #FAFAFA;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E0E0E0;
        margin: 0.5rem 0;
    }
    .stButton button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
    }
    .stTextArea textarea {
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# App title
st.markdown('<h1 class="main-header">🤖 AutoSE Platform</h1>', unsafe_allow_html=True)
st.markdown("""
**Autonomous Solution Engineering Platform**  
Multi-agent system for enterprise solution engineering that validates compatibility, 
optimizes infrastructure decisions, and generates proposals automatically.
""")

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    # API endpoint configuration
    api_endpoint = st.text_input(
        "API Endpoint",
        value="http://localhost:8000",
        help="URL of the FastAPI backend"
    )
    
    st.markdown("---")
    
    # Example requirements
    st.markdown("## 📋 Example Requirements")
    
    examples = {
        "100-camera AI surveillance system": "Deploy an AI security system supporting 100 cameras with GPU acceleration",
        "Small office security": "10-camera security system for small office building",
        "Large enterprise deployment": "200-camera AI surveillance system with redundant power and network",
        "Edge AI deployment": "5-camera edge AI system for remote monitoring",
        "Network-heavy deployment": "50-camera system requiring 96 network ports"
    }
    
    selected_example = st.selectbox(
        "Load example:",
        list(examples.keys())
    )
    
    if st.button("Load Example"):
        st.session_state.requirement_text = examples[selected_example]
        st.rerun()
    
    st.markdown("---")
    
    # Product catalog info
    st.markdown("## 🏷️ Product Catalog")
    
    catalog_info = {
        "AI Server X1": "800W, 4xGPU, $15,000, max 50 cameras",
        "AI Server X2": "1500W, 8xGPU, $28,000, max 120 cameras",
        "Edge Node": "150W, 1xGPU, $4,000, max 10 cameras",
        "UPS 5000W": "5000W capacity, $2,000",
        "Switch 48P": "400W, 48 ports, $1,500"
    }
    
    for product, specs in catalog_info.items():
        st.markdown(f"**{product}**")
        st.markdown(f"*{specs}*")
    
    st.markdown("---")
    
    # Validation rules
    st.markdown("## ✅ Validation Rules")
    st.markdown("- **Power Check**: Total power ≤ 5000W (UPS capacity)")
    st.markdown("- **Network Check**: Available ports ≥ Required ports")
    st.markdown("- **GPU Check**: GPU products selected if GPU required")

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<h2 class="sub-header">📝 Enter Requirements</h2>', unsafe_allow_html=True)
    
    # Requirement input
    requirement_text = st.text_area(
        "Describe your requirement:",
        value=st.session_state.get("requirement_text", ""),
        height=150,
        placeholder="Example: 'Deploy an AI security system supporting 100 cameras with GPU acceleration and 48 network ports'",
        help="Describe your infrastructure requirement in natural language"
    )
    
    # Analyze button
    analyze_button = st.button("🚀 Analyze & Generate Proposal", type="primary")
    
    # Status indicator
    if analyze_button and requirement_text:
        with st.spinner("🤖 Analyzing requirement with multi-agent system..."):
            # Show processing steps
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            steps = [
                "Extracting structured requirements...",
                "Matching products from catalog...",
                "Validating compatibility...",
                "Generating proposal..."
            ]
            
            for i, step in enumerate(steps):
                progress_bar.progress((i + 1) / len(steps))
                status_text.text(step)
                time.sleep(0.5)  # Simulate processing
            
            try:
                # Call API
                response = requests.post(
                    f"{api_endpoint}/analyze",
                    json={"text": requirement_text},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.proposal_result = result
                    st.session_state.last_requirement = requirement_text
                    st.session_state.proposal_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    status_text.text("✅ Proposal generated successfully!")
                    progress_bar.progress(100)
                    time.sleep(0.5)
                    st.rerun()
                else:
                    error_data = response.json()
                    st.error(f"❌ Error: {error_data.get('detail', 'Unknown error')}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API backend. Make sure the FastAPI server is running.")
            except requests.exceptions.Timeout:
                st.error("❌ Request timeout. The server is taking too long to respond.")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
    
    # Display previous requirement if exists
    if "last_requirement" in st.session_state:
        st.markdown("---")
        st.markdown("### Last Requirement")
        st.info(st.session_state.last_requirement)

with col2:
    st.markdown('<h2 class="sub-header">📄 Proposal Results</h2>', unsafe_allow_html=True)
    
    if "proposal_result" in st.session_state:
        result = st.session_state.proposal_result
        
        # Display timestamp
        st.markdown(f"*Generated: {st.session_state.proposal_time}*")
        
        # Display markdown proposal
        with st.expander("📋 View Full Proposal", expanded=True):
            st.markdown(result["markdown"])
        
        # Display JSON reasoning
        with st.expander("🔍 View JSON Reasoning"):
            st.json(result["json"])
        
        # Quick summary
        st.markdown("### 📊 Quick Summary")
        
        # Requirements summary
        reqs = result["json"]["requirements"]
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Cameras", reqs["device_count"])
            st.metric("Power (W)", reqs["estimated_power_w"])
        with col_b:
            st.metric("GPU Required", "Yes" if reqs["gpu_required"] else "No")
            st.metric("Network Ports", reqs["network_ports"])
        
        # Selected products
        st.markdown("### 🛒 Selected Products")
        products = result["json"]["selected_products"]
        for product in products:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{product['name']}**")
                with col2:
                    if product['price'] > 0:
                        st.markdown(f"${product['price']:,}")
                with col3:
                    if product['max_cameras'] > 0:
                        st.markdown(f"📷 {product['max_cameras']}")
                    elif product['capacity_w'] > 0:
                        st.markdown(f"⚡ {product['capacity_w']}W")
                    elif product['port_count'] > 0:
                        st.markdown(f"🔌 {product['port_count']}p")
        
        # Total cost
        total_cost = sum(p["price"] for p in products)
        st.markdown(f"**Total Cost: ${total_cost:,}**")
        
        # Validation status
        st.markdown("### ✅ Validation Status")
        validation = result["json"]["validation"]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if validation["power_check"] == "PASS":
                st.success("Power ✓")
            elif validation["power_check"] == "WARNING":
                st.warning("Power ⚠")
            else:
                st.error("Power ✗")
        
        with col2:
            if validation["network_check"] == "PASS":
                st.success("Network ✓")
            elif validation["network_check"] == "WARNING":
                st.warning("Network ⚠")
            else:
                st.error("Network ✗")
        
        with col3:
            if validation["gpu_check"] == "PASS":
                st.success("GPU ✓")
            elif validation["gpu_check"] == "WARNING":
                st.warning("GPU ⚠")
            else:
                st.error("GPU ✗")
        
        # Warnings
        if validation.get("warnings"):
            st.markdown("### ⚠️ Warnings & Recommendations")
            for warning in validation["warnings"]:
                st.warning(warning)
        
        # Download buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            # Download markdown
            markdown_content = result["markdown"]
            st.download_button(
                label="📥 Download Markdown",
                data=markdown_content,
                file_name=f"autose_proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
        
        with col2:
            # Download JSON
            json_content = json.dumps(result["json"], indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_content,
                file_name=f"autose_proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    else:
        st.info("👈 Enter a requirement and click 'Analyze & Generate Proposal' to see results.")
        
        # Show example output
        with st.expander("📋 View Example Output"):
            st.markdown("""
            # AutoSE Platform Proposal
            
            ## Requirements Summary
            
            - **Device Count**: 100 cameras/devices
            - **GPU Required**: Yes
            - **Estimated Power**: 1500W
            - **Network Ports**: 48 ports
            
            ## Recommended Products
            
            ### AI Server X2
            - **Power Consumption**: 1500W
            - **GPU Count**: 8
            - **Price**: $28,000
            - **Max Cameras Supported**: 120
            
            ### Switch 48P
            - **Power Consumption**: 400W
            - **Network Ports**: 48
            - **Price**: $1,500
            
            **Total Estimated Cost**: $29,500
            
            ## Validation Results
            
            - **Power Check**: PASS
            - **Network Check**: PASS
            - **GPU Check**: PASS
            
            ✅ **All validation checks passed**
            """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>AutoSE Platform v0.1.0 | Multi-agent autonomous platform for enterprise solution engineering</p>
    <p>Powered by FastAPI, DeepSeek V3.2, and Streamlit</p>
</div>
""", unsafe_allow_html=True)