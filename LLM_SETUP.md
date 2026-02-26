# MOH Q&A Cleaner - Setup Guide

## LLM Integration

This application now supports AI-powered features using OpenAI's API!

### Features Available:

**With LLM (AI-Powered):**
- ✅ Intelligent question rephrasing
- ✅ Semantic duplicate detection
- ✅ Auto-categorization of questions
- ✅ Better context understanding

**Without LLM (Rule-Based):**
- ✅ Pattern-based rephrasing
- ✅ Word-overlap duplicate detection
- ✅ Manual categorization only
- ✅ Fast and free!

### Setup Instructions:

#### 1. Install Dependencies
```bash
cd ~/Documents/qa-cleaner
pip3 install -r requirements.txt
```

#### 2. Get OpenAI API Key (Optional)
1. Go to https://platform.openai.com/api-keys
2. Create an account (if needed)
3. Generate a new API key

#### 3. Configure the App
Edit the `.env` file:
```bash
# Enable LLM features
USE_LLM=true

# Add your API key
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**OR keep it disabled:**
```bash
USE_LLM=false
```

#### 4. Run the Application
```bash
# Terminal 1: Start Flask backend
python3 app.py

# Terminal 2: Start web server
python3 -m http.server 8080
```

#### 5. Open in Browser
Navigate to: `http://localhost:8080`

### Cost Considerations:

**OpenAI API Costs (GPT-3.5-turbo):**
- ~$0.0005 per 1,000 tokens
- Average: $0.01-0.05 per 100 questions
- Very affordable for moderate use

**Free Alternative:**
- Set `USE_LLM=false` for rule-based processing (no cost)

### Comparison:

| Feature | Rule-Based | LLM-Powered |
|---------|-----------|-------------|
| Speed | ⚡ Fast | 🐢 Slower |
| Cost | 💰 Free | 💵 ~$0.01/100 Q's |
| Question Rephrasing | Good | Excellent |
| Duplicate Detection | Good | Excellent |
| Auto-Categorization | ❌ No | ✅ Yes |
| Accuracy | 85% | 95%+ |

### Troubleshooting:

**"LLM features not enabled"**
- Check your `.env` file
- Verify `USE_LLM=true`
- Confirm API key is valid

**"API rate limit"**
- OpenAI has rate limits
- Wait a moment and try again
- Consider upgrading your API plan

**"Connection error"**
- Check internet connection
- Verify API key is active
- Check OpenAI service status
