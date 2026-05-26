# AutoSE Platform

**Autonomous Solution Engineering Platform** - Multi-agent autonomous platform for enterprise solution engineering that validates compatibility, optimizes infrastructure decisions, and generates proposals automatically.

## 🎯 Core Concept

Multi-agent autonomous platform for enterprise solution engineering that validates compatibility, optimizes infrastructure decisions, and generates proposals automatically.

## ✨ Features

1. **Input Field**: Client requirement text box
   - Example: "Deploy an AI security system supporting 100 cameras"

2. **Agent 1 - Requirement Analyzer**:
   - Extracts structured fields from user input using DeepSeek V3.2
   - Fields: `device_count`, `gpu_required`, `estimated_power_w`, `network_ports`

3. **Agent 2 - Product Retrieval**:
   - Matches requirements against built-in product catalog
   - Hardcoded catalog with 5 products

4. **Validation Layer** (Deterministic, not LLM):
   - Checks if total power exceeds UPS capacity (5000W threshold)
   - Returns warning if validation fails

5. **Output**: Generate proposal with explainable reasoning including:
   - Why selected product is recommended
   - Why alternatives were rejected
   - Risk analysis (if any)
   - Optimization suggestions

## 🏷️ Product Catalog

Hardcoded products:
- **AI Server X1**: 800W, 4xGPU, $15,000, max cameras: 50
- **AI Server X2**: 1500W, 8xGPU, $28,000, max cameras: 120
- **Edge Node**: 150W, 1xGPU, $4,000, max cameras: 10
- **UPS 5000W**: 5000W capacity, $2,000
- **Switch 48P**: 400W, 48 ports, $1,500

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip or uv package manager

### Installation

1. **Clone and setup environment:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

2. **Configure environment variables:**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file and add your DeepSeek API key
# Get API key from: https://platform.deepseek.com/api_keys
```

3. **Run the backend API:**
```bash
# Start FastAPI server
python -m uvicorn src.autose_platform.main:app --reload
```
The API will be available at: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

4. **Run the frontend:**
```bash
# Install Streamlit if not already installed
pip install streamlit

# Start Streamlit app
streamlit run streamlit_app.py
```
The frontend will be available at: http://localhost:8501

## 📋 Example Workflow

**User Input**: "100-camera AI surveillance system"

**Pipeline Process**:
1. **Agent 1 extracts**: `{device_count: 100, gpu_required: true, estimated_power_w: 1500, network_ports: 48}`
2. **Agent 2 retrieves**: AI Server X2 (120 cameras, 1500W)
3. **Validation**: 1500W < 5000W (PASS)
4. **Output**: Proposal recommending AI Server X2 + Switch 48P

## 🏗️ Architecture

### Backend Components
- **FastAPIBackend**: Main orchestrator
- **RequirementAnalyzer**: Agent 1 - Extracts structured requirements
- **ProductRetriever**: Agent 2 - Matches against product catalog
- **ValidationLayer**: Deterministic validation checks
- **ProposalGenerator**: Creates markdown + JSON proposals

### Frontend
- **Streamlit App**: Chat-style interface
- Real-time requirement input
- Proposal display with markdown rendering
- JSON reasoning viewer
- Download functionality

## 🧪 Testing

Run the test suite:
```bash
# Run unit tests
pytest tests/

# Run implementation test
python test_implementation.py

# Test API endpoints
python -m pytest tests/test_main.py -v
```

## 🔧 Configuration

### Environment Variables
- `DEEPSEEK_API_KEY`: Your DeepSeek API key (required for LLM extraction)
- `DEEPSEEK_API_URL`: DeepSeek API endpoint
- `DEEPSEEK_MODEL`: Model to use (default: deepseek-chat)
- `POWER_THRESHOLD_W`: Power validation threshold (default: 5000W)
- `CORS_ORIGINS`: Allowed frontend origins

### Product Catalog
The product catalog is hardcoded in `src/autose_platform/product_retriever.py`. To modify:
1. Edit the `_load_catalog()` method
2. Update product attributes as needed
3. Restart the application

## 📁 Project Structure

```
autose-platform/
├── src/autose_platform/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── backend.py           # Main orchestrator
│   ├── models.py            # Pydantic data models
│   ├── config.py            # Configuration management
│   ├── requirement_analyzer.py  # Agent 1
│   ├── product_retriever.py     # Agent 2
│   ├── validation_layer.py      # Validation layer
│   └── proposal_generator.py    # Proposal generator
├── tests/                   # Test files
├── streamlit_app.py        # Frontend application
├── test_implementation.py  # Implementation test
├── pyproject.toml          # Project dependencies
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

## 🔌 API Endpoints

### POST `/analyze`
Analyze requirement and generate proposal.

**Request:**
```json
{
  "text": "Deploy an AI security system supporting 100 cameras"
}
```

**Response:**
```json
{
  "markdown": "# Proposal\n\n## Recommended Products...",
  "json": {
    "requirements": {
      "device_count": 100,
      "gpu_required": true,
      "estimated_power_w": 1500,
      "network_ports": 48
    },
    "selected_products": [
      {
        "name": "AI Server X2",
        "power_w": 1500,
        "gpu_count": 8,
        "price": 28000,
        "max_cameras": 120
      }
    ],
    "validation": {
      "power_check": "PASS",
      "network_check": "PASS",
      "gpu_check": "PASS"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET `/health`
Health check endpoint.

### GET `/`
API information and available endpoints.

## 🐳 Docker Support

Build and run with Docker:

```bash
# Build the image
docker build -t autose-platform .

# Run the container
docker run -p 8000:8000 --env-file .env autose-platform
```

## 🔄 Fallback Mechanism

If DeepSeek API is unavailable:
1. System uses regex-based extraction as fallback
2. Basic field extraction from text patterns
3. Default values for missing fields
4. Continues with product matching and validation

## 📈 Future Enhancements

1. **Extended Product Catalog**: Database integration
2. **Multiple LLM Providers**: OpenAI, Anthropic, etc.
3. **Advanced Validation**: Cost optimization, performance metrics
4. **User Authentication**: Multi-user support
5. **Proposal Templates**: Customizable output formats
6. **Historical Analysis**: Learn from past proposals
7. **Integration APIs**: Connect to procurement systems

## 🛠️ Development

### Adding New Products
1. Edit `src/autose_platform/product_retriever.py`
2. Add new Product to `_load_catalog()` method
3. Update matching logic in `match()` method
4. Add validation rules if needed
5. Update tests

### Adding New Validation Rules
1. Edit `src/autose_platform/validation_layer.py`
2. Add new validation method
3. Update `ValidationResult` model if needed
4. Integrate into `validate()` method
5. Update tests

### Customizing Proposal Format
1. Edit `src/autose_platform/proposal_generator.py`
2. Modify `_generate_markdown()` method
3. Update `_generate_json_reasoning()` method
4. Customize templates as needed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Built with FastAPI, Streamlit, and DeepSeek V3.2
- Inspired by enterprise solution engineering workflows
- Designed for hackathon demonstration

## 📞 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the test cases
3. Examine the example workflow
4. Contact the development team