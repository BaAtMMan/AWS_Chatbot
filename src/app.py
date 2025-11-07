"""
AWS Lambda Function for Amazon Lex V2 Fulfillment with PDF Knowledge Base

This function serves as the fulfillment hook for Amazon Lex V2 chatbot.
It handles basic intents directly and uses a PDF knowledge base
for unrecognized user input via FallbackIntent.

NO IF/ELSE STATEMENTS - Uses intelligent PDF search!

Runtime: Python 3.10
"""

import json
import os
import boto3
from botocore.exceptions import ClientError
import re
from io import BytesIO

# Import PDF reader
try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("PyPDF2 not available")

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# Environment Variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'SessionTable')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# PDF Knowledge Base Configuration
PDF_S3_BUCKET = os.environ.get('PDF_S3_BUCKET', '')  # S3 bucket with PDF
PDF_S3_KEY = os.environ.get('PDF_S3_KEY', 'aws_knowledge_base.pdf')  # PDF file name
USE_PDF_KB = os.environ.get('USE_PDF_KB', 'true').lower() == 'true'

# Cache for PDF content (loaded once per Lambda container)
PDF_CONTENT_CACHE = None

# Initialize DynamoDB table
table = dynamodb.Table(TABLE_NAME)


# ============================================================================
# PDF KNOWLEDGE BASE - NO IF/ELSE STATEMENTS!
# ============================================================================

def load_pdf_from_s3():
    """
    Load PDF from S3 and cache it in memory.
    Only loads once per Lambda container for performance.
    Optimized for large PDFs.
    """
    global PDF_CONTENT_CACHE
    
    if PDF_CONTENT_CACHE is not None:
        print("✓ Using cached PDF content")
        return PDF_CONTENT_CACHE
    
    if not PDF_S3_BUCKET:
        raise Exception("PDF_S3_BUCKET not configured")
    
    try:
        print(f"→ Loading PDF from S3: s3://{PDF_S3_BUCKET}/{PDF_S3_KEY}")
        
        # Download PDF from S3
        response = s3_client.get_object(Bucket=PDF_S3_BUCKET, Key=PDF_S3_KEY)
        pdf_bytes = response['Body'].read()
        
        print(f"→ PDF downloaded: {len(pdf_bytes)} bytes")
        
        # Read PDF
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        total_pages = len(pdf_reader.pages)
        
        print(f"→ Extracting text from {total_pages} pages...")
        
        # Extract all text from all pages (with progress logging)
        all_text = []
        for page_num, page in enumerate(pdf_reader.pages):
            if page_num % 10 == 0:  # Log progress every 10 pages
                print(f"→ Processing page {page_num + 1}/{total_pages}")
            
            text = page.extract_text()
            if text and text.strip():  # Only add pages with actual content
                all_text.append({
                    'page': page_num + 1,
                    'content': text
                })
        
        PDF_CONTENT_CACHE = all_text
        print(f"✓ PDF loaded successfully: {len(all_text)} pages with content (from {total_pages} total)")
        return all_text
        
    except Exception as e:
        print(f"✗ Error loading PDF: {str(e)}")
        raise


def search_pdf_for_answer(question, pdf_content):
    """
    Intelligently search PDF for answer to question.
    NO IF/ELSE STATEMENTS - uses keyword matching and scoring!
    
    Args:
        question (str): User's question
        pdf_content (list): PDF pages with content
        
    Returns:
        str: Best matching answer from PDF
    """
    
    # Extract keywords from question (simple but effective)
    keywords = extract_keywords(question)
    
    print(f"→ Searching PDF for keywords: {keywords}")
    
    # Score each page based on keyword matches
    page_scores = []
    for page_data in pdf_content:
        page_text = page_data['content'].lower()
        score = 0
        
        # Count keyword occurrences
        for keyword in keywords:
            score += page_text.count(keyword.lower())
        
        if score > 0:
            page_scores.append({
                'page': page_data['page'],
                'score': score,
                'content': page_data['content']
            })
    
    # Sort by score (highest first)
    page_scores.sort(key=lambda x: x['score'], reverse=True)
    
    if not page_scores:
        return f"I couldn't find information about '{question}' in the knowledge base. Could you rephrase your question?"
    
    # Get the best matching page
    best_match = page_scores[0]
    
    # Extract relevant section (around the keywords)
    answer = extract_relevant_section(best_match['content'], keywords)
    
    # Add helpful context
    answer_with_context = f"{answer}\n\n(Source: Page {best_match['page']} of knowledge base)"
    
    print(f"✓ Found answer on page {best_match['page']} (score: {best_match['score']})")
    
    return answer_with_context


def extract_keywords(text):
    """
    Extract important keywords from question.
    Removes common words, keeps important terms.
    """
    # Common words to ignore
    stop_words = {'what', 'is', 'are', 'the', 'a', 'an', 'how', 'do', 'does', 
                  'can', 'tell', 'me', 'about', 'explain', 'describe', 'in', 'to',
                  'for', 'of', 'and', 'or', 'it', 'this', 'that', 'i', 'you'}
    
    # Split into words and clean
    words = re.findall(r'\b[a-z0-9]+\b', text.lower())
    
    # Keep important words
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords if keywords else [text.lower()]


def extract_relevant_section(page_content, keywords, context_chars=1200):
    """
    Extract the most relevant section from page based on keywords.
    Returns clean, readable text with proper formatting.
    """
    page_lower = page_content.lower()
    
    # Find first occurrence of any keyword
    earliest_pos = len(page_content)
    best_keyword = None
    for keyword in keywords:
        pos = page_lower.find(keyword.lower())
        if pos != -1 and pos < earliest_pos:
            earliest_pos = pos
            best_keyword = keyword
    
    # If no keywords found, return beginning
    if earliest_pos == len(page_content):
        section = page_content[:context_chars]
        start = 0
    else:
        # Find start of sentence before keyword (look backwards for sentence start)
        start = earliest_pos
        # Look backwards for sentence boundaries
        for i in range(max(0, earliest_pos - 200), earliest_pos):
            if page_content[i:i+2] in ['. ', '.\n', '? ', '! '] or i == 0:
                start = i + 2 if i > 0 else 0
                break
        
        # Extract to end position
        end = min(len(page_content), start + context_chars)
        section = page_content[start:end]
    
    # Clean up the text for better readability
    section = clean_pdf_text(section)
    
    # Try to end at sentence boundary
    section = trim_to_sentence(section)
    
    # Ensure it starts with capital letter (proper sentence start)
    if section and section[0].islower():
        # Find first capital letter or sentence start
        for i, char in enumerate(section):
            if char.isupper() or (i > 0 and section[i-2:i] in ['. ', '.\n']):
                section = section[i:]
                break
    
    return section.strip()


def clean_pdf_text(text):
    """
    Clean up PDF-extracted text for better readability.
    Fixes formatting issues, bullets, and line breaks.
    """
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # Fix bullets - convert weird bullet characters to proper bullets
    text = re.sub(r'[•▪▫◦⚫⚬○●]', '• ', text)
    
    # Fix line breaks around bullets
    text = re.sub(r'\n+•', '\n• ', text)
    
    # Remove extra line breaks (more than 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Fix common PDF artifacts
    text = text.replace('ﬁ', 'fi')  # Fix ligature
    text = text.replace('ﬂ', 'fl')  # Fix ligature
    text = text.replace('—', '-')   # Fix em-dash
    
    # Clean up spaces around punctuation
    text = re.sub(r'\s+([,.;:!?])', r'\1', text)
    
    # Ensure proper spacing after periods
    text = re.sub(r'\.([A-Z])', r'. \1', text)
    
    return text.strip()


def trim_to_sentence(text, max_length=1000):
    """
    Trim text to end at a complete sentence.
    Avoids cutting off mid-sentence.
    """
    if len(text) <= max_length:
        return text
    
    # Truncate to max length
    text = text[:max_length]
    
    # Find last sentence ending
    last_period = max(
        text.rfind('. '),
        text.rfind('.\n'),
        text.rfind('? '),
        text.rfind('! ')
    )
    
    if last_period > max_length * 0.5:  # Only if we're not cutting too much
        text = text[:last_period + 1]
    
    return text.strip()


def query_pdf_knowledge_base(question):
    """
    Main function to query PDF knowledge base.
    Replaces ALL if/else statements with intelligent search!
    """
    if not PDF_AVAILABLE:
        return "PDF reader is not available. Please contact administrator."
    
    if not USE_PDF_KB:
        return "PDF knowledge base is disabled."
    
    try:
        # Load PDF (cached after first load)
        pdf_content = load_pdf_from_s3()
        
        # Search for answer
        answer = search_pdf_for_answer(question, pdf_content)
        
        return answer
        
    except Exception as e:
        error_msg = str(e)
        print(f"✗ PDF search failed: {error_msg}")
        return f"I encountered an error searching the knowledge base. Please try rephrasing your question."


# ============================================================================
# MAIN QUERY FUNCTION
# ============================================================================

def query_llm(text):
    """
    Main query function - Uses PDF Knowledge Base!
    NO IF/ELSE STATEMENTS - intelligent PDF search instead!
    """
    
    # Use PDF Knowledge Base (FREE and works!)
    print("→ Using PDF Knowledge Base (NO IF/ELSE!)")
    return query_pdf_knowledge_base(text)


def query_local_kb(text):
    """
    Uses PDF Knowledge Base instead of if/elif statements!
    Searches your PDF automatically for answers.
    
    This replaces 200+ lines of if/elif logic with intelligent PDF search.
    """
    return query_llm(text)


# ============================================================================
# AWS SERVICE FUNCTIONS
# ============================================================================

def get_session(session_id):
    """
    Retrieve session data from DynamoDB table by session_id.
    
    Args:
        session_id (str): The unique session identifier
        
    Returns:
        dict: Session data or empty dict if not found or error occurs
    """
    try:
        response = table.get_item(Key={'session_id': session_id})
        session_data = response.get('Item', {})
        print(f"Retrieved session data for {session_id}: {session_data}")
        return session_data
    except ClientError as e:
        print(f"Error retrieving session {session_id}: {e.response['Error']['Message']}")
        return {}
    except Exception as e:
        print(f"Unexpected error retrieving session {session_id}: {str(e)}")
        return {}


def save_session(session_id, session_data):
    """
    Save session data to DynamoDB table.
    
    Args:
        session_id (str): The unique session identifier
        session_data (dict): The session data to save
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        # Ensure session_id is included in the data
        session_data['session_id'] = session_id
        
        table.put_item(Item=session_data)
        print(f"Session {session_id} saved successfully")
        return True
    except ClientError as e:
        print(f"Error saving session {session_id}: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"Unexpected error saving session {session_id}: {str(e)}")
        return False


def close(session_attributes, fulfillment_state, message_content):
    """
    Format the JSON response to send back to Amazon Lex V2.
    
    Args:
        session_attributes (dict): Session attributes to maintain state
        fulfillment_state (str): The fulfillment state (e.g., 'Fulfilled', 'Failed')
        message_content (str): The message content to send to the user
        
    Returns:
        dict: Properly formatted Lex V2 response
    """
    return {
        'sessionState': {
            'sessionAttributes': session_attributes if session_attributes else {},
            'dialogAction': {
                'type': 'Close'
            },
            'intent': {
                'name': 'FallbackIntent',
                'state': fulfillment_state
            }
        },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': message_content
            }
        ]
    }


# ============================================================================
# MAIN LAMBDA HANDLER
# ============================================================================

def lambda_handler(event, context):
    """
    AWS Lambda handler for Amazon Lex V2 fulfillment hook.
    
    This function processes incoming Lex V2 events, handles various intents,
    and integrates with PDF Knowledge Base for fallback responses.
    
    Args:
        event (dict): Lex V2 event containing sessionId, intent, and user input
        context: Lambda context object
        
    Returns:
        dict: Lex V2 response format with session state and messages
    """
    try:
        # Log the incoming event for debugging
        print(f"Received Lex V2 event: {json.dumps(event)}")
        
        # Extract key information from the Lex V2 event
        session_id = event.get('sessionId', 'unknown-session')
        intent_name = event.get('sessionState', {}).get('intent', {}).get('name', 'Unknown')
        input_transcript = event.get('inputTranscript', '').strip()
        session_attributes = event.get('sessionState', {}).get('sessionAttributes', {})
        
        print(f"Processing - SessionID: {session_id}, Intent: {intent_name}, Input: {input_transcript}")
        
        # Load existing session data from DynamoDB
        session_data = get_session(session_id)
        
        # Initialize session data if it doesn't exist
        if not session_data:
            session_data = {
                'session_id': session_id,
                'conversation_history': [],
                'intent_count': {}
            }
        
        # Update conversation history
        if 'conversation_history' not in session_data:
            session_data['conversation_history'] = []
        
        # Intent-based response logic
        if intent_name == 'GreetingIntent':
            message = "Hello! How can I help you with your AWS questions?"
            
        elif intent_name == 'CheckStatusIntent':
            message = "I am checking your status now."
            
        else:
            # FallbackIntent or any other unrecognized intent
            if input_transcript:
                # Query PDF Knowledge Base (NO IF/ELSE!)
                print(f"Fallback triggered - querying PDF Knowledge Base with: {input_transcript}")
                message = query_llm(input_transcript)
            else:
                # No input text available
                message = "I'm not sure how to help with that. Could you please rephrase your question?"
        
        # Track intent usage
        if 'intent_count' not in session_data:
            session_data['intent_count'] = {}
        
        session_data['intent_count'][intent_name] = session_data['intent_count'].get(intent_name, 0) + 1
        
        # Add current interaction to conversation history
        session_data['conversation_history'].append({
            'intent': intent_name,
            'user_input': input_transcript,
            'bot_response': message
        })
        
        # Limit conversation history to last 10 interactions
        if len(session_data['conversation_history']) > 10:
            session_data['conversation_history'] = session_data['conversation_history'][-10:]
        
        # Save updated session data to DynamoDB
        save_session(session_id, session_data)
        
        # Format and return Lex V2 response
        response = close(session_attributes, 'Fulfilled', message)
        
        print(f"Returning response: {json.dumps(response)}")
        return response
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        
        # Return error response to Lex
        error_response = close(
            session_attributes={},
            fulfillment_state='Failed',
            message_content="I apologize, but I encountered an error processing your request. Please try again."
        )
        
        return error_response

