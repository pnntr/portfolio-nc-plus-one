#!/bin/bash -xe

echo '[install] starting install script' | systemd-cat -p info

# Log all output to a file and the system console
exec > >(tee -a /var/log/user-data.log) 2>&1

SECRET_ARN="${SECRET_ARN:?SECRET_ARN not set}"
export DB_HOST="${DB_HOST:?DB_HOST not set}"

PROJECT_REPO_LINK="https://github.com/pnntr/portfolio-nc-plus-one.git"
PROJECT_PATH="/home/ubuntu/main_repo"

# Stop on errors, undefined variables, and failed pipelines
set -Eeuo pipefail

# Capture failures
trap 'EXIT_CODE=$?;
      echo "========================================";
      echo "ERROR: User-data script failed";
      echo "Line: ${LINENO}";
      echo "Command: ${BASH_COMMAND}";
      echo "Exit code: ${EXIT_CODE}";
      echo "Timestamp: $(date)";
      echo "========================================";
      exit "$EXIT_CODE"' ERR

echo "Starting EC2 user-data script at $(date)"

echo '[install] starting update and upgrade' | systemd-cat -p info
apt update && sudo apt upgrade -y

# General deps
echo '[install] starting deps install' | systemd-cat -p info
apt install -y git curl make iptables awscli jq python3.14-venv postgresql-client

# Routing rules for web server
echo '[install] starting iptables configuration' | systemd-cat -p info
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8000
sudo iptables -t nat -A OUTPUT \
  -p tcp -d 127.0.0.1 --dport 80 \
  -j REDIRECT --to-ports 8000

# Project: Setup github token
echo '[install] token taking' | systemd-cat -p info
TOKEN=$(aws secretsmanager get-secret-value \
  --secret-id github/deploy-token \
  --region eu-west-2 \
  --query SecretString \
  --output text | jq -r '.token')

## Avoid putting the token in the repository URL
export GIT_TERMINAL_PROMPT=0

# Project: clone
echo '[install] starting project cloning' | systemd-cat -p info
git -c http.extraheader="AUTHORIZATION: basic $(printf 'x-access-token:%s' "$TOKEN" | base64 -w0)" \
  clone ${PROJECT_REPO_LINK} ${PROJECT_PATH}

unset TOKEN

# Project: install and run
cd ${PROJECT_PATH}
echo '[install] installing project requirements' | systemd-cat -p info
make requirements

# Project: get DB env vars
echo "Retrieving PostgreSQL credentials from AWS Secrets Manager..."

SECRET=$(aws secretsmanager get-secret-value \
    --secret-id "${SECRET_ARN}" \
    --region "eu-west-2" \
    --query SecretString \
    --output text)

DB_USER=$(echo "$SECRET" | jq -r '.username')
DB_PASSWORD=$(echo "$SECRET" | jq -r '.password')
DB_HOST=$DB_HOST
DB_PORT="5432"
DB_DB="toy"

cat > .env <<EOF
DB_USER=$(echo "$SECRET" | jq -r '.username')
DB_PASSWORD=$(echo "$SECRET" | jq -r '.password')
DB_HOST=$DB_HOST
DB_PORT="5432"
DB_DB="toy"
EOF

chmod 600 .env

unset SECRET

echo "Creating database"
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_DB" \
    -f src/data/seed.sql

echo "Seeding database"
python db/utils.py

echo "Starting application..."

exec uvicorn main:app
