from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import re
import io
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize AIBot API (Govtech)
USE_LLM = os.getenv('USE_LLM', 'false').lower() == 'true'
AIBOT_API_KEY = os.getenv('AIBOT_API_KEY')
AIBOT_API_URL = os.getenv('AIBOT_API_URL', 'https://api.uat.aibots.gov.sg/v1.0/api')
AIBOT_MODEL = os.getenv('AIBOT_MODEL', 'azure~openai.gpt-4o-mini')

if USE_LLM and AIBOT_API_KEY and AIBOT_API_KEY != 'your_api_key_here':
    aibot_available = True
    print("✓ LLM features enabled (Govtech AIBot)")
else:
    aibot_available = False
    USE_LLM = False
    print("✓ Rule-based processing only")

def call_aibot(prompt, max_tokens=150, temperature=0.3):
    """Call Govtech AIBot API"""
    if not aibot_available:
        return None
    
    try:
        headers = {
            'X-ATLAS-Key': AIBOT_API_KEY,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': AIBOT_MODEL,
            'messages': [{
                'role': 'user',
                'content': prompt
            }],
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        response = requests.post(AIBOT_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        # Parse AIBot response format
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content'].strip()
        elif 'response' in result:
            return result['response'].strip()
        elif isinstance(result, str):
            return result.strip()
        return None
    except Exception as e:
        print(f"AIBot API error: {e}")
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
    if use_llm_now:
        if aibot_available:
            try:
                prompt = f"""You are a medical Q&A standardizer. Rephrase questions to be generic, professional, and suitable for a healthcare knowledge base. Remove personal pronouns. Keep questions concise.

Rephrase this question: {question}

Respond with only the rephrased question."""
                rephrased = call_aibot(prompt, max_tokens=100, temperature=0.3)
                if rephrased and rephrased.endswith('?'):
                    return rephrased
            except Exception as e:
                print(f"AIBot error: {e}, falling back to rules")
        else:
            print("⚠️  AI requested but AIBot API key not configured. Using rule-based processing.")
    
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
    
    return rephrased

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
                answer = call_aibot(prompt, max_tokens=5, temperature=0)
                if answer:
                    return 'yes' in answer.lower()
            except Exception as e:
                print(f"AIBot similarity error: {e}, falling back to rules")
        else:
            print("⚠️  AI requested but AIBot API key not configured. Using word-overlap similarity.")
    
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
    answer_col = None
    category_col = None
    
    # Look for question, answer, and category columns
    for col in columns:
        col_lower = str(col).lower()
        if 'question' in col_lower or 'q' == col_lower:
            question_col = col
        elif 'answer' in col_lower or 'a' == col_lower or 'ans' in col_lower:
            answer_col = col
        elif 'topic' in col_lower or 'category' in col_lower or 'cat' in col_lower or 'subject' in col_lower:
            category_col = col
    
    # If not found, use first columns
    if question_col is None and len(columns) > 0:
        question_col = columns[0]
    if answer_col is None and len(columns) > 1:
        answer_col = columns[1]
    if category_col is None and len(columns) > 2:
        category_col = columns[2]
    
    if question_col is None or answer_col is None:
        raise ValueError("Could not identify question and answer columns")
    
    # Create new dataframe with cleaned data
    cleaned_data = []
    seen_questions = []
    
    for idx, row in df.iterrows():
        question = clean_text(row[question_col])
        answer = clean_text(row[answer_col])
        
        # Get category or auto-categorize using LLM if enabled
        if category_col and category_col in df.columns and pd.notna(row[category_col]):
            category = clean_text(row[category_col])
        elif use_llm_for_this_request and aibot_available:
            try:
                prompt = f"""You are a medical topic categorizer. Respond with only ONE category from: Fever Management, Chronic Conditions, Diabetes, Cardiac Health, Infectious Diseases, Medication, Pain Management, First Aid, Pediatrics, Mental Health, Nutrition, Vaccinations, or General.

Categorize this question: {question}

Respond with ONLY the category name."""
                category = call_aibot(prompt, max_tokens=20, temperature=0)
                if not category:
                    category = "General"
            except Exception as e:
                category = "General"
        else:
            category = "General"
        
        # Skip empty rows
        if not question or not answer:
            stats['issues_fixed'] += 1
            continue
        
        # Skip very short questions/answers
        if len(question) < 3 or len(answer) < 3:
            stats['issues_fixed'] += 1
            continue
        
        # Remove sensitive information from both question and answer
        original_question = question
        original_answer = answer
        
        question = remove_sensitive_info(question)
        answer = remove_sensitive_info(answer)
        
        if question != original_question or answer != original_answer:
            stats['sensitive_info_removed'] += 1
        
        # Rephrase question for standardization
        rephrased_question = rephrase_question(question, use_llm_for_this_request)
        if rephrased_question != question:
            stats['questions_rephrased'] += 1
            question = rephrased_question
        
        # Check for similar questions (more aggressive duplicate detection)
        is_duplicate = False
        for seen_q in seen_questions:
            if is_similar_question(question, seen_q, 0.8, use_llm_for_this_request):
                is_duplicate = True
                stats['duplicates_removed'] += 1
                break
        
        if is_duplicate:
            continue
        
        seen_questions.append(question)
        cleaned_data.append({
            'category': category,
            'question': question,
            'answer': answer
        })
    
    return cleaned_data, stats

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
        print("⚠️  WARNING: AI processing requested but AIBot API key not configured!")
        print("   Add your X-ATLAS-Key to .env file to enable AI features.")
        print("   Falling back to rule-based processing...")
    
    try:
        # Read Excel file
        df = pd.read_excel(file)
        
        # Clean the data with AI override
        cleaned_data, stats = clean_qa_data(df, use_llm_override)
        
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
    print("Starting Q&A Cleaner Server...")
    print("Server running at http://localhost:5000")
    app.run(debug=True, port=5000)
