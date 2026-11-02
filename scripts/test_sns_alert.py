#!/usr/bin/env python3
"""Amazon SNS Low-Stock Alert Test Script.

Validates that:
1. AWS Boto3 credentials / IAM Instance Profile are active.
2. The SNS Topic ARN is reachable.
3. The email subscription receives test alert messages.

Usage:
    export SNS_TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:small-shop-low-stock-topic"
    python scripts/test_sns_alert.py
"""

import os
import sys
from dotenv import load_dotenv

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from app.services.sns_service import send_low_stock_notification


def main():
    topic_arn = os.environ.get('SNS_TOPIC_ARN', '').strip()
    region = os.environ.get('AWS_REGION', 'us-east-1')

    print("=" * 65)
    print("  AMAZON SNS LOW-STOCK ALERT VERIFICATION UTILITY")
    print("=" * 65)
    print(f"Target Region:  {region}")
    print(f"SNS Topic ARN:  {topic_arn if topic_arn else '[NOT SET - Local Simulation Mode]'}")
    print("-" * 65)

    test_product = {
        "name": "Organic Whole Milk 1L",
        "sku": "PRD-1001",
        "current_quantity": 2,
        "min_stock_level": 5
    }

    print(f"Dispatching test alert for: {test_product['name']} (SKU: {test_product['sku']})...")
    result = send_low_stock_notification(
        product_name=test_product["name"],
        sku=test_product["sku"],
        current_quantity=test_product["current_quantity"],
        min_stock_level=test_product["min_stock_level"]
    )

    print("-" * 65)
    print(f"Result Status: {result.get('status').upper()}")

    if result.get('status') == 'published':
        print("✅ SUCCESS! Message published to Amazon SNS.")
        print(f"  MessageId: {result.get('message_id')}")
        print(f"  TopicArn:  {result.get('topic_arn')}")
        print("\n👉 Check your subscribed email inbox to verify the email arrived!")
    elif result.get('status') == 'simulated':
        print("ℹ️ Running in Local Simulation Mode.")
        print("  To test real email delivery:")
        print("  1. Create an SNS Topic in AWS Console.")
        print("  2. Subscribe your email address.")
        print("  3. Set SNS_TOPIC_ARN in your .env file or environment variable:")
        print('     export SNS_TOPIC_ARN="arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:small-shop-low-stock-topic"')
        print("  4. Re-run this script!")
    else:
        print("❌ FAILED to publish alert:")
        print(f"  Error: {result.get('error')}")
        print("\nTroubleshooting tips:")
        print("  1. Check if the IAM role has sns:Publish permissions.")
        print("  2. Verify the SNS_TOPIC_ARN is correct.")

    print("=" * 65)


if __name__ == '__main__':
    main()
