# AutoSE Platform - Conversation Memory System

## Overview

Added multi-turn conversation memory to transform AutoSE from a single-query tool into a true autonomous sales engineer that remembers context and handles follow-up questions.

## Key Features

### 1. **Session-Based Memory**
- Each conversation gets a unique `session_id`
- In-memory storage of conversation history (resets on server restart)
- Tracks: original requirements, current solution, budget constraints, modifications

### 2. **Context-Aware Responses**
- Detects follow-up questions based on keywords (budget, price, cheaper, alternatives, etc.)
- References previous solutions when answering follow-ups
- Supports natural conversation flow

### 3. **Follow-up Question Types**
- **Budget/Price Questions**: "What's the total cost?", "What's the minimum spend?"
- **Modification Requests**: "Can I reduce the price?", "What if I remove X feature?"
- **Alternative Options**: "Show me cheaper alternatives", "What other options are there?"
- **General Follow-ups**: "Tell me more about...", "How does this work?"

## API Changes

### New Endpoints:
- `GET /api/sessions` - List all active sessions
- `GET /api/session/{session_id}` - Get session details
- `DELETE /api/session/{session_id}` - Delete a session

### Updated Endpoint:
- `POST /api/analyze` - Now accepts optional `session_id` parameter

### Request Format:
```json
{
  "text": "User requirement or follow-up question",
  "session_id": "optional-session-id"  // For continuing conversations
}
```

### Response Format (for follow-ups):
```json
{
  "success": true,
  "session_id": "session-uuid",
  "is_follow_up": true,
  "follow_up_response": {
    "type": "budget_info|modification_request|alternative_request|general_follow_up",
    "message": "Context-aware response",
    "total_cost": 28000,  // For budget questions
    "currency": "USD"
  }
}
```

## Frontend Updates

### New Features:
1. **Session Indicator**: Shows active session ID in sidebar
2. **Follow-up Question Examples**: Pre-configured follow-up questions in sidebar
3. **Session Management**: "New Session" button to start fresh conversations
4. **Context-Aware Display**: Follow-up responses shown differently from full solutions

### Session State:
```python
st.session_state.session_id  # Current conversation session
st.session_state.current_solution  # Last generated solution
st.session_state.messages  # Chat history
```

## How It Works

### 1. **Initial Request**
```
User: "Deploy a 100-camera AI security system"
→ Creates new session with unique ID
→ Processes through all 4 agents
→ Stores solution in session memory
→ Returns full solution with session_id
```

### 2. **Follow-up Question**
```
User: "What's the total budget?"
→ Detects as follow-up (contains "budget" keyword)
→ Retrieves current solution from session memory
→ Calculates total cost from stored products
→ Returns budget information without reprocessing
→ Adds modification to session history
```

### 3. **Another Follow-up**
```
User: "Show me cheaper alternatives"
→ Detects as follow-up (contains "cheaper")
→ References same session
→ Suggests exploring alternative configurations
→ Maintains conversation context
```

## Example Conversations

### Conversation 1: Budget Discussion
```
User: Deploy an AI security system for 50 cameras
AutoSE: [Generates solution with AI Server X2 + Switch 48P, $32,000]

User: What's the total budget?
AutoSE: The current solution costs $32,000. You can reduce costs by...

User: Can I reduce the price?
AutoSE: I can help you modify the solution. Please specify...
```

### Conversation 2: Feature Modification
```
User: 10-camera security system for small office
AutoSE: [Generates solution with Edge Node, $4,000]

User: What if I add GPU acceleration?
AutoSE: [References current solution, suggests upgrade path]

User: How much to add redundant power?
AutoSE: [Calculates additional cost based on current setup]
```

## Implementation Details

### Backend (`src/autose_platform/main.py`):
- `ConversationMemory` class to store session data
- `conversation_store` dictionary for in-memory storage
- `is_follow_up_question()` function for keyword detection
- `handle_follow_up_question()` for context-aware responses

### Frontend (`chat_frontend.py`):
- Session state management with Streamlit
- Dynamic sidebar with follow-up examples
- Different display for follow-up vs. full solutions
- Session ID display and management

## Testing

Run the test script:
```bash
python test_conversation_memory.py
```

## Usage Instructions

1. **Start Backend**:
   ```bash
   python -m src.autose_platform.main
   ```

2. **Start Frontend**:
   ```bash
   streamlit run chat_frontend.py
   ```

3. **Test Conversation**:
   - Enter initial requirement
   - Ask follow-up questions using sidebar examples or your own
   - Watch as AutoSE remembers context and provides relevant answers

## Future Enhancements

1. **Persistent Storage**: Database integration for long-term memory
2. **Advanced NLP**: Better follow-up detection using LLM
3. **Solution Modification**: Actual product swapping based on requests
4. **Multi-user Support**: User authentication and separate conversations
5. **Export Conversations**: Save conversation history as PDF/email

## Notes

- Current implementation uses simple keyword detection for follow-ups
- In-memory storage means conversations reset when server restarts
- All existing Chutes API integration remains unchanged
- Backward compatible: Existing single-query usage still works