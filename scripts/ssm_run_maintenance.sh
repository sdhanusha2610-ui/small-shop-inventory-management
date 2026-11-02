#!/usr/bin/env bash
# ==============================================================================
# Small Shop Inventory Management System - AWS Systems Manager (SSM) Utility
# Remotely manages the EC2 instance WITHOUT SSH keys or opening Port 22.
# ==============================================================================

set -e

INSTANCE_ID="${1:-$EC2_INSTANCE_ID}"
REGION="${AWS_REGION:-us-east-1}"

if [ -z "$INSTANCE_ID" ]; then
    echo "❌ Error: Instance ID is required."
    echo "Usage: ./scripts/ssm_run_maintenance.sh <INSTANCE_ID> [ACTION]"
    echo "   or: export EC2_INSTANCE_ID='i-0123456789abcdef0'"
    echo ""
    echo "Available Actions:"
    echo "  status   - View Gunicorn, Nginx, and system health status"
    echo "  restart  - Restart inventory Gunicorn and Nginx services"
    echo "  logs     - Tail the latest 30 lines of application error logs"
    echo "  shell    - Open an interactive browser/terminal Session Manager shell"
    exit 1
fi

ACTION="${2:-status}"

echo "========================================================================"
echo "AWS SYSTEMS MANAGER (SSM) REMOTE ADMINISTRATION"
echo "Target Instance:  $INSTANCE_ID"
echo "AWS Region:       $REGION"
echo "Action Requested: $ACTION"
echo "========================================================================"

case "$ACTION" in
    shell)
        echo "Initiating interactive Session Manager terminal (No Port 22 SSH needed)..."
        aws ssm start-session --target "$INSTANCE_ID" --region "$REGION"
        ;;

    status)
        echo "Querying application and service telemetry via SSM Run Command..."
        COMMAND_ID=$(aws ssm send-command \
            --instance-ids "$INSTANCE_ID" \
            --document-name "AWS-RunShellScript" \
            --comment "Check inventory system service status" \
            --parameters 'commands=[
                "echo \"=== GUNICORN SERVICE STATUS ===\"",
                "systemctl status inventory --no-pager -l | head -n 12",
                "echo \"\"",
                "echo \"=== NGINX STATUS ===\"",
                "systemctl status nginx --no-pager -l | head -n 8",
                "echo \"\"",
                "echo \"=== LOCAL HEALTH ENDPOINT ===\"",
                "curl -s http://127.0.0.1:5000/health || echo \"Health check failed!\"",
                "echo \"\"",
                "echo \"=== SYSTEM RESOURCE UTILIZATION ===\"",
                "free -h",
                "df -h / | tail -n 1"
            ]' \
            --output text \
            --query "Command.CommandId" \
            --region "$REGION")

        echo "Dispatched SSM Command ID: $COMMAND_ID"
        echo "Waiting for command execution..."
        sleep 4
        aws ssm get-command-invocation \
            --command-id "$COMMAND_ID" \
            --instance-id "$INSTANCE_ID" \
            --query "StandardOutputContent" \
            --output text \
            --region "$REGION"
        ;;

    restart)
        echo "Restarting application services via SSM Run Command..."
        COMMAND_ID=$(aws ssm send-command \
            --instance-ids "$INSTANCE_ID" \
            --document-name "AWS-RunShellScript" \
            --comment "Restart inventory Gunicorn and Nginx" \
            --parameters 'commands=[
                "systemctl restart inventory",
                "systemctl restart nginx",
                "sleep 2",
                "curl -s http://127.0.0.1:5000/health"
            ]' \
            --output text \
            --query "Command.CommandId" \
            --region "$REGION")

        echo "Dispatched SSM Command ID: $COMMAND_ID"
        sleep 4
        aws ssm get-command-invocation \
            --command-id "$COMMAND_ID" \
            --instance-id "$INSTANCE_ID" \
            --query "StandardOutputContent" \
            --output text \
            --region "$REGION"
        echo "✓ Application restarted successfully."
        ;;

    logs)
        echo "Retrieving application logs via SSM..."
        COMMAND_ID=$(aws ssm send-command \
            --instance-ids "$INSTANCE_ID" \
            --document-name "AWS-RunShellScript" \
            --comment "Retrieve inventory application logs" \
            --parameters 'commands=[
                "echo \"=== GUNICORN ACCESS LOGS (LAST 15) ===\"",
                "tail -n 15 /var/log/inventory/access.log 2>/dev/null || echo \"No access logs yet\"",
                "echo \"\"",
                "echo \"=== GUNICORN ERROR LOGS (LAST 15) ===\"",
                "tail -n 15 /var/log/inventory/error.log 2>/dev/null || echo \"No error logs\""
            ]' \
            --output text \
            --query "Command.CommandId" \
            --region "$REGION")

        echo "Dispatched SSM Command ID: $COMMAND_ID"
        sleep 3
        aws ssm get-command-invocation \
            --command-id "$COMMAND_ID" \
            --instance-id "$INSTANCE_ID" \
            --query "StandardOutputContent" \
            --output text \
            --region "$REGION"
        ;;

    *)
        echo "Unknown action '$ACTION'. Valid actions: status, restart, logs, shell."
        exit 1
        ;;
esac

echo "========================================================================"
