# TwinEngine Backend — Deployment Guide

> Deployable on **Azure App Service** (primary) and **Render** (free tier).

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Azure Deployment (Recommended)](#azure-deployment)
4. [Render Deployment (Free Tier)](#render-deployment)
5. [Docker (Local / Self-hosted)](#docker-local)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Post-Deployment](#post-deployment)

---

## Prerequisites

- Python 3.12+
- Docker & Docker Compose (for containerized deployment)
- Azure CLI (`az`) — for Azure deployment
- GitHub account — for CI/CD

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | Django secret key (auto-generated for Render/Azure) |
| `DEBUG` | ✅ | `False` in production |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `REDIS_URL` | ✅ | Redis connection string (Channels + Celery) |
| `ALLOWED_HOSTS` | ✅ | Comma-separated hostnames |
| `CORS_ALLOWED_ORIGINS` | ✅ | Frontend URL(s) |
| `CSRF_TRUSTED_ORIGINS` | ✅ | Frontend URL(s) |
| `DEPLOY_ENV` | ✅ | `development` / `staging` / `production` |
| `CLOUDINARY_*` | ⬜ | Cloudinary credentials (media uploads) |
| `AZURE_OPENAI_*` | ⬜ | Azure OpenAI credentials (GPT reports) |
| `EMAIL_HOST_*` | ⬜ | SMTP credentials (email notifications) |

---

## Azure Deployment

### Option A: One-Command Deploy (Quickest)

```bash
# Login to Azure
az login

# Deploy everything (PostgreSQL + Redis + ACR + App Service)
chmod +x .azure/deploy.sh
.azure/deploy.sh twinengine-rg centralindia
```

This script:
1. Creates a resource group
2. Deploys infrastructure via Bicep (PostgreSQL Flexible Server, Azure Cache for Redis, Container Registry, App Service)
3. Builds & pushes Docker image to ACR
4. Configures the web app with a generated SECRET_KEY
5. Restarts the app and outputs the live URL

### Option B: Step-by-Step Azure CLI

```bash
# 1. Create resource group
az group create --name twinengine-rg --location centralindia

# 2. Deploy infrastructure
az deployment group create \
  --resource-group twinengine-rg \
  --template-file .azure/infra.bicep \
  --parameters appName=twinengine dbPassword='YourStrongPassword123!'

# 3. Build & push Docker image
ACR_NAME=$(az acr list -g twinengine-rg --query '[0].name' -o tsv)
az acr login --name $ACR_NAME
docker build -t ${ACR_NAME}.azurecr.io/twinengine:latest .
docker push ${ACR_NAME}.azurecr.io/twinengine:latest

# 4. Set remaining secrets
WEBAPP_NAME=$(az webapp list -g twinengine-rg --query '[0].name' -o tsv)
az webapp config appsettings set -g twinengine-rg -n $WEBAPP_NAME \
  --settings \
    SECRET_KEY=$(python3 -c "import secrets;print(secrets.token_urlsafe(50))") \
    DEPLOY_ENV=production \
    CLOUDINARY_CLOUD_NAME=xxx \
    CLOUDINARY_API_KEY=xxx \
    CLOUDINARY_API_SECRET=xxx
```

### Option C: GitHub Actions Auto-Deploy

Push to `main` triggers automatic Azure deployment. Set these **GitHub Secrets**:

| Secret | Value |
|--------|-------|
| `AZURE_CREDENTIALS` | `az ad sp create-for-rbac --role contributor --scopes /subscriptions/<SUB_ID>` |
| `ACR_LOGIN_SERVER` | `twinengineacr.azurecr.io` |
| `ACR_USERNAME` | ACR admin username |
| `ACR_PASSWORD` | ACR admin password |
| `AZURE_WEBAPP_NAME` | App Service name |
| `AZURE_RESOURCE_GROUP` | Resource group name |

### Azure Architecture

```
┌─────────────────────────────────────────────────────┐
│  Azure Resource Group: twinengine-rg                │
│                                                     │
│  ┌──────────────┐   ┌──────────────────────────┐   │
│  │ Container    │   │ App Service (Linux)       │   │
│  │ Registry     │──→│ Docker: twinengine:latest │   │
│  │ (ACR)        │   │ WebSockets: Daphne ASGI   │   │
│  └──────────────┘   └────────┬─────────────────┘   │
│                              │                      │
│              ┌───────────────┼───────────────┐      │
│              │               │               │      │
│  ┌───────────▼──┐ ┌─────────▼───┐ ┌────────▼───┐  │
│  │ PostgreSQL   │ │ Redis Cache │ │ Celery     │  │
│  │ Flexible     │ │ (Basic C0)  │ │ Worker     │  │
│  │ Server (B1ms)│ │             │ │ (optional) │  │
│  └──────────────┘ └─────────────┘ └────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Render Deployment

### Quick Deploy (Blueprint)

1. Push your repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**
3. Connect your GitHub repo — Render auto-detects `render.yaml`
4. Fill in the manual env vars (Cloudinary, Azure OpenAI, Email) in Render dashboard
5. Deploy!

### Manual Deploy

1. **New Web Service** → connect GitHub repo
2. Build Command: `./build.sh`
3. Start Command: `daphne -b 0.0.0.0 -p $PORT --proxy-headers twinengine_core.asgi:application`
4. Add environment variables from `.env.example`
5. Add a PostgreSQL database (free tier)
6. For Redis: use an external provider like [Upstash](https://upstash.com/) (free tier)

---

## Docker (Local)

```bash
# Start everything (PostgreSQL + Redis + Django + Celery worker + Beat)
docker compose up -d

# Check logs
docker compose logs -f web

# Create superuser
docker compose exec web python manage.py createsuperuser

# Seed demo data
docker compose exec web python manage.py create_full_demo_data

# Stop
docker compose down

# Stop & remove volumes
docker compose down -v
```

Or use the Makefile shortcuts:
```bash
make docker-up        # Start all services
make docker-logs      # Follow web logs
make docker-shell     # Open Django shell
make docker-down      # Stop services
make docker-clean     # Stop + remove volumes
```

---

## CI/CD Pipeline

### Workflows

| Workflow | Trigger | Actions |
|----------|---------|---------|
| `ci.yml` | Push to `main`/`develop`, PRs to `main` | Lint → Test → Docker build |
| `deploy-azure.yml` | Push to `main`, manual dispatch | Build → Push to ACR → Deploy to App Service → Health check |

### Manual Trigger

```bash
gh workflow run "Deploy → Azure" --field image_tag=v2.0.1
```

---

## Post-Deployment

### 1. Create Superuser
```bash
# Azure
az webapp ssh -g twinengine-rg -n <WEBAPP_NAME>
python manage.py createsuperuser

# Render
# Use Render shell (Dashboard → Shell tab)
python manage.py createsuperuser
```

### 2. Seed Demo Data
```bash
python manage.py create_full_demo_data
```

### 3. Verify
```bash
# Health check
curl https://<YOUR_DOMAIN>/api/health/

# API docs
open https://<YOUR_DOMAIN>/api/docs/

# Admin panel
open https://<YOUR_DOMAIN>/admin/
```

### 4. Monitor Logs
```bash
# Azure
az webapp log tail -g twinengine-rg -n <WEBAPP_NAME>

# Docker
docker compose logs -f web
```
