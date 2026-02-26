# Google Gemini Setup Guide - FREE LLM

## Quick Setup (2 minutes)

### Step 1: Get FREE API Key
1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with Google
3. Click "Create API key"
4. Copy the key

### Step 2: Add Key to Application
Edit the `.env` file:
```
GEMINI_API_KEY=paste_your_actual_key_here
USE_LLM=true
```

### Step 3: Restart Server
```bash
cd ~/Documents/qa-cleaner
python3 app.py
```

Look for: ✓ LLM features enabled (Google Gemini)

## Why Google Gemini?

✅ **100% FREE** - No credit card needed
✅ **60 requests/minute** - Generous limits  
✅ **Good quality** - Similar to GPT-3.5
✅ **Privacy friendly** - No data retention

## What You Get

**With LLM enabled:**
- Smarter question rephrasing
- Semantic duplicate detection (finds similar meaning, not just exact matches)
- Auto-categorization of questions

**Without LLM:**
- Still works great with rule-based processing
- No API calls, faster processing
- All sensitive info removal still works

## Testing

Upload a healthcare Excel file and check:
- Questions are intelligently rephrased
- Similar questions detected (not just duplicates)
- Categories auto-assigned

## Troubleshooting

**Still says "Rule-based processing only"?**
- Check .env has real API key (not `your_api_key_here`)
- Set `USE_LLM=true`
- Restart Flask server

**Getting errors?**
- Verify API key is valid at https://makersuite.google.com
- Free tier: 60 requests/min, 1500/day
- Wait a minute if you hit rate limit
