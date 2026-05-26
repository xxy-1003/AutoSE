# How to Test AutoSE Conversational Sales Engineer

## 🚀 Quick Start

### Option 1: Using Batch Script (Windows)
```bash
run_autose_with_negotiation.bat
```

### Option 2: Manual Start

1. **Start the Backend API:**
   ```bash
   python -m src.autose_platform.main
   ```
   - API available at: http://localhost:8000
   - Health check: http://localhost:8000/health

2. **Start the Frontend UI:**
   ```bash
   streamlit run chat_frontend.py
   ```
   - UI available at: http://localhost:8501

## 🧪 Test Cases to Try

### Initial Requirements (Start Here):
1. "Deploy a smart home system for a 3-bedroom house"
2. "100-camera AI surveillance system"
3. "Small office security with 10 cameras"

### Negotiation Phrases (After Getting a Solution):

**Complaining/Rejecting:**
- "This solution is wrong"
- "This is not suitable"
- "Not reasonable for my needs"

**Budget Constraints:**
- "Too expensive, budget=3000"
- "I only have $2500"
- "Budget: $1500 maximum"

**Device Reduction:**
- "Reduce cameras to 20"
- "Fewer devices please"
- "Simplify the solution"

**Alternatives:**
- "Show me alternatives"
- "Different option please"
- "What are my options?"

## 📊 Expected Behavior

### When you say "This solution is wrong":
✅ AutoSE will:
1. Detect negotiation intent
2. Ask clarifying questions:
   - "What feels wrong? Budget, performance, or number of devices?"
   - "Would you like me to: A) Lower total price B) Reduce device count C) Replace with cheaper models?"
3. Show current solution summary
4. Offer alternative options

### When you say "Too expensive, budget=3000":
✅ AutoSE will:
1. Extract budget constraint ($3000)
2. Generate Economy/Balanced/Performance alternatives
3. Show cost comparison
4. Recommend specific adjustments

### When you say "Reduce cameras to 20":
✅ AutoSE will:
1. Extract device count constraint (20)
2. Adjust server and equipment recommendations
3. Recalculate total cost
4. Show before/after comparison

## 🔍 Verification Steps

1. **Run pattern verification:**
   ```bash
   python verify_negotiation.py
   ```

2. **Check implementation:**
   - Open `chat_frontend.py` and look for "Negotiation Examples" in sidebar
   - Check that negotiation responses are displayed properly

3. **Test API directly:**
   ```bash
   # Using curl or Postman
   POST http://localhost:8000/api/analyze
   {
     "text": "This solution is wrong",
     "session_id": "your-session-id"
   }
   ```

## 🎯 Multi-Turn Negotiation Example

Here's a complete test flow:

1. **Initial Request:**
   ```
   User: Deploy a smart home system for 3 bedrooms
   AutoSE: ✅ Generated solution: 15 devices, $4,200 total
   ```

2. **First Negotiation:**
   ```
   User: Too expensive, budget=3000
   AutoSE: 💬 I understand. Current: $4,200 | Economy: $2,800 | Balanced: $3,400
   AutoSE: ❓ Would you like to reduce devices or find cheaper products?
   ```

3. **Specific Request:**
   ```
   User: Reduce light controllers
   AutoSE: ✅ Updated: Reduced light controllers, new total: $3,650
   ```

4. **Final Adjustment:**
   ```
   User: Also remove temperature sensor
   AutoSE: ✅ Final: $3,450. Ready to proceed?
   ```

## 🛠️ Files Modified

The following files were upgraded for negotiation capabilities:

1. **Core Logic:**
   - `src/autose_platform/requirement_analyzer.py` - Added negotiation detection
   - `src/autose_platform/product_retriever.py` - Added alternative generation
   - `src/autose_platform/proposal_generator.py` - Added negotiation responses
   - `src/autose_platform/main.py` - Added negotiation handling

2. **Frontend:**
   - `chat_frontend.py` - Added negotiation UI and examples

3. **Test Files:**
   - `verify_negotiation.py` - Pattern verification
   - `test_negotiation_simple.py` - Simple test
   - `run_autose_with_negotiation.bat` - Startup script
   - `NEGOTIATION_UPGRADE_SUMMARY.md` - Complete documentation

## ⚡ Quick Commands

```bash
# Verify implementation
python verify_negotiation.py

# See example flow
python test_negotiation_simple.py

# Start everything (follow instructions)
run_autose_with_negotiation.bat
```

## 📞 Troubleshooting

**Issue: API not responding**
- Check backend is running: `python -m src.autose_platform.main`
- Verify port 8000 is available

**Issue: Frontend not loading**
- Check streamlit is installed: `pip install streamlit`
- Verify port 8501 is available

**Issue: Negotiation not detected**
- Check the exact phrases match patterns
- Ensure you have a current solution before negotiating

## ✅ Success Criteria

The upgrade is successful when:

1. ✅ AutoSE detects negotiation intent from phrases like "wrong", "expensive", "reduce"
2. ✅ AutoSE asks clarifying questions based on intent
3. ✅ AutoSE extracts constraints like budget=3000, cameras=20
4. ✅ AutoSE generates alternative solutions (Economy/Balanced/Performance)
5. ✅ AutoSE maintains conversation memory across turns
6. ✅ Frontend displays negotiation responses clearly

## 🎉 Congratulations!

Your AutoSE platform now has full Conversational Sales Engineer capabilities with advanced negotiation skills. The system can handle multi-turn conversations, understand constraints, provide alternatives, and work with users to find the right solution.