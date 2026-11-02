#!/usr/bin/env bash
# ==============================================================================
# Small Shop Inventory Management System - EC2 Bootstrap & Setup Script
# Can be run directly as EC2 UserData or inside an SSM Session Manager terminal.
# Compatible with Ubuntu 22.04 LTS / 24.04 LTS
# ==============================================================================

set -e

# Redirect all output to log file for debugging
exec > >(tee -a /var/log/inventory_setup.log) 2>&1
echo "========================================================================"
echo "Starting EC2 Automated Bootstrap at $(date)"
echo "========================================================================"

export DEBIAN_FRONTEND=noninteractive

# 1. Update OS Packages
echo "[1/8] Updating Ubuntu system packages..."
apt-get update -y
apt-get upgrade -y

# 2. Install Required Dependencies
echo "[2/8] Installing Python3, Nginx, MySQL Client, and Git..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    git \
    mysql-client \
    curl \
    jq \
    wget \
    tar

# 3. Verify / Install AWS Systems Manager (SSM) Agent
echo "[3/8] Verifying AWS Systems Manager (SSM) Agent..."
if ! systemctl is-active --quiet snap.amazon-ssm-agent.amazon-ssm-agent; then
    snap install amazon-ssm-agent --classic || true
    systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent || true
    systemctl start snap.amazon-ssm-agent.amazon-ssm-agent || true
fi
echo "  ✓ AWS SSM Agent is active."

# 4. Install Prometheus Node Exporter (for Server Telemetry)
echo "[4/8] Installing Prometheus Node Exporter..."
NODE_EXPORTER_VERSION="1.8.2"
if ! command -v node_exporter &> /dev/null; then
    wget -q https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz -O /tmp/node_exporter.tar.gz
    tar -xzf /tmp/node_exporter.tar.gz -C /tmp/
    cp /tmp/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/
    useradd -rs /bin/false node_exporter || true
    
    cat <<EOF > /etc/systemd/system/node_exporter.service
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable node_exporter
    systemctl start node_exporter
    echo "  ✓ Node Exporter running on port 9100."
fi

# 5. Create Application and Log Directories
echo "[5/8] Creating directory structure..."
APP_DIR="/opt/inventory-system"
LOG_DIR="/var/log/inventory"

mkdir -p "$APP_DIR"
mkdir -p "$LOG_DIR"
chown -R ubuntu:www-data "$LOG_DIR"
chmod -R 775 "$LOG_DIR"

# 6. Setup Python Virtual Environment
echo "[6/8] Configuring Python Virtual Environment in $APP_DIR/venv..."
if [ ! -d "$APP_DIR/venv" ]; then
    python3 -m venv "$APP_DIR/venv"
fi

# Activate and upgrade pip
"$APP_DIR/venv/bin/pip" install --upgrade pip

# If requirements.txt exists in APP_DIR, install it
if [ -f "$APP_DIR/requirements.txt" ]; then
    "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
fi

# 7. Configure Nginx Reverse Proxy
echo "[7/8] Configuring Nginx Reverse Proxy..."
if [ -f "$APP_DIR/scripts/nginx_inventory.conf" ]; then
    cp "$APP_DIR/scripts/nginx_inventory.conf" /etc/nginx/sites-available/inventory
else
    cat <<'EOF' > /etc/nginx/sites-available/inventory
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 16M;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    location /static/ {
        alias /opt/inventory-system/app/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /node-metrics {
        proxy_pass http://127.0.0.1:9100/metrics;
    }
}
EOF
fi

# Disable default site, enable inventory site
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/inventory /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx
echo "  ✓ Nginx configured and restarted."

# 8. Configure Systemd Service for Gunicorn
echo "[8/8] Configuring Gunicorn Systemd service..."
if [ -f "$APP_DIR/scripts/inventory.service" ]; then
    cp "$APP_DIR/scripts/inventory.service" /etc/systemd/system/inventory.service
else
    cat <<EOF > /etc/systemd/system/inventory.service
[Unit]
Description=Gunicorn instance to serve Small Shop Inventory System
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/opt/inventory-system
Environment="PATH=/opt/inventory-system/venv/bin"
EnvironmentFile=/opt/inventory-system/.env
ExecStart=/opt/inventory-system/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 --timeout 60 --access-logfile /var/log/inventory/access.log --error-logfile /var/log/inventory/error.log wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
fi

systemctl daemon-reload
systemctl enable inventory || true

# Fix permissions
chown -R ubuntu:www-data "$APP_DIR"

echo "========================================================================"
echo "🎉 EC2 Bootstrap Completed Successfully at $(date)"
echo "Run: systemctl restart inventory"
echo "========================================================================"
