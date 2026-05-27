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
import uuid

# Page configuration
st.set_page_config(
    page_title="AutoSE - AI Sales Engineer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if "current_solution" not in st.session_state:
    st.session_state.current_solution = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

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
        "Load initial requirement:",
        list(examples.keys())
    )
    
    if st.button("Load Example", use_container_width=True):
        # Store the example text and trigger processing
        st.session_state.example_text = examples[selected_example]
        st.rerun()
    
    st.markdown("---")
    
    # Follow-up questions (only show if we have a current solution)
    if st.session_state.current_solution:
        st.markdown("## 🔄 Follow-up & Negotiation")
        
        follow_up_examples = {
            "What's the total budget?": "What's the total budget for this solution?",
            "Can I reduce the price?": "Can I reduce the price of this solution?",
            "Show cheaper alternatives": "Show me cheaper alternative options",
            "What if I remove GPU?": "What if I remove GPU acceleration to save costs?",
            "Add redundant power": "How much to add redundant power supply?"
        }
        
        selected_follow_up = st.selectbox(
            "Ask follow-up:",
            list(follow_up_examples.keys())
        )
        
        if st.button("Ask Follow-up", use_container_width=True):
            # Store the follow-up text and trigger processing
            st.session_state.example_text = follow_up_examples[selected_follow_up]
            st.rerun()
        
        st.markdown("### 💬 Negotiation Examples")
        
        negotiation_examples = {
            "This is wrong / not suitable": "This solution is wrong",
            "Too expensive, budget=3000": "Too expensive, I only have $3000",
            "Reduce cameras to 20": "Reduce cameras to 20",
            "Simplify the solution": "Simplify the solution",
            "Not reasonable for my needs": "This is not reasonable for my needs"
        }
        
        selected_negotiation = st.selectbox(
            "Try negotiation:",
            list(negotiation_examples.keys())
        )
        
        if st.button("Start Negotiation", use_container_width=True):
            # Store the negotiation text and trigger processing
            st.session_state.example_text = negotiation_examples[selected_negotiation]
            st.rerun()
    
    st.markdown("---")
    
    # Chat controls
    st.markdown("## 💬 Chat Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_solution = None
            st.rerun()
    
    with col2:
        if st.button("New Session", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.current_solution = None
            st.rerun()
    
    # Session information
    st.markdown("### 📝 Session Info")
    if st.session_state.current_solution:
        st.success(f"**Active Session:** {st.session_state.session_id[:8]}...")
        st.caption(f"Conversation memory is active. Ask follow-up questions about budget, modifications, or alternatives.")
    else:
        st.info("**New Session:** {st.session_state.session_id[:8]}...")
        st.caption("Your conversation will be remembered for follow-up questions.")
    
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

# Chat history and session are already initialized at the top

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
            # Check if this is a no-exact-match response
            is_no_exact_match = message.get("content", {}).get("no_exact_match", False)
            is_follow_up = message.get("is_follow_up", False)
            is_negotiation = message.get("is_negotiation", False)
            
            if is_no_exact_match:
                # Display no-exact-match response
                result = message["content"]
                
                st.warning("⚠️ **No Exact Match Found**")
                
                # Show the message
                if "message" in result:
                    st.markdown(result["message"])
                
                # Show options
                options = result.get("options", [])
                if options:
                    st.markdown("**Options:**")
                    for option in options:
                        if isinstance(option, dict):
                            st.markdown(f"- {option.get('description', '')}")
                        else:
                            st.markdown(f"- {option}")
                
                # Don't show full solution
                continue
            
            if is_follow_up:
                # Display follow-up response
                result = message["content"]
                follow_up = result.get("follow_up_response", {})
                
                if follow_up:
                    st.markdown(f"**{follow_up.get('type', 'Follow-up').replace('_', ' ').title()}**")
                    st.markdown(follow_up.get("message", ""))
                    
                    # Show budget info if available
                    if follow_up.get("type") == "budget_info":
                        total_cost = follow_up.get("total_cost", 0)
                        st.metric("Total Cost", f"${total_cost:,}")
                
                # Don't show full solution for follow-ups
                continue
            
            # Check if this is a negotiation response
            if is_negotiation:
                result = message["content"]
                
                # Display negotiation response
                st.info("💬 **Negotiation Response**")
                
                # Show the formatted message
                if "message" in result:
                    st.markdown(result["message"])
                
                # Show clarifying questions
                clarifying_questions = result.get("clarifying_questions", [])
                if clarifying_questions:
                    with st.expander("📝 **Clarifying Questions**", expanded=True):
                        for i, question in enumerate(clarifying_questions):
                            st.markdown(f"{i+1}. {question}")
                
                # Show current solution summary
                current_summary = result.get("current_solution_summary", {})
                if current_summary:
                    with st.expander("📊 **Current Solution Summary**", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Cost", f"${current_summary.get('total_cost', 0):,}")
                            st.metric("Device Count", current_summary.get('device_count', 0))
                        with col2:
                            st.metric("Product Count", current_summary.get('product_count', 0))
                        
                        # Show most expensive items
                        expensive_items = current_summary.get("most_expensive_items", [])
                        if expensive_items:
                            st.markdown("**Most Expensive Items:**")
                            for item in expensive_items:
                                st.markdown(f"- {item.get('name')}: ${item.get('price', 0):,} ({item.get('category')})")
                
                # Show alternative options
                alternative_options = result.get("alternative_options", {})
                if alternative_options:
                    with st.expander("🔄 **Alternative Options**", expanded=False):
                        for alt_type, summary in alternative_options.items():
                            if summary.get("total_cost", 0) > 0:
                                alt_type_display = alt_type.capitalize()
                                st.markdown(f"### {alt_type_display} Option")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Total Cost", f"${summary.get('total_cost', 0):,}")
                                with col2:
                                    st.metric("Product Count", summary.get('product_count', 0))
                                
                                # Show key products
                                products = summary.get("products", [])
                                if products:
                                    st.markdown("**Key Products:**")
                                    for product in products[:3]:
                                        st.markdown(f"- {product.get('name')}: ${product.get('price', 0):,}")
                
                # Show recommended action
                recommended_action = result.get("recommended_action", "")
                if recommended_action:
                    st.success(f"**Recommended:** {recommended_action}")
                
                # Don't show full solution for negotiations
                continue
            
            # For regular assistant messages, we have structured data
            if isinstance(message["content"], dict):
                # Display the structured response
                result = message["content"]
                
                # Show success status
                if result.get("success", False):
                    if result.get("intelligent_analysis", False):
                        st.success("✅ Intelligent analysis completed successfully!")
                    else:
                        st.success("✅ Solution designed successfully!")
                
                # Display intelligent analysis if available
                if result.get("intelligent_analysis", False):
                    analysis = result.get("analysis", {})
                    if analysis:
                        st.markdown("### 🧠 Intelligent Analysis")
                        st.markdown(f"**Goal:** {analysis.get('goal', '')}")
                        
                        # Show core products
                        core_products = analysis.get("core_products", [])
                        if core_products:
                            st.markdown(f"**Core Products:** {', '.join(core_products)}")
                        
                        # Show reasoning
                        reasoning = analysis.get("reasoning", "")
                        if reasoning:
                            with st.expander("📝 **Reasoning**", expanded=False):
                                st.markdown(reasoning)
                
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
                if "selected_products" in result and result["selected_products"]:
                    st.markdown("### 🛒 Recommended Products")
                    
                    # Create products table
                    products_data = []
                    for product in result["selected_products"]:
                        products_data.append({
                            "Product": product.get("name", "Unknown"),
                            "Category": product.get("category", ""),
                            "Price ($)": f"${product.get('price', 0):,}",
                            "Power (W)": product.get("power_w", 0) or "N/A",
                            "Description": product.get("description", "")[:50] + "..." if product.get("description") else "N/A"
                        })
                    
                    if products_data:
                        df = pd.DataFrame(products_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        # Calculate total cost
                        total_cost = result.get("total_cost", 0) or sum(product.get("price", 0) for product in result["selected_products"])
                        st.markdown(f"**Total Estimated Cost: ${total_cost:,}**")
                
                # Also check for "products" key for backward compatibility
                elif "products" in result and result["products"]:
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
                
                # Display explanations if available
                if "explanations" in result and result["explanations"]:
                    st.markdown("### 📝 Product Explanations")
                    for explanation in result["explanations"]:
                        if isinstance(explanation, dict):
                            with st.expander(f"**{explanation.get('product_name', 'Product')} (${explanation.get('product_price', 0):,})**", expanded=False):
                                st.markdown(explanation.get("explanation", ""))
                        else:
                            st.markdown(f"- {explanation}")
                
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
                # Call the AutoSE API with session_id
                request_data = {"text": prompt}
                if st.session_state.session_id:
                    request_data["session_id"] = st.session_state.session_id
                
                # Use intelligent analysis endpoint for all requests
                response = requests.post(
                    f"{api_endpoint}/api/analyze_intelligently",
                    json=request_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Store session_id if provided
                    if "session_id" in result:
                        st.session_state.session_id = result["session_id"]
                    
                    # Check if this is a no-exact-match response
                    if result.get("no_exact_match", False):
                        st.warning("⚠️ No exact match found")
                        
                        # Display no-match response
                        no_match_response = result.get("no_match_response", {})
                        if no_match_response:
                            st.markdown(f"**{no_match_response.get('message', '')}**")
                            
                            # Show options
                            options = no_match_response.get("options", [])
                            if options:
                                st.markdown("**Options:**")
                                for option in options:
                                    if isinstance(option, dict):
                                        st.markdown(f"- {option.get('description', '')}")
                                    else:
                                        st.markdown(f"- {option}")
                    
                    # Check if this is a negotiation response
                    elif result.get("is_negotiation", False):
                        st.info("💬 Processing negotiation...")
                        
                        # Store current solution for follow-up questions
                        if "current_solution_summary" in result:
                            st.session_state.current_solution = result
                    
                    # Check if this is a follow-up response
                    elif result.get("is_follow_up", False):
                        st.info("🔍 Processing follow-up question...")
                        
                        # Display follow-up response
                        follow_up = result.get("follow_up_response", {})
                        if follow_up:
                            st.markdown(f"**{follow_up.get('type', 'Follow-up').replace('_', ' ').title()}**")
                            st.markdown(follow_up.get("message", ""))
                            
                            # Show budget info if available
                            if follow_up.get("type") == "budget_info":
                                total_cost = follow_up.get("total_cost", 0)
                                st.metric("Total Cost", f"${total_cost:,}")
                    
                    else:
                        # Store current solution for follow-up questions
                        st.session_state.current_solution = result
                        
                        # Check for alert system questions
                        if result.get("has_alert_questions", False):
                            st.info("🔔 Alert system configuration needed")
                            alert_questions = result.get("alert_system_questions", [])
                            for question in alert_questions:
                                st.markdown(f"• {question}")
                        
                        st.success("✅ Intelligent analysis completed successfully!")
                    
                    # Display the structured response (handled in the chat history display)
                    # The actual display will happen when the message is rendered in the history
                    
                    # Add assistant response to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "is_follow_up": result.get("is_follow_up", False),
                        "is_negotiation": result.get("is_negotiation", False)
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