#!/usr/bin/env bash
# ==============================================================
# TwinEngine — Azure Quick Deploy Script
# ==============================================================
# Prerequisites:
#   - Azure CLI installed & logged in (az login)
#   - Docker installed & running
#
# Usage:
#   chmod +x .azure/deploy.sh
#   .azure/deploy.sh [RESOURCE_GROUP] [LOCATION]
# ==============================================================
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────
APP_NAME="twinengine"
RG="${1:-twinengine-rg}"
LOCATION="${2:-centralindia}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "══════════════════════════════════════════════════"
echo " TwinEngine — Azure Deployment"
echo " Resource Group: ${RG}"
echo " Location:       ${LOCATION}"
echo "══════════════════════════════════════════════════"

# ── Step 1: Create Resource Group ─────────────────────────────
echo ""
echo "→ Step 1: Creating resource group..."
az group create --name "${RG}" --location "${LOCATION}" --output table

# ── Step 2: Deploy Infrastructure (Bicep) ─────────────────────
echo ""
echo "→ Step 2: Deploying infrastructure via Bicep..."
echo "  (PostgreSQL, Redis, ACR, App Service — ~5 min)"

DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -base64 24)}"

DEPLOY_OUTPUT=$(az deployment group create \
    --resource-group "${RG}" \
    --template-file .azure/infra.bicep \
    --parameters appName="${APP_NAME}" dbPassword="${DB_PASSWORD}" imageTag="${IMAGE_TAG}" \
    --output json)

# Extract outputs
ACR_NAME=$(echo "${DEPLOY_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['properties']['outputs']['acrName']['value'])")
ACR_SERVER=$(echo "${DEPLOY_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['properties']['outputs']['acrLoginServer']['value'])")
WEB_APP_NAME=$(echo "${DEPLOY_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['properties']['outputs']['webAppName']['value'])")
WEB_APP_URL=$(echo "${DEPLOY_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['properties']['outputs']['webAppUrl']['value'])")

echo "  ACR:     ${ACR_SERVER}"
echo "  Web App: ${WEB_APP_NAME}"

# ── Step 3: Build & Push Docker Image ─────────────────────────
echo ""
echo "→ Step 3: Building & pushing Docker image..."
az acr login --name "${ACR_NAME}"
docker build -t "${ACR_SERVER}/${APP_NAME}:${IMAGE_TAG}" .
docker push "${ACR_SERVER}/${APP_NAME}:${IMAGE_TAG}"

# ── Step 4: Configure App Settings ───────────────────────────
echo ""
echo "→ Step 4: Setting SECRET_KEY..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
az webapp config appsettings set \
    --resource-group "${RG}" \
    --name "${WEB_APP_NAME}" \
    --settings SECRET_KEY="${SECRET_KEY}" \
    --output none

# ── Step 5: Restart & Verify ─────────────────────────────────
echo ""
echo "→ Step 5: Restarting web app..."
az webapp restart --resource-group "${RG}" --name "${WEB_APP_NAME}"

echo ""
echo "══════════════════════════════════════════════════"
echo " ✅ Deployment Complete!"
echo ""
echo " Web App:  ${WEB_APP_URL}"
echo " API Docs: ${WEB_APP_URL}/api/docs/"
echo " Admin:    ${WEB_APP_URL}/admin/"
echo ""
echo " DB Password: ${DB_PASSWORD}"
echo " (Save this — it won't be shown again)"
echo "══════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Set remaining env vars (Cloudinary, Azure OpenAI, Email):"
echo "     az webapp config appsettings set --resource-group ${RG} --name ${WEB_APP_NAME} \\"
echo "       --settings CLOUDINARY_CLOUD_NAME=... CLOUDINARY_API_KEY=... CLOUDINARY_API_SECRET=..."
echo ""
echo "  2. Create superuser:"
echo "     az webapp ssh --resource-group ${RG} --name ${WEB_APP_NAME}"
echo "     python manage.py createsuperuser"
echo ""
echo "  3. Seed demo data:"
echo "     python manage.py create_full_demo_data"
