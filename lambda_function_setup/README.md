## Create IAM Role for Lambda

1) Go to IAM → Roles → Create role

2) Select: AWS service → Lambda

    Attach policies:
    AWSLambdaBasicExecutionRole
    AmazonDynamoDBFullAccess
    AmazonSESFullAccess (for email)

3)  Role name: lambda-price-tracker-role
4) Create role

----
## Lambda Function 1: Add Price Tracker

1) Go to AWS Lambda → Create function
2) Function name: add-price-tracker
    Runtime: Python 3.13
    Execution role: Use existing role → lambda-price-tracker-role
    Click Create function
3) Add code in add_price_tracker.py
4) Configuration:

    Timeout: Change from 3 seconds to 30 seconds (Configuration tab)
    Add Layer for requests library:
    Click Add a layer
    Choose AWS layers
    Select AWSSDKPandas-Python39 (includes requests)
5)  Environment Variables:

    Go to Configuration → Environment variables
    Add: SERPAPI_KEY = your_actual_serpapi_key

----

## Lambda Function 2: Check Prices (Scheduled)

1) Create another Lambda function:
        Function name: check-prices-scheduled
        Runtime: Python 3.9
        Execution role: Use existing role → lambda-price-tracker-role

2) Add code mentioned in check_prices_scheduled.py

3) 
        Timeout: 60 seconds (this runs longer)
        Memory: 256 MB
4) Add requests layer (same as before)
5) Environment Variables:
       GMAIL_USER = your.email@gmail.com
        GMAIL_APP_PASSWORD = your-16-char-password
        SERPAPI_KEY = your_serpapi_key
