import json
import boto3
import urllib.request
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Attr

# ---------------- AWS RESOURCES ---------------- #

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('price-tracker')

# ---------------- ENV VARS ---------------- #

SERPAPI_KEY = os.environ.get('SERPAPI_KEY')
GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')


# ---------------- HELPERS ---------------- #

def parse_price(value):
    """Safely parse price from str / int / float / dict"""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        try:
            return float(value.replace('$', '').replace(',', '').strip())
        except ValueError:
            return None

    if isinstance(value, dict):
        if 'value' in value:
            return parse_price(value['value'])
        if 'raw' in value:
            return parse_price(value['raw'])

    return None


def extract_price(data):
    """Safely extract price from SerpAPI response"""

    # Buybox
    buybox = data.get('buybox_winner')
    if isinstance(buybox, dict):
        price = parse_price(buybox.get('price'))
        if price is not None:
            return price

    # Product results
    product = data.get('product_results')
    if isinstance(product, dict):
        price = parse_price(product.get('price'))
        if price is not None:
            return price

    # Offers
    offers = data.get('offers')
    if isinstance(offers, list) and offers:
        first_offer = offers[0]
        if isinstance(first_offer, dict):
            price = parse_price(first_offer.get('price'))
            if price is not None:
                return price

    return None


# ---------------- LAMBDA ---------------- #

def lambda_handler(event, context):

    if not all([SERPAPI_KEY, GMAIL_USER, GMAIL_APP_PASSWORD]):
        raise ValueError("Missing required environment variables")

    response = table.scan(
        FilterExpression=Attr('is_active').eq(True)
    )
    trackers = response.get('Items', [])

    print(f"Active trackers: {len(trackers)}")

    notifications_sent = 0
    errors = 0

    for tracker in trackers:
        try:
            asin = tracker['asin']
            tracker_id = tracker['tracker_id']
            email = tracker['user_email']
            title = tracker['product_title']
            link = tracker['product_link']
            notif_type = tracker['notification_type']

            old_price = float(tracker['current_price'])

            # -------- SERPAPI CALL -------- #
            url = (
                "https://serpapi.com/search.json"
                f"?engine=amazon_product&asin={asin}&api_key={SERPAPI_KEY}"
            )

            with urllib.request.urlopen(url) as r:
                data = json.loads(r.read().decode())

            if 'error' in data:
                print(f"SerpAPI error for {asin}: {data['error']}")
                errors += 1
                continue

            new_price = extract_price(data)

            if new_price is None:
                print(f"Price not found for {asin}")
                errors += 1
                continue

            print(f"{asin}: {old_price} → {new_price}")

            # -------- NOTIFICATION LOGIC -------- #
            should_notify = False
            reason = ""

            if notif_type == "any_drop" and new_price < old_price:
                drop = old_price - new_price
                pct = (drop / old_price) * 100
                should_notify = True
                reason = f"Price dropped ${drop:.2f} ({pct:.1f}%)"

            elif notif_type == "target_price":
                target = float(tracker['target_price'])
                if new_price <= target:
                    should_notify = True
                    reason = f"Target price reached: ${target:.2f}"

            # -------- SEND EMAIL FIRST -------- #
            if should_notify:
                if not send_gmail_notification(
                    email, title, old_price, new_price, link, reason
                ):
                    errors += 1
                    continue

                notifications_sent += 1

            # -------- UPDATE DB -------- #
            table.update_item(
                Key={'tracker_id': tracker_id},
                UpdateExpression="SET current_price=:p, last_checked=:t",
                ExpressionAttributeValues={
                    ':p': Decimal(str(new_price)),
                    ':t': datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            print(f"Tracker failed ({tracker.get('tracker_id')}): {e}")
            errors += 1

    return {
        "statusCode": 200,
        "body": json.dumps({
            "checked": len(trackers),
            "notifications_sent": notifications_sent,
            "errors": errors
        })
    }


# ---------------- EMAIL ---------------- #

def send_gmail_notification(recipient, title, old_price, new_price, link, reason):

    drop = old_price - new_price
    pct = (drop / old_price) * 100

    msg = MIMEMultipart("alternative")
    msg["From"] = GMAIL_USER
    msg["To"] = recipient
    msg["Subject"] = f"🔔 Price Drop: {title[:45]}"

    msg.attach(MIMEText(
        f"{title}\n\nOld: ${old_price:.2f}\nNew: ${new_price:.2f}\n\n{link}",
        "plain"
    ))

    msg.attach(MIMEText(
        f"""
        <html><body>
        <h2>🎉 Price Drop Alert</h2>
        <p><strong>{title}</strong></p>
        <p><del>${old_price:.2f}</del> → <b>${new_price:.2f}</b></p>
        <p>{reason}</p>
        <a href="{link}">View on Amazon</a>
        </body></html>
        """,
        "html"
    ))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {recipient}")
        return True
    except Exception as e:
        print("SMTP error:", e)
        return False
