"""
AWS Lambda Function for API Gateway Proxy to Amazon Lex V2

This function receives user messages via API Gateway and forwards them
to an Amazon Lex V2 bot using the RecognizeText API.

Runtime: Python 3.10
"""

import json
import boto3
from botocore.exceptions import ClientError

# Initialize Lex V2 Runtime client
lex_client = boto3.client('lexv2-runtime')

# Lex Bot Configuration
# These values are specific to the deployed Lex bot and alias
BOT_ID = "ZUD17UCEC4"
BOT_ALIAS_ID = "UUORFDMIMY"
LOCALE_ID = "en_US"


def lambda_handler(event, context):
    """
    AWS Lambda handler for API Gateway proxy to Amazon Lex V2.
    
    This function processes incoming HTTP requests from API Gateway,
    extracts user messages, forwards them to Lex V2, and returns
    the bot's response.
    
    Args:
        event (dict): API Gateway event containing the HTTP request details
        context: Lambda context object
        
    Returns:
        dict: API Gateway proxy response with statusCode, headers, and body
    """
    try:
        # Log the incoming event for debugging
        print(f"Received API Gateway event: {json.dumps(event)}")
        
        # Validate that the request has a body
        if 'body' not in event or not event['body']:
            print("Error: Request body is missing")
            return create_error_response(
                status_code=400,
                error_message="Request body is required"
            )
        
        # Parse the JSON body from API Gateway
        try:
            body = json.loads(event['body'])
            print(f"Parsed request body: {json.dumps(body)}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            return create_error_response(
                status_code=400,
                error_message="Invalid JSON in request body"
            )
        
        # Extract required fields from the request body
        try:
            message = body['message']
            user_id = body['user_id']
        except KeyError as e:
            missing_field = str(e).strip("'")
            print(f"Missing required field: {missing_field}")
            return create_error_response(
                status_code=400,
                error_message=f"Missing required field: {missing_field}"
            )
        
        # Validate that message and user_id are not empty
        if not message or not isinstance(message, str):
            print("Error: Message field is empty or invalid")
            return create_error_response(
                status_code=400,
                error_message="Message must be a non-empty string"
            )
        
        if not user_id or not isinstance(user_id, str):
            print("Error: User ID field is empty or invalid")
            return create_error_response(
                status_code=400,
                error_message="User ID must be a non-empty string"
            )
        
        print(f"Processing message from user '{user_id}': {message}")
        
        # Call Amazon Lex V2 RecognizeText API
        try:
            lex_response = lex_client.recognize_text(
                botId=BOT_ID,
                botAliasId=BOT_ALIAS_ID,
                localeId=LOCALE_ID,
                sessionId=user_id,  # Use user_id as the session identifier
                text=message
            )
            
            print(f"Lex response received: {json.dumps(lex_response, default=str)}")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"Lex ClientError [{error_code}]: {error_message}")
            
            # Provide user-friendly error messages based on error type
            if error_code == 'ResourceNotFoundException':
                return create_error_response(
                    status_code=500,
                    error_message="Lex bot configuration error. Please contact support."
                )
            elif error_code == 'AccessDeniedException':
                return create_error_response(
                    status_code=500,
                    error_message="Permission error accessing Lex bot."
                )
            else:
                return create_error_response(
                    status_code=500,
                    error_message="Error communicating with the chatbot. Please try again."
                )
        
        except Exception as e:
            print(f"Unexpected error calling Lex: {str(e)}")
            return create_error_response(
                status_code=500,
                error_message="An unexpected error occurred. Please try again."
            )
        
        # Extract the bot's reply from the Lex response
        bot_reply = extract_bot_reply(lex_response)
        
        # Extract additional metadata from Lex response for enhanced client experience
        intent_name = lex_response.get('sessionState', {}).get('intent', {}).get('name', 'Unknown')
        intent_state = lex_response.get('sessionState', {}).get('intent', {}).get('state', 'Unknown')
        
        print(f"Bot reply: {bot_reply}")
        print(f"Intent: {intent_name}, State: {intent_state}")
        
        # Prepare the response payload
        response_payload = {
            'reply': bot_reply,
            'intent': intent_name,
            'intent_state': intent_state,
            'session_id': user_id
        }
        
        # Return successful API Gateway response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # Enable CORS
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps(response_payload)
        }
        
    except Exception as e:
        # Catch-all for any unexpected errors
        print(f"Unexpected error in lambda_handler: {str(e)}")
        return create_error_response(
            status_code=500,
            error_message="Internal server error. Please try again later."
        )


def extract_bot_reply(lex_response):
    """
    Extract the bot's reply text from the Lex V2 response.
    
    Args:
        lex_response (dict): The response from Lex V2 recognize_text API
        
    Returns:
        str: The bot's reply message or a default error message
    """
    try:
        # Check if messages exist in the response
        if 'messages' in lex_response and lex_response['messages']:
            # Extract content from the first message
            first_message = lex_response['messages'][0]
            
            if 'content' in first_message and first_message['content']:
                return first_message['content']
            else:
                print("Warning: Message exists but has no content")
                return "Sorry, I encountered a problem. Please try again."
        else:
            print("Warning: No messages in Lex response")
            return "Sorry, I encountered a problem. Please try again."
            
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error extracting bot reply: {str(e)}")
        return "Sorry, I encountered a problem. Please try again."


def create_error_response(status_code, error_message):
    """
    Create a standardized error response for API Gateway.
    
    Args:
        status_code (int): HTTP status code for the error
        error_message (str): Human-readable error message
        
    Returns:
        dict: API Gateway proxy response with error details
    """
    error_payload = {
        'error': error_message,
        'status': 'error'
    }
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(error_payload)
    }

