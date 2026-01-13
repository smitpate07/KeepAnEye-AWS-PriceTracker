## Create DynamoDB Table

1) Go to AWS Console → DynamoDB → Create table

2) Configure:

    Table name: price-tracker
    
        Partition key: tracker_id (String)
        Sort key: Leave empty
        Table settings: Use default settings
        Click Create table

3) Add GSI (Global Secondary Index) for querying by email:
- Go to your table → Indexes tab → Create index
    - Partition key: user_email (String)
    - Index name: user_email-index
    - Click Create index