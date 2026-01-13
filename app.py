import streamlit as st
import requests
import json
import re
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Get the API Gateway URL from the environment variable
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL")

# Page config
st.set_page_config(
    page_title="KeepAnEye - Amazon Price Tracker",
    page_icon="🛒",
    layout="centered"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #FF9900;
        padding: 20px 0;
    }
    .info-box {
        background-color: #E7F3E7;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #007600;
        margin: 20px 0;
    }
    .warning-box {
        background-color: #FFF3CD;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #FFC107;
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🛒 KeepAnEye - AWS Price Tracker </h1>', unsafe_allow_html=True)
st.markdown("### Track Amazon product prices and get notified when they drop!")

# Info box
st.markdown("""
<div class="info-box">
    <strong>How it works:</strong><br>
    1. Enter the product ASIN and your email<br>
    2. Choose notification preference<br>
    3. We'll check prices every 12 hours<br>
    4. Get email alerts when prices drop!
</div>
""", unsafe_allow_html=True)

# Helper function to extract ASIN
def extract_asin(url_or_asin):
    """Extract ASIN from Amazon URL or return as-is if already ASIN"""
    # If it's already a 10-character alphanumeric ASIN
    if re.match(r'^[A-Z0-9]{10}$', url_or_asin):
        return url_or_asin
    
    # Try to extract from URL
    patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/gp/product/([A-Z0-9]{10})',
        r'/product/([A-Z0-9]{10})',
        r'ASIN=([A-Z0-9]{10})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_asin)
        if match:
            return match.group(1)
    
    return None

# Input section
st.markdown("---")
st.markdown("### 📦 Product Information")

asin_input = st.text_input(
    "Amazon Product URL or ASIN",
    placeholder="e.g., https://www.amazon.com/dp/B08N5WRWNW or B08N5WRWNW",
    help="Enter the full Amazon product URL or just the 10-character ASIN code"
)

email = st.text_input(
    "Your Email Address",
    placeholder="your.email@example.com",
    help="We'll send price drop notifications to this email"
)

# Notification preferences
st.markdown("### 🔔 Notification Preferences")

notification_type = st.radio(
    "When should we notify you?",
    options=["any_drop", "target_price"],
    format_func=lambda x: "Any price drop below signup price" if x == "any_drop" else "Only when price reaches my target",
    help="Choose how you want to be notified about price changes"
)

target_price = None
if notification_type == "target_price":
    target_price = st.number_input(
        "Target Price ($)",
        min_value=0.01,
        step=0.01,
        format="%.2f",
        help="You'll be notified when the price drops to or below this amount"
    )

# Submit button
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    submit_button = st.button("🚀 Start Tracking", use_container_width=True, type="primary",disabled=True)

# Process submission
if submit_button:
    # Validate inputs
    if not asin_input or not email:
        st.error("❌ Please fill in all required fields (ASIN and Email)")
    elif not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        st.error("❌ Please enter a valid email address")
    else:
        # Extract ASIN
        asin = extract_asin(asin_input)
        
        if not asin:
            st.error("❌ Invalid ASIN or URL. Please check and try again.")
        else:
            # Show loading spinner
            with st.spinner("🔍 Fetching product information and setting up tracker..."):
                try:
                    # Prepare payload
                    payload = {
                        "asin": asin,
                        "user_email": email,
                        "notification_type": notification_type
                    }
                    
                    if notification_type == "target_price":
                        payload["target_price"] = target_price
                    
                    # Make API request
                    response = requests.post(
                        API_GATEWAY_URL,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ Price tracker successfully created!")
                        
                        # Show product details
                        st.markdown("---")
                        st.markdown("### 📊 Tracking Details")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Current Price", f"${data['current_price']:.2f}")
                        with col2:
                            st.metric("ASIN", data['asin'])
                        
                        st.info(f"**Product:** {data['product_title']}")
                        
                        if notification_type == "target_price":
                            st.info(f"🎯 You'll be notified when the price drops to ${target_price:.2f} or below")
                        else:
                            st.info(f"📉 You'll be notified of any price drop below ${data['current_price']:.2f}")
                        
                        st.markdown("""
                        <div class="info-box">
                            <strong>What happens next?</strong><br>
                            • We'll check the price every 12 hours<br>
                            • You'll receive an email when the price drops based on your preference<br>
                            • The email will include the new price and a direct link to the product
                        </div>
                        """, unsafe_allow_html=True)
                        
                    else:
                        error_data = response.json()
                        st.error(f"❌ Error: {error_data.get('error', 'Unknown error occurred')}")
                        
                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. Please try again.")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Network error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")

# Footer
st.markdown("---")

# How to find ASIN section
with st.expander("❓ How to find a product's ASIN?"):
    st.markdown("""
    **Method 1: From the URL**
    - Look for the 10-character code after `/dp/` in the Amazon URL
    - Example: `https://www.amazon.com/dp/B08N5WRWNW` → ASIN is `B08N5WRWNW`
    
    **Method 2: From the Product Page**
    - Scroll down to "Product Information" or "Product Details"
    - Look for "ASIN" in the list
    
    **Method 3: Use the full URL**
    - Just paste the entire Amazon product URL, we'll extract the ASIN automatically!
    """)