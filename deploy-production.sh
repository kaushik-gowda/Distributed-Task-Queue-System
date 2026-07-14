#!/bin/bash
# Production Deployment Script for Distributed Task Queue System
# Run this script on your production server

set -e

echo "=================================================="
echo "Production Deployment - Task Queue System"
echo "=================================================="

# Configuration
PROJECT_DIR="/opt/task-queue"
SERVICE_USER="taskqueue"
SERVICE_GROUP="taskqueue"
VENV_DIR="${PROJECT_DIR}/venv"
LOGS_DIR="/var/log/task-queue"
DATA_DIR="/var/lib/task-queue"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Prerequisites
log_info "Step 1: Checking prerequisites..."
if ! command -v python3.11 &> /dev/null; then
    log_error "Python 3.11 not found. Please install Python 3.11+"
    exit 1
fi
log_info "✓ Python 3.11 found: $(python3.11 --version)"

if ! command -v redis-cli &> /dev/null; then
    log_warn "Redis CLI not found. Make sure Redis is installed and accessible."
fi

# Step 2: Create service user
log_info "Step 2: Setting up service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    sudo useradd -r -s /bin/false "$SERVICE_USER"
    log_info "✓ Created service user: $SERVICE_USER"
else
    log_info "✓ Service user already exists: $SERVICE_USER"
fi

# Step 3: Create directories
log_info "Step 3: Creating directories..."
sudo mkdir -p "$PROJECT_DIR" "$LOGS_DIR" "$DATA_DIR"
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" "$PROJECT_DIR" "$LOGS_DIR" "$DATA_DIR"
sudo chmod 750 "$PROJECT_DIR" "$LOGS_DIR" "$DATA_DIR"
log_info "✓ Directories created and permissions set"

# Step 4: Clone/copy code
log_info "Step 4: Deploying application code..."
if [ ! -d "$PROJECT_DIR/.git" ]; then
    log_warn "Git repository not found. Assuming code is already deployed."
else
    cd "$PROJECT_DIR"
    git pull origin main
    log_info "✓ Code updated from git"
fi

# Step 5: Setup Python virtual environment
log_info "Step 5: Setting up Python virtual environment..."
python3.11 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel
pip install -r "${PROJECT_DIR}/requirements.txt"
log_info "✓ Virtual environment setup complete"

# Step 6: Create logs directory with proper permissions
log_info "Step 6: Setting up logging..."
touch "$LOGS_DIR/api.log" "$LOGS_DIR/worker.log"
sudo chown "$SERVICE_USER:$SERVICE_GROUP" "$LOGS_DIR"/*.log
sudo chmod 640 "$LOGS_DIR"/*.log
log_info "✓ Log files created"

# Step 7: Copy environment file
log_info "Step 7: Configuring environment..."
if [ ! -f "${PROJECT_DIR}/.env" ]; then
    cp "${PROJECT_DIR}/.env.production" "${PROJECT_DIR}/.env"
    log_warn "Please edit ${PROJECT_DIR}/.env with your production settings"
else
    log_info "✓ .env file already exists"
fi

# Step 8: Database initialization
log_info "Step 8: Initializing database..."
cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"
python -c "from src.db import init_db; init_db(); print('Database initialized successfully')"
log_info "✓ Database initialized"

# Step 9: Install systemd services
log_info "Step 9: Installing systemd services..."
sudo tee /etc/systemd/system/task-queue-api.service > /dev/null <<EOF
[Unit]
Description=Task Queue API Server
After=network.target redis.service
Requires=redis.service

[Service]
Type=notify
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_DIR/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:$LOGS_DIR/api.log
StandardError=append:$LOGS_DIR/api.log

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/task-queue-worker.service > /dev/null <<EOF
[Unit]
Description=Task Queue Worker
After=network.target redis.service task-queue-api.service
Requires=redis.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_DIR/bin/python worker_main.py
Restart=always
RestartSec=10
StandardOutput=append:$LOGS_DIR/worker.log
StandardError=append:$LOGS_DIR/worker.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
log_info "✓ Systemd services installed"

# Step 10: Setup log rotation
log_info "Step 10: Setting up log rotation..."
sudo tee /etc/logrotate.d/task-queue > /dev/null <<EOF
$LOGS_DIR/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 $SERVICE_USER $SERVICE_GROUP
    sharedscripts
    postrotate
        systemctl reload task-queue-api task-queue-worker 2>/dev/null || true
    endscript
}
EOF
log_info "✓ Log rotation configured"

# Step 11: Security hardening
log_info "Step 11: Applying security hardening..."
sudo chmod 600 "${PROJECT_DIR}/.env"
sudo chown "$SERVICE_USER:$SERVICE_GROUP" "${PROJECT_DIR}/.env"
log_info "✓ File permissions hardened"

# Step 12: Nginx configuration (optional)
log_info "Step 12: Creating Nginx configuration (optional)..."
sudo tee /etc/nginx/sites-available/task-queue > /dev/null <<'EOF'
upstream task_queue_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name task-queue.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name task-queue.example.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/task-queue.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/task-queue.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy settings
    location / {
        proxy_pass http://task_queue_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }
    
    # API documentation
    location /docs {
        proxy_pass http://task_queue_backend/docs;
        proxy_set_header Host $host;
    }
    
    # Metrics (restrict access)
    location /metrics {
        allow 10.0.0.0/8;
        deny all;
        proxy_pass http://task_queue_backend/metrics;
    }
}
EOF
log_info "✓ Nginx configuration created at /etc/nginx/sites-available/task-queue"
log_warn "Don't forget to enable the site: sudo ln -s /etc/nginx/sites-available/task-queue /etc/nginx/sites-enabled/"

echo ""
echo "=================================================="
log_info "Deployment complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit ${PROJECT_DIR}/.env with your production settings"
echo "2. Configure Nginx (if using):"
echo "   sudo ln -s /etc/nginx/sites-available/task-queue /etc/nginx/sites-enabled/"
echo "   sudo nginx -t && sudo systemctl reload nginx"
echo "3. Start services:"
echo "   sudo systemctl start task-queue-api"
echo "   sudo systemctl start task-queue-worker"
echo "4. Enable on boot:"
echo "   sudo systemctl enable task-queue-api"
echo "   sudo systemctl enable task-queue-worker"
echo "5. Monitor logs:"
echo "   sudo tail -f $LOGS_DIR/api.log"
echo "   sudo tail -f $LOGS_DIR/worker.log"
echo ""
