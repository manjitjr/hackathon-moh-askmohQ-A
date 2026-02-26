# Govtech AIBot Setup Guide

## Quick Setup

### Step 1: Get Your API Key (X-ATLAS-Key)
1. Visit the AIBot Portal: https://uat.aibots.gov.sg/chats/f4090ef5e15b4ad7b2620e946d8c629a
2. Sign in with your Govtech credentials
3. Navigate to API Settings or Developer Portal
4. Copy your X-ATLAS-Key

### Step 2: Configure the Application
Edit the `.env` file in the project folder:

```bash
AIBOT_API_KEY=your_actual_x_atlas_key_here
USE_LLM=true
```

### Step 3: Restart the Server
```bash
cd ~/Documents/qa-cleaner
python3 app.py
```

Look for: `✓ LLM features enabled (Govtech AIBot)`

## API Details

- **API Endpoint**: `https://api.uat.aibots.gov.sg/v1.0/api`
- **Model**: `azure~openai.gpt-4o-mini`
- **Authentication**: X-ATLAS-Key header
- **Bot Interface**: https://uat.aibots.gov.sg/chats/f4090ef5e15b4ad7b2620e946d8c629a

## What AIBot Does

When enabled, AIBot handles:
1. **Smart Question Rephrasing** - Contextual understanding and standardization
2. **Semantic Duplicate Detection** - Finds similar questions with different wording
3. **Auto-Categorization** - Assigns medical categories automatically

## Testing

1. **Toggle AI ON** in the web interface
2. **Upload an Excel file** with healthcare questions
3. **Check the console** for AIBot API calls
4. **Verify results** show improved processing

## API Call Example

```python
import requests
import json

url = "https://api.uat.aibots.gov.sg/v1.0/api"

payload = json.dumps({
    "model": "azure~openai.gpt-4o-mini",
    "messages": [{
        "role": "user",
        "content": "Your prompt here"
    }],
    "max_tokens": 150,
    "temperature": 0.3
})

headers = {
    'X-ATLAS-Key': '<your-api-key>',
    'Content-Type': 'application/json'
}

response = requests.post(url, headers=headers, data=payload)
print(response.json())
```

## Troubleshooting

### "AI requested but AIBot API key not configured"
- Check `.env` file has the correct X-ATLAS-Key
- Ensure `USE_LLM=true` (not `false`)
- Restart Flask server

### API Errors
- Verify your X-ATLAS-Key is valid
- Check you have access to the UAT environment
- Ensure network can reach `api.uat.aibots.gov.sg`

### Still Using Rule-Based Processing
1. Open `.env` file
2. Verify `AIBOT_API_KEY` is set (not `your_api_key_here`)
3. Set `USE_LLM=true`
4. Restart: `python3 app.py`

## Security Notes

- ✅ AIBot is a **government-secured** AI service
- ✅ Data processed within **Singapore government infrastructure**
- ✅ Compliant with government data protection policies
- ✅ Suitable for handling **healthcare Q&A data**

## Disable AI Features

To go back to rule-based processing:
1. Set `USE_LLM=false` in `.env`
2. Restart server
3. Or simply toggle OFF in the web interface
