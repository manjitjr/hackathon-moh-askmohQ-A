from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
import pandas as pd
import re
import io
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import json
from dotenv import load_dotenv
from logging_config import setup_logging
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Setup logging
setup_logging(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize AIBot API (Govtech)
USE_LLM = os.getenv('USE_LLM', 'false').lower() == 'true'
AIBOT_API_KEY = os.getenv('AIBOT_API_KEY')
AIBOT_API_URL = os.getenv('AIBOT_API_URL', 'https://api.uat.aibots.gov.sg/v1.0/api/chats')
AIBOT_MODEL = os.getenv('AIBOT_MODEL', 'azure~openai.gpt-4o-mini')
AIBOT_API_MSGS = os.getenv('AIBOT_API_MSGS', '/messages')
AIBOT_AGENT_ID = os.getenv('AIBOT_AGENT_ID')

# Set Singapore timezone for timestamping
sg_tz = ZoneInfo('Asia/Singapore')

def setup_aibot(temperature):
    """Setup AIBot chat"""
    if not aibot_available:
        app.logger.warning("⚠️  AIBot API key not configured. Skipping AIBot setup.")
        return ""
    
    try:
        headers = {
            'X-ATLAS-Key': AIBOT_API_KEY,
            'Content-Type': 'application/json'
        }
        
        payload ={
            "agents": [AIBOT_AGENT_ID],
            "model": AIBOT_MODEL,
            "name": "QA Cleaner Test",
            "params": {"temperature": temperature}
        }
        
        # Log chat setup request
        app.logger.info("="*60)
        app.logger.info("🔧 AIBot Chat Setup Request")
        app.logger.info(f"URL: {AIBOT_API_URL}")
        app.logger.info(f"Model: {AIBOT_MODEL}")
        app.logger.info(f"Agent ID: {AIBOT_AGENT_ID}")
        app.logger.info(f"Temperature: {temperature}")
        app.logger.info("="*60)
        
        response = requests.post(AIBOT_API_URL, headers=headers, json=payload, timeout=10, verify=False)
        
        app.logger.info(f"📡 Setup Response Status: {response.status_code}")
        
        response.raise_for_status()
        
        result = response.json()
        chat_id = result.get('id')
        
        app.logger.info("="*60)
        app.logger.info("✅ AIBot Chat Setup Successful")
        app.logger.info(f"Chat ID: {chat_id}")
        app.logger.info(f"Full Response: {json.dumps(result, indent=2)}")
        app.logger.info("="*60)
        
        return chat_id
    except Exception as e:
        app.logger.error("="*60)
        app.logger.error("❌ AIBot Chat Setup Failed")
        app.logger.error(f"Error: {e}")
        app.logger.error("="*60)
        return ""
    
if USE_LLM and AIBOT_API_KEY and AIBOT_API_KEY != 'your_api_key_here':
    aibot_available = True
    chat_id = setup_aibot(temperature=0.3)
    app.logger.info(f"✓ LLM features enabled (Govtech AIBot), chatID = {chat_id}")
else:
    aibot_available = False
    USE_LLM = False
    app.logger.info("✓ Rule-based processing only")

def call_aibot(prompt):
    """Call Govtech AIBot Message API"""
    if not aibot_available:
        return None
    
    try:
        msg_url = AIBOT_API_URL +  "/" + chat_id + AIBOT_API_MSGS
        
        # Log the request details
        app.logger.info("="*60)
        app.logger.info("🤖 AIBot API Request")
        app.logger.info(f"URL: {msg_url}")
        app.logger.info(f"Prompt: {prompt[:200]}...")  # First 200 chars
        app.logger.info("="*60)

        response = requests.post(
            msg_url,
            headers={"X-ATLAS-Key": AIBOT_API_KEY},
            data={"content": prompt},
            verify=False
        )
        
        # Log response status
        app.logger.info(f"📡 AIBot Response Status: {response.status_code}")
        
        response.raise_for_status()

        result = response.json()
        print(f"AIBot result: {result['response']['content']}")
        
        # Log the full response
        app.logger.info("="*60)
        app.logger.info("🤖 AIBot API Response")
        app.logger.info(f"Response: {json.dumps(result, indent=2)}")
        app.logger.info("="*60)
        
        # Parse AIBot response format
        if 'choices' in result and len(result['choices']) > 0:
            answer = result['choices'][0]['message']['content'].strip()
            app.logger.info(f"✅ Parsed Answer: {answer}")
            return answer
        elif 'response' in result:
            # Handle both string and dict formats
            if isinstance(result['response'], dict) and 'content' in result['response']:
                answer = result['response']['content'].strip()
            elif isinstance(result['response'], str):
                answer = result['response'].strip()
            else:
                answer = str(result['response']).strip()
            app.logger.info(f"✅ Parsed Answer: {answer}")
            return answer
        elif isinstance(result, str):
            answer = result.strip()
            app.logger.info(f"✅ Parsed Answer: {answer}")
            return answer
        return None
    except Exception as e:
        # Try to extract API error details if present
        try:
            err_body = None
            if 'response' in locals() and response is not None:
                try:
                    err_body = response.json()
                except Exception:
                    err_body = response.text
            app.logger.error("="*60)
            app.logger.error("❌ AIBot API Error")
            app.logger.error(f"Error: {e}")
            app.logger.error(f"Response Body: {err_body}")
            app.logger.error("="*60)
        except Exception:
            app.logger.error(f"❌ AIBot API error: {e}")
        return None

def remove_sensitive_info(text):
    """Remove sensitive healthcare information"""
    if pd.isna(text) or text is None:
        return ""
    
    text = str(text)
    
    # Remove names (common patterns like "Mr./Mrs./Ms./Dr. Name" or "Name, FirstName")
    text = re.sub(r'\b(?:Mr|Mrs|Ms|Dr|Miss)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', '[PATIENT NAME]', text)
    text = re.sub(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?=\s+(?:has|was|is|had|called|visited|asked))', '[PATIENT NAME]', text)
    
    # Remove phone numbers
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}', '[PHONE]', text)
    
    # Remove email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Remove dates of birth
    text = re.sub(r'\b(?:DOB|Date of Birth|born on|birthday)[\s:]*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', '[DOB]', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', '[DATE]', text)
    
    # Remove medical record numbers, patient IDs
    text = re.sub(r'\b(?:MRN|Patient ID|Record #|ID)[\s:]*[A-Z0-9]{5,}\b', '[PATIENT ID]', text, flags=re.IGNORECASE)
    
    # Remove specific addresses
    text = re.sub(r'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b', '[ADDRESS]', text, flags=re.IGNORECASE)
    
    # Remove SSN
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
    
    # Remove insurance numbers
    text = re.sub(r'\b(?:Insurance|Policy)[\s#:]*[A-Z0-9]{6,}\b', '[INSURANCE]', text, flags=re.IGNORECASE)
    
    return text

def rephrase_question(question, use_llm_for_request=None):
    """Rephrase questions to be more generic and standardized"""
    if pd.isna(question) or not question:
        return question
    
    # Use LLM if enabled (check override or global setting)
    use_llm_now = use_llm_for_request if use_llm_for_request is not None else USE_LLM
    
    app.logger.info(f"🔍 Processing question: '{question[:80]}...' | AI Mode: {use_llm_now}")
    
    if use_llm_now:
        if aibot_available:
            # Check local database for an existing entry and reuse it if available
            try:
                existing = find_existing_entry_by_question(question)
                if existing:
                    app.logger.info(f"♻️ Found existing entry in database, reusing it")
                    # Build a rephrased_question dict matching expected schema
                    rephrased = {
                        'category': existing.get('category', ''),
                        'question': existing.get('question') or existing.get('original_question') or question,
                        'answer': existing.get('answer', ''),
                        'confidence': {'level': existing.get('confidence', ''), 'reason': existing.get('reason', '')}
                    }
                    return rephrased
                else:
                    app.logger.info(f"🆕 No existing entry found, calling AIBot...")
            except Exception as e:
                app.logger.warning(f"⚠️ Database lookup error: {e}")

            try:
                # Create a structured prompt for the AIBot
                prompt = f"""Analyze this healthcare question and provide a structured response in JSON format:

Question: "{question}"

Please provide:
1. A categorized topic (e.g., "General Healthcare", "Medication", "Symptoms", "Treatment", "Prevention")
2. A standardized, generic version of the question (remove personal details, make it general)
3. A brief, accurate answer to the question
4. Your confidence level (High/Medium/Low) and reason

Respond ONLY with valid JSON in this exact format:
{{
  "category": "Category Name",
  "question": "Standardized generic question?",
  "answer": "Brief accurate answer",
  "confidence": {{
    "level": "High/Medium/Low",
    "reason": "Brief explanation"
  }}
}}"""
                
                app.logger.info(f"📤 Calling AIBot for question: {question[:100]}...")
                rephrased = call_aibot(prompt)
                
                if rephrased:
                    rephrased = _parse_possible_json(rephrased)
                    app.logger.info(f"✅ AIBot response received: {str(rephrased)[:200]}...")
                    
                    # Ensure it's in the correct format
                    if isinstance(rephrased, dict):
                        return rephrased
                    else:
                        app.logger.warning(f"⚠️ AIBot response not in expected format, using fallback")
                else:
                    app.logger.warning(f"⚠️ No response from AIBot, using fallback")
                    
            except Exception as e:
                app.logger.error(f"❌ AIBot error: {e}, falling back to rules")
        else:
            app.logger.warning("⚠️  AI requested but AIBot API key not configured. Using rule-based processing.")
    else:
        app.logger.info(f"📝 Using rule-based processing (AI Mode OFF)")
    
    # Fallback to rule-based rephrasing
    # Convert to lowercase for pattern matching
    q_lower = question.lower()
    
    # Standardize common healthcare question patterns
    replacements = {
        r'\b(?:what|how) (?:can|do|should) (?:i|we|one|you) do (?:if|when|for)': 'What should be done when',
        r'\bhow (?:can|do|should) (?:i|we) treat\b': 'How to treat',
        r'\bwhat (?:are|is) the (?:symptoms?|signs?) (?:of|for)\b': 'What are the symptoms of',
        r'\bwhat (?:causes|leads to|results in)\b': 'What causes',
        r'\bhow (?:can|do) (?:i|we|you) prevent\b': 'How to prevent',
        r'\bwhen should (?:i|we|you|one) (?:see|visit|consult)\b': 'When should someone consult',
        r'\bis it (?:safe|ok|okay) to\b': 'Is it safe to',
        r'\bcan (?:i|you|one|we) (?:take|use)\b': 'Can someone take',
        r'\bwhat (?:is|are) the (?:treatment|treatments) for\b': 'What is the treatment for',
        r'\bhow (?:long|often) should (?:i|you|one|we)\b': 'How long should someone',
        r'\bmy (?:child|baby|kid)\b': 'a child',
        r'\bmy (?:mother|father|parent|husband|wife|spouse)\b': 'a family member',
    }
    
    rephrased = question
    for pattern, replacement in replacements.items():
        rephrased = re.sub(pattern, replacement, rephrased, flags=re.IGNORECASE)
    
    # Capitalize first letter
    if rephrased:
        rephrased = rephrased[0].upper() + rephrased[1:]
    
    # Ensure it ends with a question mark
    if rephrased and not rephrased.endswith('?'):
        rephrased += '?'
    
    # Return structured format matching LLM response
    return {
        'category': 'General Healthcare',
        'question': rephrased,
        'answer': '',
        'confidence': {'level': 'Low', 'reason': 'Rule-based processing without LLM analysis'}
    }

def clean_text(text):
    """Clean and normalize text"""
    if pd.isna(text) or text is None:
        return ""
    
    text = str(text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove special characters that might cause issues
    text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)
    
    return text

def is_similar_question(q1, q2, threshold=0.8, use_llm_for_request=None):
    """Check if two questions are similar (fuzzy matching)"""
    # Use LLM for semantic similarity if enabled
    use_llm_now = use_llm_for_request if use_llm_for_request is not None else USE_LLM
    if use_llm_now:
        if aibot_available:
            try:
                prompt = f"""You are a similarity checker. Respond with only 'yes' or 'no' to indicate if two questions ask essentially the same thing.

Are these questions essentially the same?
1: {q1}
2: {q2}

Respond with only 'yes' or 'no'."""
                answer = call_aibot(prompt)
                if answer:
                    return 'yes' in answer.lower()
            except Exception as e:
                app.logger.error(f"AIBot similarity error: {e}, falling back to rules")
        else:
            app.logger.warning("⚠️  AI requested but AIBot API key not configured. Using word-overlap similarity.")
    
    # Fallback to rule-based similarity
    # Normalize both questions
    q1_norm = re.sub(r'[^\w\s]', '', q1.lower())
    q2_norm = re.sub(r'[^\w\s]', '', q2.lower())
    
    # Simple similarity check based on word overlap
    words1 = set(q1_norm.split())
    words2 = set(q2_norm.split())
    
    if len(words1) == 0 or len(words2) == 0:
        return False
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    similarity = intersection / union if union > 0 else 0
    return similarity >= threshold

def clean_qa_data_stream(df, use_llm_override=None):
    """Generator function that yields progress for each Q&A processed"""
    # Determine if we should use LLM (override takes precedence)
    use_llm_for_this_request = use_llm_override if use_llm_override is not None else USE_LLM
    
    stats = {
        'original_count': len(df),
        'duplicates_removed': 0,
        'issues_fixed': 0,
        'sensitive_info_removed': 0,
        'questions_rephrased': 0
    }
    
    # Try to identify question column
    columns = df.columns.tolist()
    question_col = None
    
    for col in columns:
        col_lower = str(col).lower()
        if 'question' in col_lower or 'q' == col_lower:
            question_col = col
    
    if question_col is None and len(columns) > 0:
        question_col = columns[0]
    
    if question_col is None:
        raise ValueError("Could not identify question column")
    
    seen_questions = []
    total_rows = len(df)
    
    for idx, row in df.iterrows():
        question = clean_text(row[question_col])
        
        # Skip empty or very short questions
        if not question or len(question) < 3:
            stats['issues_fixed'] += 1
            continue
        
        # Remove sensitive information
        original_question = question
        question = remove_sensitive_info(question)
        
        if question != original_question:
            stats['sensitive_info_removed'] += 1
        
        # Rephrase question
        rephrased_result = rephrase_question(question, use_llm_for_this_request)
        
        # Handle both dict and string responses
        if isinstance(rephrased_result, dict):
            rephrased_question = rephrased_result.get('question', question)
        else:
            rephrased_question = rephrased_result
            rephrased_result = {
                'category': 'General Healthcare',
                'question': rephrased_question,
                'answer': '',
                'confidence': {'level': 'Low', 'reason': 'Rule-based processing'}
            }
        
        if rephrased_question != question:
            stats['questions_rephrased'] += 1
        
        seen_questions.append(question)
        
        cleaned_item = {
            'category': rephrased_result.get('category', 'General Healthcare'),
            'question': rephrased_result.get('question', rephrased_question),
            'answer': rephrased_result.get('answer', ''),
            'confidence': rephrased_result.get('confidence', {}).get('level', 'Low'),
            'reason': rephrased_result.get('confidence', {}).get('reason', ''),
        }
        
        # Yield progress update
        yield {
            'type': 'progress',
            'index': idx + 1,
            'total': total_rows,
            'percentage': int(((idx + 1) / total_rows) * 100),
            'data': cleaned_item,
            'stats': stats.copy()
        }

def clean_qa_data(df, use_llm_override=None):
    """Clean and process healthcare Q&A data"""
    # Determine if we should use LLM (override takes precedence)
    use_llm_for_this_request = use_llm_override if use_llm_override is not None else USE_LLM
    
    stats = {
        'original_count': len(df),
        'duplicates_removed': 0,
        'issues_fixed': 0,
        'sensitive_info_removed': 0,
        'questions_rephrased': 0
    }
    
    # Try to identify question, answer, and category columns
    columns = df.columns.tolist()
    question_col = None
    
    # Look for question, answer, and category columns
    for col in columns:
        col_lower = str(col).lower()
        if 'question' in col_lower or 'q' == col_lower:
            question_col = col
    
    # If not found, use first columns
    if question_col is None and len(columns) > 0:
        question_col = columns[0]
    
    if question_col is None:
        raise ValueError("Could not identify question column")
    
    # Create new dataframe with cleaned data
    cleaned_data = []
    seen_questions = []
    
    for idx, row in df.iterrows():
        question = clean_text(row[question_col])
        
        # Skip empty rows
        if not question:
            stats['issues_fixed'] += 1
            continue
        
        # Skip very short questions
        if len(question) < 3:
            stats['issues_fixed'] += 1
            continue
        
        # Remove sensitive information from question
        original_question = question
        
        question = remove_sensitive_info(question)
        
        if question != original_question:
            stats['sensitive_info_removed'] += 1
        
        # Rephrase question for standardization
        app.logger.info(f"USING LLM: {use_llm_for_this_request}")
        rephrased_result = rephrase_question(question, use_llm_for_this_request)
        
        # Handle both dict (LLM/structured) and string (fallback) responses
        if isinstance(rephrased_result, dict):
            rephrased_question = rephrased_result.get('question', question)
        else:
            # Old format - shouldn't happen now but keep for safety
            rephrased_question = rephrased_result
            rephrased_result = {
                'category': 'General Healthcare',
                'question': rephrased_question,
                'answer': '',
                'confidence': {'level': 'Low', 'reason': 'Rule-based processing'}
            }
        
        if rephrased_question != question:
            stats['questions_rephrased'] += 1
        
        # Check for similar questions (more aggressive duplicate detection)
        # is_duplicate = False
        # for seen_q in seen_questions:
        #     if is_similar_question(question, seen_q, 0.8, use_llm_for_this_request):
        #         is_duplicate = True
        #         stats['duplicates_removed'] += 1
        #         break
        
        # if is_duplicate:
        #     continue
        seen_questions.append(question)
        # Attempt to extract category and answer columns if present

        cleaned_data.append({
            'category': rephrased_result.get('category', 'General Healthcare'),
            'question': rephrased_result.get('question', rephrased_question),
            'answer': rephrased_result.get('answer', ''),
            'confidence': rephrased_result.get('confidence', {}).get('level', 'Low'),
            'reason': rephrased_result.get('confidence', {}).get('reason', ''),
        })
        # cleaned_data.append(rephrased_question)
    
    return cleaned_data, stats


def _normalize_text(s: str) -> str:
    """Normalize text for duplicate checking (module-level helper)."""
    try:
        if pd.isna(s):
            return ''
    except Exception:
        pass
    if s is None:
        return ''
    s = str(s).strip().lower()
    if s == 'nan':
        return ''
    s = re.sub(r'[\W_]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def collect_existing_questions_from_df(existing_df: pd.DataFrame) -> set:
    """Collect normalized question strings from any question-like columns in a DataFrame."""
    existing_questions = set()
    for col in existing_df.columns:
        try:
            col_lower = str(col).lower()
        except Exception:
            col_lower = ''
        if 'question' in col_lower or col_lower == 'q' or col_lower.startswith('q'):
            existing_df[col] = existing_df[col].fillna('').astype(str)
            for x in existing_df[col].tolist():
                nx = _normalize_text(x)
                if nx:
                    existing_questions.add(nx)
    return existing_questions


def is_duplicate_row(row: pd.Series, existing_questions: set) -> tuple:
    """Return (is_duplicate: bool, key_used: str) for the given row.
    Prefers `original_question` normalized value, falls back to `question`.
    """
    norm_orig = _normalize_text(row.get('original_question', ''))
    norm_q = _normalize_text(row.get('question', ''))
    key_used = norm_orig or norm_q
    if key_used and key_used in existing_questions:
        return True, key_used
    return False, key_used


def find_existing_entry_by_question(question_text: str, filename: str = 'database.xlsx') -> dict | None:
    """Search the Excel database for a matching question and return a dict row if found."""
    if not question_text:
        return None
    key = _normalize_text(question_text)
    if not key:
        return None

    if not os.path.exists(filename):
        return None

    try:
        df = pd.read_excel(filename)
    except Exception:
        return None

    # Check any question-like column for a match (original_question preferred)
    for col in df.columns:
        try:
            col_lower = str(col).lower()
        except Exception:
            col_lower = ''
        if 'question' in col_lower or col_lower == 'q' or col_lower.startswith('q'):
            for _, r in df.iterrows():
                val = r.get(col, '')
                if _normalize_text(val) == key:
                    # convert row to a consistent dict shape
                    rowd = {c: (r.get(c, '') if not pd.isna(r.get(c, '')) else '') for c in df.columns}
                    return rowd
    return None

def save_database_excel(df, cleaned_data):
    """Save cleaned data to a database Excel file (append or create)."""
    filename = 'database.xlsx'
    # Ensure list of dicts
    try:
        new_data = pd.DataFrame(cleaned_data)
    except Exception:
        # If cleaned_data is not a list of dicts, attempt to normalize
        new_data = pd.DataFrame([item if isinstance(item, dict) else {'question': str(item)} for item in cleaned_data])

    # Attempt to recover the original question text from the uploaded `df`
    # to store alongside the cleaned/rephrased question. This mirrors the
    # filtering logic in `clean_qa_data` so the lengths should align.
    original_questions = []
    try:
        # identify question column in original df
        qcol = None
        for c in df.columns.tolist():
            cl = str(c).lower()
            if 'question' in cl or cl == 'q':
                qcol = c
                break
        if qcol is None and len(df.columns) > 0:
            qcol = df.columns[0]

        if qcol is not None:
            for _, row in df.iterrows():
                raw_q = clean_text(row.get(qcol, ''))
                if not raw_q:
                    continue
                if len(raw_q) < 3:
                    continue
                original_questions.append(raw_q)
    except Exception:
        original_questions = []

    # If we successfully extracted original questions and the counts align,
    # add them as an `original_question` column to the new data.
    if original_questions:
        try:
            if 'original_question' not in new_data.columns:
                # If lengths differ, align by taking the first N entries.
                if len(original_questions) >= len(new_data):
                    new_data['original_question'] = original_questions[:len(new_data)]
                else:
                    # pad with empty strings if fewer originals than cleaned rows
                    padded = original_questions + [''] * (len(new_data) - len(original_questions))
                    new_data['original_question'] = padded
        except Exception:
            pass

    # Add timestamp column for when these rows were saved (Singapore timezone)
    try:
        timestamp = datetime.now(sg_tz).strftime('%Y-%m-%d %H:%M:%S %Z')
    except Exception:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Ensure there's a 'question' column we can use to detect duplicates
    if 'question' not in new_data.columns:
        # try to find a column that looks like a question
        for c in new_data.columns:
            if str(c).lower().startswith('q') or 'question' in str(c).lower():
                new_data = new_data.rename(columns={c: 'question'})
                break

    # Fill NA and coerce to string for comparison
    if 'question' in new_data.columns:
        new_data['question'] = new_data['question'].fillna('').astype(str)
    else:
        # Nothing sensible to save
        print('No question column found in cleaned data; aborting save.')
        return

    # Add timestamp only for new rows (will be set on rows that are appended)
    new_data['date_time'] = ''

    # If file exists, read existing questions and filter out duplicates
    if os.path.exists(filename):
        try:
            existing_data = pd.read_excel(filename)
            # collect normalized existing questions from any question-like column
            existing_questions = collect_existing_questions_from_df(existing_data)

            # Determine rows to append (skip when original_question or question already exists)
            to_append_rows = []
            for _, row in new_data.iterrows():
                is_dup, key_used = is_duplicate_row(row, existing_questions)
                if not is_dup and key_used:
                    # set timestamp for this appended row
                    try:
                        row_ts = datetime.now(sg_tz).strftime('%Y-%m-%d %H:%M:%S %Z')
                    except Exception:
                        row_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    row = row.copy()
                    row['date_time'] = row_ts
                    to_append_rows.append(row)
                    existing_questions.add(key_used)
                else:
                    # duplicate detected or no usable question; skip
                    pass

            if not to_append_rows:
                print('No new (non-duplicate) questions to append to', filename)
                return

            to_append_df = pd.DataFrame(to_append_rows)

            # Combine and save
            combined_data = pd.concat([existing_data, to_append_df], ignore_index=True)
            combined_data.to_excel(filename, index=False)
            print(f'Appended {len(to_append_df)} new rows to {filename}')

        except Exception as e:
            print(f"Error appending to {filename}: {e}")
            # fallback: write only the new non-duplicate rows
            try:
                new_data.to_excel(filename, index=False)
            except Exception as e2:
                print(f"Failed to write fallback {filename}: {e2}")
    else:
        # New file: set timestamp for all rows
        try:
            row_ts = datetime.now(sg_tz).strftime('%Y-%m-%d %H:%M:%S %Z')
        except Exception:
            row_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        new_data['date_time'] = row_ts
        new_data.to_excel(filename, index=False)

def _parse_possible_json(s):
    """If `s` is a JSON-looking string, attempt to parse and return Python object; otherwise return original."""
    if not isinstance(s, str):
        return s
    s_stripped = s.strip()
    if not s_stripped:
        return s
    if (s_stripped.startswith('{') or s_stripped.startswith('[')):
        try:
            return json.loads(s_stripped)
        except Exception:
            return s
    return s

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Invalid file type. Please upload an Excel file'}), 400
    
    # Get AI toggle setting from request
    use_llm_override = request.form.get('use_llm', 'false').lower() == 'true'
    
    # Warn if AI requested but not configured
    if use_llm_override and not aibot_available:
        app.logger.warning("⚠️  WARNING: AI processing requested but AIBot API key not configured!")
        app.logger.warning("   Add your X-ATLAS-Key to .env file to enable AI features.")
        app.logger.warning("   Falling back to rule-based processing...")
    
    try:
        # Read Excel file
        df = pd.read_excel(file)
        
        # Clean the data with AI override
        cleaned_data, stats = clean_qa_data(df, use_llm_override)
        print(f"Cleaning stats: {cleaned_data}")
        print(f"Cleaning stats: {stats}")

        # Persist cleaned results to local database.xlsx (append)
        try:
            save_database_excel(df, cleaned_data)
            print('Saved cleaned data to database.xlsx')
        except Exception as e:
            print(f'Warning: failed to save cleaned data to database.xlsx: {e}')
        
        return jsonify({
            'success': True,
            'cleaned_data': cleaned_data,
            'total_questions': len(cleaned_data),
            'duplicates_removed': stats['duplicates_removed'],
            'issues_fixed': stats['issues_fixed'],
            'sensitive_info_removed': stats['sensitive_info_removed'],
            'questions_rephrased': stats['questions_rephrased'],
            'original_count': stats['original_count']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload/stream', methods=['POST'])
def upload_file_stream():
    """Stream processing results in real-time using Server-Sent Events"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Invalid file type. Please upload an Excel file'}), 400
    
    # Get AI toggle setting from request
    use_llm_override = request.form.get('use_llm', 'false').lower() == 'true'
    
    # Read Excel file BEFORE creating generator (to avoid closed file issue)
    try:
        df = pd.read_excel(file)
    except Exception as e:
        return jsonify({'error': f'Failed to read Excel file: {str(e)}'}), 400
    
    def generate():
        try:
            total_rows = len(df)
            
            yield f"data: {json.dumps({'type': 'start', 'total': total_rows})}\\n\\n"
            
            # Process with streaming
            cleaned_data = []
            stats = {
                'original_count': total_rows,
                'duplicates_removed': 0,
                'issues_fixed': 0,
                'sensitive_info_removed': 0,
                'questions_rephrased': 0
            }
            
            for result in clean_qa_data_stream(df, use_llm_override):
                if result['type'] == 'progress':
                    cleaned_data.append(result['data'])
                    # Update stats
                    if result.get('stats'):
                        stats.update(result['stats'])
                    
                    # Send progress update
                    yield f"data: {json.dumps(result)}\\n\\n"
            
            # Save to database
            try:
                save_database_excel(df, cleaned_data)
            except Exception as e:
                app.logger.error(f'Failed to save to database: {e}')
            
            # Send completion
            yield f"data: {json.dumps({'type': 'complete', 'cleaned_data': cleaned_data, 'stats': stats, 'total_questions': len(cleaned_data)})}\\n\\n"
            
        except Exception as e:
            app.logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\\n\\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/download/excel', methods=['POST'])
def download_excel():
    try:
        data = request.json
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Cleaned Q&A')
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='cleaned_qa_data.xlsx'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.logger.info("Starting Q&A Cleaner Server...")
    app.logger.info("Server running at http://localhost:5000")
    app.run(debug=True, port=5000)
