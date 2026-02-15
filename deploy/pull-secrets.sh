#!/bin/bash
# Pull secrets from AWS Secrets Manager and write .env
# Usage: ./deploy/pull-secrets.sh [secret-name]
#
# Requires: aws cli, jq, IAM role with secretsmanager:GetSecretValue

set -euo pipefail

SECRET_NAME="${1:-ethos/production}"
ENV_FILE="${2:-.env}"

echo "Pulling secrets from ${SECRET_NAME}..."

SECRET_JSON=$(aws secretsmanager get-secret-value \
  --secret-id "$SECRET_NAME" \
  --query 'SecretString' \
  --output text)

if [ -z "$SECRET_JSON" ]; then
  echo "ERROR: No secrets found for ${SECRET_NAME}" >&2
  exit 1
fi

# Docker compose sets NEO4J_URI inside containers, so pin it here
cat > "$ENV_FILE" <<HEADER
# Auto-generated from AWS Secrets Manager: ${SECRET_NAME}
# Do not edit manually. Update secrets with:
#   aws secretsmanager put-secret-value --secret-id ${SECRET_NAME} --secret-string '...'
# Then re-run: ./deploy/pull-secrets.sh
NEO4J_URI=bolt://localhost:7694
HEADER

# Write each key=value pair from the JSON secret
echo "$SECRET_JSON" | jq -r 'to_entries[] | "\(.key)=\(.value)"' >> "$ENV_FILE"

echo "Wrote $(echo "$SECRET_JSON" | jq 'length') vars to ${ENV_FILE}"
