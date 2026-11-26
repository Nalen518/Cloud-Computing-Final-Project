#!/usr/bin/env bash
# Deploys the stock tracker on the EC2 instance (Amazon Linux 2023):
# installs Docker and Compose, builds the api image, pushes it to ECR, and starts both services.
# Needs the instance profile LabInstanceProfile (for ECR) and the ECR repository items-api.
#
# Usage, in the repo folder on the instance:
#   bash scripts/deploy_ec2.sh
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
REPO_NAME="items-api"

echo "== 1. Docker, Compose and Git =="
sudo dnf install -y docker git >/dev/null
sudo systemctl enable --now docker
if ! sudo docker compose version >/dev/null 2>&1; then
  # Amazon Linux's docker package has no Compose plugin, so install the official binary.
  sudo mkdir -p /usr/local/lib/docker/cli-plugins
  sudo curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi
sudo docker compose version

echo "== 2. Settings (.env) =="
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"
IMAGE="$REGISTRY/$REPO_NAME:latest"
if [ ! -f .env ]; then
  cp .env.example .env
  # Random passwords, created on the instance only; .env is git-ignored.
  sed -i "s/^MYSQL_ROOT_PASSWORD=.*/MYSQL_ROOT_PASSWORD=$(python3 -c "import secrets; print(secrets.token_hex(16))")/" .env
  sed -i "s/^MYSQL_PASSWORD=.*/MYSQL_PASSWORD=$(python3 -c "import secrets; print(secrets.token_hex(16))")/" .env
  chmod 600 .env
  echo "Created .env with random passwords"
fi
sed -i "s|^API_IMAGE=.*|API_IMAGE=$IMAGE|" .env

echo "== 3. Build the api image and push it to ECR =="
aws ecr get-login-password --region "$REGION" | sudo docker login --username AWS --password-stdin "$REGISTRY"
sudo docker build -t "$IMAGE" app
sudo docker push "$IMAGE"

echo "== 4. Start both services =="
sudo docker compose up -d
sudo docker compose ps

echo "== 5. Health check =="
for _ in $(seq 1 30); do
  curl -fs http://localhost/health && echo && break
  sleep 2
done
curl -fs http://localhost/health >/dev/null || { echo "api is not healthy; check: sudo docker compose logs api"; exit 1; }
echo "Done. From your laptop: API_URL=http://<public IP> bash scripts/test_api.sh"
