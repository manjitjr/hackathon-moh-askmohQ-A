# MOH Q&A Cleaner - hackathon-moh-askmohQ-A

> Created for the MOH IFC hackathon for AskMoh Group

A healthcare-focused web application to upload, clean, and prepare Excel files containing questions and answers for AI knowledge bases with Govtech AIBot integration.

## Features

- 📤 Upload Excel files (.xlsx, .xls)
- 🏥 Healthcare-specific data cleaning:
  - Removes sensitive information (PHI/PII)
  - Removes duplicates with AI-powered semantic detection
  - Rephrases questions for standardization
  - Auto-categorizes by medical topics
  - Trims whitespace and normalizes formatting
- 🤖 **Dual-Mode Operation**:
  - **AI-Powered**: Govtech AIBot API integration (smart & secure)
  - **Rule-Based**: Fast pattern-matching (free & fast)
- 🎨 MOH Singapore branding (green theme)
- 📊 Statistics dashboard
- 👀 Preview cleaned data with categories
- 💾 Export in multiple formats (JSON, CSV, Excel)

## Quick Start

1. Install dependencies:
```bash
cd ~/Documents/qa-cleaner
pip3 install -r requirements.txt
```

2. Configure AIBot API (optional):
```bash
# Edit .env file with your X-ATLAS-Key
USE_LLM=true
AIBOT_API_KEY=your_api_key_here
AIBOT_API_URL="https://api.uat.aibots.gov.sg/v1.0/api/chats"
AIBOT_MODEL="llm_model_name"
AIBOT_API_MSGS="/messages"
AIBOT_AGENT_ID="chatbot_agent_id"
```

3. Start the servers:
```bash
# Terminal 1: Flask backend
python3 app.py

# Terminal 2: Web server
python3 -m http.server 8080
```

4. Open in browser:
```
http://localhost:8080
```

## How to Use

1. **Toggle AI**: Enable/disable AIBot features with the toggle switch
2. **Upload**: Drag and drop your Excel file or click to browse
3. **Process**: Automatic cleaning with sensitive info removal
4. **Review**: Check statistics and preview with categories
5. **Download**: Export in your preferred format

## Excel File Format

Your Excel file should contain:
- **Question** column (required)
- **Answer** column (required)
- **Category/Topic** column (optional - will auto-categorize if AI enabled)

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python Flask
- **AI Integration**: Govtech AIBot API (azure~openai.gpt-4o-mini)
- **Data Processing**: Pandas, OpenPyXL
