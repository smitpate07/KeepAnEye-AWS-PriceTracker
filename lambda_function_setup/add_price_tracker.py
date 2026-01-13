import json
import boto3
import uuid
import requests
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('price-tracker')

# Get SerpAPI key from environment variable
SERPAPI_KEY = os.environ.get('SERPAPI_KEY')

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        asin = body.get('asin')
        user_email = body.get('user_email')
        notification_type = body.get('notification_type', 'any_drop')  # 'any_drop' or 'target_price'
        target_price = body.get('target_price')  # Optional, only for target_price type
        
        # Validate inputs
        if not asin or not user_email:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({'error': 'ASIN and email are required'})
            }
        
        # Get current price from Amazon using SerpAPI GET request
        url = f"https://serpapi.com/search.json?engine=amazon_product&asin={asin}&api_key={SERPAPI_KEY}"
        
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if 'error' in data:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({'error': f'Invalid ASIN or API error: {data["error"]}'})
            }
        
        # Extract product information from product_results
        product_results = data.get('product_results', {})
        metdata_results = data.get('search_metadata', {})
        product_title = product_results.get('title', data.get('product_title', 'Unknown Product'))
        product_link = metdata_results.get('amazon_product_url', data.get('link', f'https://www.amazon.com/dp/{asin}'))
        
        # Get current price - try multiple locations in the response
        current_price = None
        
        # Method 1: Check buybox_winner
        if 'buybox_winner' in data and data['buybox_winner']:
            buybox = data['buybox_winner']
            if 'price' in buybox and buybox['price']:
                price_data = buybox['price']
                # Handle different price formats
                if isinstance(price_data, dict):
                    if 'value' in price_data:
                        current_price = float(price_data['value'])
                    elif 'raw' in price_data:
                        price_str = str(price_data['raw']).replace('$', '').replace(',', '').strip()
                        try:
                            current_price = float(price_str)
                        except ValueError:
                            pass
                elif isinstance(price_data, (int, float)):
                    current_price = float(price_data)
                elif isinstance(price_data, str):
                    price_str = price_data.replace('$', '').replace(',', '').strip()
                    try:
                        current_price = float(price_str)
                    except ValueError:
                        pass
        
        # Method 2: Check product_results
        if current_price is None and 'product_results' in data:
            product_results = data['product_results']
            if 'price' in product_results:
                price_data = product_results['price']
                if isinstance(price_data, dict) and 'value' in price_data:
                    current_price = float(price_data['value'])
                elif isinstance(price_data, str):
                    price_str = price_data.replace('$', '').replace(',', '').strip()
                    try:
                        current_price = float(price_str)
                    except ValueError:
                        pass
        
        # Method 3: Check offers array
        if current_price is None and 'offers' in data and data['offers']:
            offers = data['offers']
            if isinstance(offers, list) and len(offers) > 0:
                first_offer = offers[0]
                if 'price' in first_offer:
                    price_data = first_offer['price']
                    if isinstance(price_data, dict) and 'value' in price_data:
                        current_price = float(price_data['value'])
                    elif isinstance(price_data, str):
                        price_str = price_data.replace('$', '').replace(',', '').strip()
                        try:
                            current_price = float(price_str)
                        except ValueError:
                            pass
        
        if current_price is None:
            # Log the full response for debugging
            print(f"Could not parse price. Full response: {json.dumps(data)}")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({'error': 'Could not retrieve price for this product. It may be out of stock or unavailable.'})
            }
        
        # Validate target price if notification type is target_price
        if notification_type == 'target_price':
            if not target_price:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS'
                    },
                    'body': json.dumps({'error': 'Target price is required for target_price notification type'})
                }
            target_price = float(target_price)
            if target_price >= current_price:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS'
                    },
                    'body': json.dumps({'error': 'Target price must be lower than current price'})
                }
        
        # Create tracker item
        tracker_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'tracker_id': tracker_id,
            'asin': asin,
            'user_email': user_email,
            'product_title': product_title,
            'product_link': product_link,
            'initial_price': Decimal(str(current_price)),
            'current_price': Decimal(str(current_price)),
            'notification_type': notification_type,
            'is_active': True,
            'created_at': timestamp,
            'last_checked': timestamp
        }
        
        # Add target price if specified
        if notification_type == 'target_price':
            item['target_price'] = Decimal(str(target_price))
        
        # Save to DynamoDB
        table.put_item(Item=item)
        
        print(f"Successfully tracked product: {product_title} at ${current_price}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'message': 'Price tracker added successfully',
                'tracker_id': tracker_id,
                'product_title': product_title,
                'current_price': current_price,
                'asin': asin
            })
        }
        
    except requests.exceptions.Timeout:
        print("SerpAPI request timed out")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({'error': 'Request timed out. Please try again.'})
        }
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({'error': f'Network error: {str(e)}'})
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }