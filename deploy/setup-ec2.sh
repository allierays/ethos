#!/bin/bash
# Ethos Academy — EC2 setup script
# Run this ONLY if you skipped CloudFormation and launched EC2 manually.
# CloudFormation UserData runs this automatically.
#
# Usage:
#   scp -i your-key.pem deploy/setup-ec2.sh ubuntu@YOUR_EC2_IP:~
#   ssh -i your-key.pem ubuntu@YOUR_EC2_IP
#   chmod +x setup-ec2.sh && ./setup-ec2.sh

set -euo pipefail

echo "=== Creating 2GB swap ==="
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
echo "=== Swap enabled ==="

echo "=== Installing Docker ==="
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker $USER
echo "=== Docker installed ==="

echo "=== Cloning repo ==="
git clone https://github.com/allierays/ethos-academy.git ~/ethos-academy
mkdir -p ~/ethos-academy/backups

echo "=== Installing AWS CLI v2 ==="
ARCH=$(dpkg --print-architecture)
if [ "$ARCH" = "arm64" ]; then
  curl -sL https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip -o /tmp/awscliv2.zip
else
  curl -sL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/awscliv2.zip
fi
cd /tmp && unzip -oq awscliv2.zip && sudo ./aws/install
echo "=== AWS CLI installed ==="

echo "=== Setting up cron jobs ==="
(crontab -l 2>/dev/null; echo "0 1 * * * cd /home/ubuntu/ethos-academy && docker compose -f docker-compose.prod.yml exec -T app /app/.venv/bin/python -m scripts.neo4j_export /app/backups >> /var/log/ethos-backup.log 2>&1"; echo "15 1 * * * cd /home/ubuntu/ethos-academy && aws s3 sync backups/ s3://ethos-academy-backups/neo4j/ >> /var/log/ethos-backup.log 2>&1"; echo "0 2 * * * cd /home/ubuntu/ethos-academy && docker compose -f docker-compose.prod.yml exec -T app /app/.venv/bin/python -m scripts.nightly_reflection >> /var/log/ethos-nightly.log 2>&1") | crontab -
echo "=== Cron installed: backup (1 AM), S3 sync (1:15 AM), nightly reflection (2 AM) ==="

echo ""
echo "=== NEXT STEPS ==="
echo ""
echo "1. Log out and back in (for docker group):"
echo "   exit"
echo "   ssh -i your-key.pem ubuntu@YOUR_EC2_IP"
echo ""
echo "2. Create .env file:"
echo "   cd ~/ethos-academy && cp .env.example .env && nano .env"
echo "   Required: ANTHROPIC_API_KEY, NEO4J_USER=neo4j, NEO4J_PASSWORD=<strong-password>"
echo ""
echo "3. Launch:"
echo "   docker compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "4. Import Neo4j data (after containers are healthy):"
echo "   Export locally:  uv run python scripts/neo4j_export.py backups/"
echo "   Copy to server:  scp -i your-key.pem backups/neo4j-backup-*.cypher ubuntu@YOUR_EC2_IP:~/ethos/backups/"
echo "   Import on server: cat backups/<file>.cypher | docker compose -f docker-compose.prod.yml exec -T neo4j cypher-shell -u neo4j -p <password>"
echo ""
echo "5. Verify:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:3000"
echo ""
echo "6. Point DNS in GoDaddy (TTL 600):"
echo "   A record: @   → YOUR_EC2_ELASTIC_IP"
echo "   A record: api → YOUR_EC2_ELASTIC_IP"
echo "   A record: mcp → YOUR_EC2_ELASTIC_IP"
echo "   Caddy handles SSL automatically once DNS propagates."
echo ""
