## API Gateway Setup

1) Go to API Gateway → Create API
2) Choose:
 HTTP API → Build
3) Configure:

    API name: price-tracker-api
    Click Next
4) Skip integrations for now → Next → Next → Create

    Create Integration:
    Click Integrations → Create
    Integration type: Lambda function
    Lambda function: add-price-tracker
    Create

5) Create Route:

    Click Routes → Create
    Method: POST
    Path: /add-tracker
    Integration: Select the Lambda integration
    Create

6)  Enable CORS:

    Click CORS
    Access-Control-Allow-Origin: *
    Access-Control-Allow-Methods: POST, OPTIONS
    Access-Control-Allow-Headers: Content-Type
    Save

7) Get API URL:

    Click Stages → $default

    Copy the Invoke URL (e.g., https://abc123.execute-api.us-east-1.amazonaws.com)