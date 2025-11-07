# Chatbot Serverless Application

This AWS SAM application creates a chatbot architecture with the following components:

## Architecture Components

### 1. DynamoDB Table (SessionTable)
- **Purpose**: Stores conversation data and session state
- **Primary Key**: `session_id` (String)
- **Billing**: Pay-per-request
- **Streams**: Enabled for real-time processing

### 2. Lambda Functions

#### ChatbotFulfillmentLambda (`src/`)
- **Runtime**: Python 3.10
- **Purpose**: Handles conversation logic and session management
- **Permissions**: DynamoDB CRUD operations on SessionTable
- **Environment**: `TABLE_NAME` (DynamoDB table name)

#### ApiProxyLambda (`src_proxy/`)
- **Runtime**: Python 3.10
- **Purpose**: Acts as a proxy between API Gateway and Amazon Lex
- **Permissions**: `lex:RecognizeText` action
- **Environment**: `LEX_BOT_ARN` (Lex bot ARN)

### 3. API Gateway (HTTP API)
- **Endpoint**: `/chat` (POST method)
- **CORS**: Enabled for web applications
- **Integration**: Triggers ApiProxyLambda

## Deployment Instructions

### Prerequisites
1. AWS CLI configured with valid credentials
2. SAM CLI installed
3. Docker Desktop running (for local development)

### Deploy the Application

1. **Update the Lex Bot ARN** in `template.yaml`:
   ```yaml
   Parameters:
     LexBotArn:
       Type: String
       Description: ARN of the Lex bot for the API proxy function
       Default: "arn:aws:lex:us-east-1:YOUR_ACCOUNT:bot:YOUR_BOT_NAME:YOUR_BOT_ALIAS"
   ```

2. **Build the application**:
   ```bash
   sam build
   ```

3. **Deploy the application**:
   ```bash
   sam deploy --guided
   ```

4. **Get the API endpoint**:
   ```bash
   sam list stack-outputs --stack-name YOUR_STACK_NAME
   ```

## API Usage

### Endpoint
```
POST https://YOUR_API_GATEWAY_URL/prod/chat
```

### Request Body
```json
{
  "message": "Hello, how are you?",
  "session_id": "unique-session-id",
  "user_id": "user123"
}
```

### Response
```json
{
  "session_id": "unique-session-id",
  "bot_response": "Hello! How can I assist you today?",
  "intent_name": "GreetingIntent",
  "fulfillment_state": "Fulfilled"
}
```

## Local Development

1. **Start local API**:
   ```bash
   sam local start-api
   ```

2. **Test locally**:
   ```bash
   curl -X POST http://localhost:3000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello", "session_id": "test-session"}'
   ```

## File Structure
```
.
├── template.yaml          # SAM template
├── src/                   # ChatbotFulfillmentLambda
│   ├── app.py
│   └── requirements.txt
├── src_proxy/             # ApiProxyLambda
│   ├── app.py
│   └── requirements.txt
└── README.md
```

## Next Steps

1. **Create your Lex bot** in the AWS Console
2. **Update the LexBotArn parameter** in template.yaml
3. **Customize the bot logic** in `src/app.py`
4. **Deploy and test** your application
5. **Integrate with your frontend** application
