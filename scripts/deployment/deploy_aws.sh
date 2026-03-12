#!/bin/bash
# AWS Deployment Script for Elite Trading Bot

set -e

echo "=========================================="
echo "Elite Trading Bot - AWS Deployment"
echo "=========================================="

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPO="elite-trading-bot"
ECS_CLUSTER="trading-bot-cluster"
ECS_SERVICE="trading-bot-service"
TASK_FAMILY="trading-bot-task"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Step 1: Building Docker image...${NC}"
docker build -t $ECR_REPO:latest .

echo -e "${YELLOW}Step 2: Getting AWS account ID...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO"

echo -e "${YELLOW}Step 3: Creating ECR repository (if not exists)...${NC}"
aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION

echo -e "${YELLOW}Step 4: Logging into ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | \
docker login --username AWS --password-stdin $ECR_URI

echo -e "${YELLOW}Step 5: Tagging image...${NC}"
docker tag $ECR_REPO:latest $ECR_URI:latest

echo -e "${YELLOW}Step 6: Pushing to ECR...${NC}"
docker push $ECR_URI:latest

echo -e "${YELLOW}Step 7: Creating ECS cluster (if not exists)...${NC}"
aws ecs describe-clusters --clusters $ECS_CLUSTER --region $AWS_REGION 2>/dev/null || \
aws ecs create-cluster --cluster-name $ECS_CLUSTER --region $AWS_REGION

echo -e "${YELLOW}Step 8: Registering task definition...${NC}"
cat > task-definition.json <<EOF
{
  "family": "$TASK_FAMILY",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "trading-bot",
      "image": "$ECR_URI:latest",
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/trading-bot",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {"name": "MT5_LOGIN", "value": "97224465"},
        {"name": "MT5_SERVER", "value": "MetaQuotes-Demo"},
        {"name": "EMAIL_ADDRESS", "value": "peterkiragu68@outlook.com"}
      ],
      "secrets": [
        {"name": "MT5_PASSWORD", "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:trading-bot/mt5-password"},
        {"name": "SMTP_PASSWORD", "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:trading-bot/smtp-password"}
      ]
    }
  ]
}
EOF

aws ecs register-task-definition --cli-input-json file://task-definition.json --region $AWS_REGION

echo -e "${YELLOW}Step 9: Creating CloudWatch log group...${NC}"
aws logs create-log-group --log-group-name /ecs/trading-bot --region $AWS_REGION 2>/dev/null || true

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Create secrets in AWS Secrets Manager:"
echo "   aws secretsmanager create-secret --name trading-bot/mt5-password --secret-string 'WdHb@1Zk' --region $AWS_REGION"
echo "   aws secretsmanager create-secret --name trading-bot/smtp-password --secret-string 'YOUR_SMTP_PASSWORD' --region $AWS_REGION"
echo ""
echo "2. Create ECS service:"
echo "   aws ecs create-service --cluster $ECS_CLUSTER --service-name $ECS_SERVICE --task-definition $TASK_FAMILY --desired-count 1 --launch-type FARGATE --region $AWS_REGION"
echo ""
echo "3. Monitor logs:"
echo "   aws logs tail /ecs/trading-bot --follow --region $AWS_REGION"
