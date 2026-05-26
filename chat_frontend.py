"""
AutoSE Platform - Chat Frontend
Streamlit chat interface for the AutoSE Platform.
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="AutoSE - AI Sales Engineer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
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
    .product-card {
        background-color: #FAFAFA;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E0E0E0;
        margin: 0.5rem 0;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #E3F2FD;
    }
    .assistant-message {
        background-color: #F5F5F5;
    }
    .stButton button {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown('<h1 class="main-header">🤖 AutoSE - Autonomous Sales Engineer</h1>', unsafe_allow_html=True)
st.markdown("""
**Describe your technical requirement in natural language, and I'll design a complete enterprise solution with:**
- Product recommendations
- Compatibility validation
- Detailed proposal
- Cost quotation
""")

# Sidebar configuration
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    # API endpoint configuration
    api_endpoint = st.text_input(
        "API Endpoint",
        value="http://localhost:8000",
        help="URL of your AutoSE Platform backend"
    )
    
    st.markdown("---")
    
    # Example requirements
    st.markdown("## 📋 Example Requirements")
    
    examples = {
        "100-camera AI surveillance": "Deploy an AI security system supporting 100 cameras with GPU acceleration",
        "Small office security": "10-camera security system for small office building",
        "Large enterprise deployment": "200-camera AI surveillance system with redundant power and network",
        "Edge AI deployment": "5-camera edge AI system for remote monitoring",
        "Network-heavy deployment": "50-camera system requiring 96 network ports"
    }
    
    selected_example = st.selectbox(
        "Load example:",
        list(examples.keys())
    )
    
    if st.button("Load Example", use_container_width=True):
        # Store the example text and trigger processing
        st.session_state.example_text = examples[selected_example]
        st.rerun()
    
    st.markdown("---")
    
    # Chat controls
    st.markdown("## 💬 Chat Controls")
    
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    # API status
    st.markdown("## 📡 API Status")
    
    try:
        health_response = requests.get(f"{api_endpoint}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            st.success("✅ API Connected")
            st.caption(f"Status: {health_data.get('status', 'unknown')}")
            st.caption(f"Using Chutes: {health_data.get('using_chutes', False)}")
        else:
            st.warning("⚠️ API Responding with Error")
    except:
        st.error("❌ API Not Reachable")
        st.caption("Make sure the backend is running on port 8000")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Check if we have an example text to process
if hasattr(st.session_state, 'example_text'):
    # Use the example text as the prompt
    prompt = st.session_state.example_text
    del st.session_state.example_text
else:
    # Normal chat input
    prompt = st.chat_input("Describe your requirement (e.g., 'Deploy a 100-camera AI security system')...", key="main_chat_input")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(f"**{message['content']}**")
        else:
            # For assistant messages, we have structured data
            if isinstance(message["content"], dict):
                # Display the structured response
                result = message["content"]
                
                # Show success status
                if result.get("success", False):
                    st.success("✅ Solution designed successfully!")
                
                # Display requirements summary
                if "requirements" in result:
                    req = result["requirements"]
                    st.markdown("### 📋 Requirements Summary")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Cameras", req.get("device_count", "N/A"))
                        st.metric("GPU Required", "Yes" if req.get("gpu_required") else "No")
                    with col2:
                        st.metric("Power (W)", req.get("estimated_power_w", "N/A"))
                        st.metric("Network Ports", req.get("network_ports", "N/A"))
                
                # Display products table
                if "products" in result and result["products"]:
                    st.markdown("### 🛒 Recommended Products")
                    
                    # Create products table
                    products_data = []
                    for product in result["products"]:
                        products_data.append({
                            "Product": product.get("name", "Unknown"),
                            "Power (W)": product.get("power_w", 0),
                            "GPUs": product.get("gpu_count", 0),
                            "Price ($)": f"${product.get('price', 0):,}",
                            "Max Cameras": product.get("max_cameras", 0) or "N/A",
                            "Ports": product.get("port_count", 0) or "N/A",
                            "Capacity (W)": product.get("capacity_w", 0) or "N/A"
                        })
                    
                    if products_data:
                        df = pd.DataFrame(products_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        # Calculate total cost
                        total_cost = sum(product.get("price", 0) for product in result["products"])
                        st.markdown(f"**Total Estimated Cost: ${total_cost:,}**")
                
                # Display validation results
                if "validation" in result:
                    validation = result["validation"]
                    st.markdown("### ✅ Validation Results")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if validation.get("power_check") == "PASS":
                            st.success("Power ✓")
                        elif validation.get("power_check") == "WARNING":
                            st.warning("Power ⚠")
                        else:
                            st.error("Power ✗")
                    
                    with col2:
                        if validation.get("network_check") == "PASS":
                            st.success("Network ✓")
                        elif validation.get("network_check") == "WARNING":
                            st.warning("Network ⚠")
                        else:
                            st.error("Network ✗")
                    
                    with col3:
                        if validation.get("gpu_check") == "PASS":
                            st.success("GPU ✓")
                        elif validation.get("gpu_check") == "WARNING":
                            st.warning("GPU ⚠")
                        else:
                            st.error("GPU ✗")
                    
                    # Show warnings
                    if validation.get("warnings"):
                        st.markdown("#### ⚠️ Warnings & Recommendations")
                        for warning in validation.get("warnings", []):
                            st.warning(warning)
                
                # Display proposal
                if "proposal" in result:
                    proposal = result["proposal"]
                    if isinstance(proposal, dict):
                        # If proposal is a dict with markdown field
                        if "markdown" in proposal:
                            with st.expander("📄 View Detailed Proposal", expanded=True):
                                st.markdown(proposal["markdown"])
                        # If proposal is the full Proposal object
                        elif hasattr(proposal, "markdown"):
                            with st.expander("📄 View Detailed Proposal", expanded=True):
                                st.markdown(proposal.markdown)
                    elif isinstance(proposal, str):
                        # If proposal is a markdown string
                        with st.expander("📄 View Detailed Proposal", expanded=True):
                            st.markdown(proposal)
            else:
                # For simple text responses
                st.markdown(message["content"])
        
        # Show timestamp if available
        if "timestamp" in message:
            st.caption(f"*{message['timestamp']}*")

# Process the prompt if we have one
if prompt:
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(f"**{prompt}**")
    
    # Display assistant response area
    with st.chat_message("assistant"):
        # Show loading spinner
        with st.spinner("🤖 Analyzing requirement with AutoSE agents..."):
            # Simulate processing steps
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            steps = [
                "Extracting requirements...",
                "Matching products...",
                "Validating compatibility...",
                "Generating proposal..."
            ]
            
            for i, step in enumerate(steps):
                progress_bar.progress((i + 1) / len(steps))
                status_text.text(step)
                time.sleep(0.3)  # Simulate processing time
            
            try:
                # Call the AutoSE API
                response = requests.post(
                    f"{api_endpoint}/api/analyze",
                    json={"text": prompt},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Display success message
                    st.success("✅ Solution designed successfully!")
                    
                    # Display the structured response (handled in the chat history display)
                    # The actual display will happen when the message is rendered in the history
                    
                    # Add assistant response to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    
                    # Rerun to update the display
                    st.rerun()
                    
                else:
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Show error
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", str(response.status_code))
                    except:
                        error_detail = f"HTTP {response.status_code}"
                    
                    st.error(f"❌ API Error: {error_detail}")
                    
                    # Add error message to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Sorry, I encountered an error: {error_detail}",
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    
            except requests.exceptions.ConnectionError:
                progress_bar.empty()
                status_text.empty()
                st.error("❌ Cannot connect to AutoSE API. Make sure the backend is running.")
                st.info(f"Expected API endpoint: {api_endpoint}/api/analyze")
                
                # Add error message to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "I cannot connect to the AutoSE backend. Please make sure the server is running on port 8000.",
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
            except requests.exceptions.Timeout:
                progress_bar.empty()
                status_text.empty()
                st.error("❌ Request timeout. The server is taking too long to respond.")
                
                # Add error message to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "The request timed out. The system might be processing a complex requirement.",
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Unexpected error: {str(e)}")
                
                # Add error message to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"An unexpected error occurred: {str(e)}",
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>AutoSE Platform v1.0.0 | Autonomous Sales Engineer for Enterprise Solutions</p>
    <p>Powered by FastAPI, Chutes API, and Streamlit</p>
</div>
""", unsafe_allow_html=True)