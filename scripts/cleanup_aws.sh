#!/usr/bin/env bash
# ==============================================================================
# Small Shop Inventory Management System - Safe AWS Resource Teardown Script
# Prevents unexpected AWS billing by cleanly deleting all provisioned resources.
# ==============================================================================

set -e

STACK_NAME="small-shop-inventory-stack"
REGION="${AWS_REGION:-us-east-1}"

echo "========================================================================"
echo "⚠️  AWS RESOURCE TEARDOWN & CLEANUP UTILITY"
echo "========================================================================"
echo "Stack Name:  $STACK_NAME"
echo "AWS Region:  $REGION"
echo "------------------------------------------------------------------------"
echo "This will delete all AWS resources created by CloudFormation, including:"
echo "  • Amazon EC2 Web Instance"
echo "  • Amazon RDS MySQL Database"
echo "  • Amazon SNS Topic & Subscriptions"
echo "  • Custom VPC, Subnets, and Security Groups"
echo "  • IAM Roles and Instance Profiles"
echo "========================================================================"

read -p "Are you sure you want to completely tear down all resources? (y/N): " -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Teardown cancelled. No resources were affected."
    exit 0
fi

echo "Initiating CloudFormation stack deletion..."
aws cloudformation delete-stack \
    --stack-name "$STACK_NAME" \
    --region "$REGION"

echo "✓ Deletion initiated."
echo "Waiting for stack deletion to complete (this typically takes 3-6 minutes for RDS)..."

aws cloudformation wait stack-delete-complete \
    --stack-name "$STACK_NAME" \
    --region "$REGION"

echo "========================================================================"
echo "🎉 All AWS resources successfully terminated. Zero residual billing!"
echo "========================================================================"
