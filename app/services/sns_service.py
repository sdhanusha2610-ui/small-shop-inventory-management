import logging
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


def get_sns_client(region_name: str = None):
    """Initializes and returns a Boto3 SNS client.
    On EC2, Boto3 automatically retrieves IAM Instance Profile credentials.
    Locally, it uses ~/.aws/credentials or environment variables.
    """
    region = region_name or os.environ.get('AWS_REGION', 'us-east-1')
    try:
        return boto3.client('sns', region_name=region)
    except Exception as e:
        logger.warning(f"Failed to create Boto3 SNS client: {e}")
        return None


def send_low_stock_notification(product_name: str, sku: str, current_quantity: int, min_stock_level: int) -> dict:
    """Publishes a low-stock alert to an Amazon SNS Topic.
    
    Args:
        product_name: Name of the product
        sku: SKU/Barcode of the product
        current_quantity: Units remaining
        min_stock_level: Configured minimum threshold
        
    Returns:
        dict with status ('published', 'simulated', 'failed') and details
    """
    topic_arn = os.environ.get('SNS_TOPIC_ARN', '').strip()
    enable_sns = os.environ.get('ENABLE_SNS_ALERTS', 'true').lower() in ('true', '1', 'yes')

    subject = f"⚠️ [AWS ALERT] Low Stock Warning: {product_name}"
    message = (
        f"INVENTORY ALERT NOTIFICATION\n"
        f"----------------------------------------\n"
        f"Product Name:    {product_name}\n"
        f"SKU Code:        {sku}\n"
        f"Current Stock:   {current_quantity} units remaining\n"
        f"Minimum Level:   {min_stock_level} units threshold\n"
        f"Status:          ACTION REQUIRED - Please reorder immediately.\n"
        f"----------------------------------------\n"
        f"Dispatched by:   Small Shop Inventory System\n"
        f"Cloud Service:   Amazon Simple Notification Service (SNS)\n"
    )

    # If SNS is disabled or topic ARN not set (e.g. running purely in local mock mode)
    if not enable_sns or not topic_arn:
        logger.info(
            f"[AWS SNS SIMULATION] Alert triggered for {product_name} (SKU: {sku}). "
            f"Stock: {current_quantity}/{min_stock_level}. (SNS_TOPIC_ARN not set)."
        )
        return {
            "status": "simulated",
            "message": f"Simulated alert: Product '{product_name}' dropped to {current_quantity} units."
        }

    # Real AWS SNS Publish
    sns_client = get_sns_client()
    if not sns_client:
        logger.error("Boto3 SNS client is unavailable.")
        return {"status": "failed", "error": "Boto3 client unavailable"}

    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject[:100],  # SNS subject max 100 characters
            Message=message
        )
        message_id = response.get('MessageId')
        logger.info(f"Successfully published SNS alert {message_id} to {topic_arn}")
        return {
            "status": "published",
            "message_id": message_id,
            "topic_arn": topic_arn
        }
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Error publishing to AWS SNS topic {topic_arn}: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }
