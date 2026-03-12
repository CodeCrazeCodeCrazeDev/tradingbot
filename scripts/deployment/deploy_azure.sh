#!/bin/bash
# Azure Deployment Script for Elite Trading Bot

set -e

echo "=========================================="
echo "Elite Trading Bot - Azure Deployment"
echo "=========================================="

# Configuration
RESOURCE_GROUP="trading-bot-rg"
LOCATION="eastus"
ACR_NAME="elitetradingbot"
CONTAINER_NAME="trading-bot"
APP_NAME="elite-trading-bot"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Step 1: Creating resource group...${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION

echo -e "${YELLOW}Step 2: Creating Azure Container Registry...${NC}"
az acr create --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME --sku Basic

echo -e "${YELLOW}Step 3: Building and pushing image...${NC}"
az acr build --registry $ACR_NAME --image $CONTAINER_NAME:latest .

echo -e "${YELLOW}Step 4: Creating Key Vault for secrets...${NC}"
VAULT_NAME="trading-bot-vault-$(date +%s)"
az keyvault create --name $VAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

echo -e "${YELLOW}Step 5: Storing secrets...${NC}"
az keyvault secret set --vault-name $VAULT_NAME \
  --name mt5-password --value "WdHb@1Zk"

echo "Enter your Outlook app password:"
read -s SMTP_PASSWORD
az keyvault secret set --vault-name $VAULT_NAME \
  --name smtp-password --value "$SMTP_PASSWORD"

echo -e "${YELLOW}Step 6: Creating Container Instance...${NC}"
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --image $ACR_NAME.azurecr.io/$CONTAINER_NAME:latest \
  --cpu 1 --memory 1 \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $(az acr credential show --name $ACR_NAME --query username -o tsv) \
  --registry-password $(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv) \
  --environment-variables \
    MT5_LOGIN=97224465 \
    MT5_SERVER=MetaQuotes-Demo \
    EMAIL_ADDRESS=peterkiragu68@outlook.com \
  --secure-environment-variables \
    MT5_PASSWORD=WdHb@1Zk \
  --restart-policy Always \
  --ports 8080

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Monitor logs:"
echo "az container logs --resource-group $RESOURCE_GROUP --name $APP_NAME --follow"
echo ""
echo "Get container status:"
echo "az container show --resource-group $RESOURCE_GROUP --name $APP_NAME --query instanceView.state"
