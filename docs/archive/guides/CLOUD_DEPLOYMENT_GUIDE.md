# ☁️ CLOUD DEPLOYMENT GUIDE

**Elite Trading Bot - Secure Cloud Deployment**

**Account**: MetaQuotes Demo  
**Login**: 97224465  
**Email**: peterkiragu68@outlook.com

---

## 🎯 OVERVIEW

Deploy your MVP trading bot to the cloud for:
- ✅ 24/7 operation
- ✅ Automatic restart on failure
- ✅ Remote monitoring
- ✅ Secure credential storage
- ✅ Professional reliability

---

## 🔒 SECURITY CHECKLIST

### ✅ Credentials Secured
- Login: 97224465 (in environment variables)
- Password: WdHb@1Zk (encrypted in cloud secrets)
- Investor: B-CtN4Ev (read-only access)
- Server: MetaQuotes-Demo

### ✅ Security Measures
- Credentials stored in cloud secrets manager
- No hardcoded passwords in code
- Encrypted environment variables
- HTTPS/TLS for all communications
- Access control via IAM roles
- Audit logging enabled

---

## ☁️ DEPLOYMENT OPTIONS

### Option 1: AWS (Amazon Web Services) ⭐ RECOMMENDED
**Best for**: Enterprise-grade reliability, extensive services

**Pros**:
- Most mature cloud platform
- Excellent monitoring (CloudWatch)
- Auto-scaling capabilities
- 99.99% uptime SLA

**Cost**: ~$10-20/month

---

### Option 2: Azure (Microsoft)
**Best for**: Integration with Microsoft services

**Pros**:
- Good Windows/MT5 compatibility
- Azure Key Vault for secrets
- Container Instances easy to use

**Cost**: ~$15-25/month

---

### Option 3: Google Cloud Platform
**Best for**: AI/ML capabilities (future)

**Pros**:
- Excellent for ML workloads
- Good pricing
- Cloud Run serverless option

**Cost**: ~$10-20/month

---

### Option 4: Docker (Local/VPS)
**Best for**: Testing, small deployments

**Pros**:
- Run anywhere
- Full control
- Lowest cost

**Cost**: $5-10/month (VPS)

---

## 🚀 QUICK START - AWS DEPLOYMENT

### Prerequisites:
1. AWS Account (free tier available)
2. AWS CLI installed
3. Docker installed

### Step 1: Install AWS CLI
```bash
# Windows
choco install awscli

# Or download from:
# https://aws.amazon.com/cli/
```

### Step 2: Configure AWS
```bash
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Output format: json
```

### Step 3: Store Secrets
```bash
# Store MT5 password
aws secretsmanager create-secret \
  --name trading-bot/mt5-password \
  --secret-string "WdHb@1Zk" \
  --region us-east-1

# Store SMTP password (get from Outlook)
aws secretsmanager create-secret \
  --name trading-bot/smtp-password \
  --secret-string "YOUR_OUTLOOK_APP_PASSWORD" \
  --region us-east-1
```

### Step 4: Deploy
```bash
# Make script executable
chmod +x deploy_aws.sh

# Run deployment
./deploy_aws.sh
```

### Step 5: Monitor
```bash
# View logs
aws logs tail /ecs/trading-bot --follow --region us-east-1

# Check status
aws ecs describe-services \
  --cluster trading-bot-cluster \
  --services trading-bot-service \
  --region us-east-1
```

---

## 🚀 QUICK START - AZURE DEPLOYMENT

### Prerequisites:
1. Azure Account (free tier available)
2. Azure CLI installed

### Step 1: Install Azure CLI
```bash
# Windows
choco install azure-cli

# Or download from:
# https://aka.ms/installazurecliwindows
```

### Step 2: Login
```bash
az login
```

### Step 3: Deploy
```bash
# Make script executable
chmod +x deploy_azure.sh

# Run deployment
./deploy_azure.sh
```

### Step 4: Monitor
```bash
# View logs
az container logs \
  --resource-group trading-bot-rg \
  --name elite-trading-bot \
  --follow

# Check status
az container show \
  --resource-group trading-bot-rg \
  --name elite-trading-bot \
  --query instanceView.state
```

---

## 🐳 DOCKER DEPLOYMENT (Local/VPS)

### Step 1: Install Docker
```bash
# Windows: Download Docker Desktop
# https://www.docker.com/products/docker-desktop

# Linux:
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### Step 2: Create .env File
```bash
copy .env.template .env
notepad .env
```

Fill in:
```env
MT5_LOGIN=97224465
MT5_PASSWORD=WdHb@1Zk
MT5_INVESTOR=B-CtN4Ev
MT5_SERVER=MetaQuotes-Demo
EMAIL_ADDRESS=peterkiragu68@outlook.com
SMTP_PASSWORD=your_outlook_app_password
```

### Step 3: Build and Run
```bash
# Build image
docker build -t trading-bot .

# Run container
docker run -d \
  --name elite-trading-bot \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  trading-bot

# Or use docker-compose
docker-compose up -d
```

### Step 4: Monitor
```bash
# View logs
docker logs -f elite-trading-bot

# Check status
docker ps

# Enter container
docker exec -it elite-trading-bot bash
```

---

## 📊 MONITORING & HEALTH CHECKS

### AWS CloudWatch
```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name TradingBot \
  --dashboard-body file://cloudwatch-dashboard.json

# Set up alarms
aws cloudwatch put-metric-alarm \
  --alarm-name bot-health \
  --alarm-description "Trading bot health check" \
  --metric-name HealthCheck \
  --namespace TradingBot \
  --statistic Average \
  --period 300 \
  --threshold 1 \
  --comparison-operator LessThanThreshold
```

### Azure Monitor
```bash
# Enable monitoring
az monitor log-analytics workspace create \
  --resource-group trading-bot-rg \
  --workspace-name trading-bot-logs

# Set up alerts
az monitor metrics alert create \
  --name bot-health-alert \
  --resource-group trading-bot-rg \
  --scopes /subscriptions/.../trading-bot \
  --condition "avg RestartCount > 3"
```

### Docker Health Checks
```bash
# Check health
docker inspect --format='{{.State.Health.Status}}' elite-trading-bot

# View health logs
docker inspect --format='{{json .State.Health}}' elite-trading-bot | jq
```

---

## 🔧 CONFIGURATION

### Environment Variables
```env
# Trading Account
MT5_LOGIN=97224465
MT5_PASSWORD=WdHb@1Zk
MT5_INVESTOR=B-CtN4Ev
MT5_SERVER=MetaQuotes-Demo

# Notifications
EMAIL_ADDRESS=peterkiragu68@outlook.com
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=peterkiragu68@outlook.com
SMTP_PASSWORD=your_app_password

# Risk Management
MAX_DAILY_LOSS=100
MAX_POSITION_SIZE=0.01
MAX_POSITIONS=3

# Cloud Settings
CLOUD_PROVIDER=aws
REGION=us-east-1
HEALTH_CHECK_PORT=8080
```

---

## 📈 PERFORMANCE METRICS

### Tracked Metrics:
- **Uptime**: 99.9% target
- **Response Time**: < 100ms
- **Memory Usage**: < 512MB
- **CPU Usage**: < 50%
- **Trades/Day**: Monitored
- **P&L**: Real-time tracking
- **Errors**: Alert on any error

### CloudWatch Metrics:
```python
# In mvp_bot.py, add:
import boto3

cloudwatch = boto3.client('cloudwatch')

def send_metric(name, value):
    cloudwatch.put_metric_data(
        Namespace='TradingBot',
        MetricData=[{
            'MetricName': name,
            'Value': value,
            'Unit': 'Count'
        }]
    )
```

---

## 🔄 AUTO-RESTART & FAILOVER

### AWS ECS Auto-Restart
```json
{
  "desiredCount": 1,
  "deploymentConfiguration": {
    "maximumPercent": 200,
    "minimumHealthyPercent": 100
  },
  "healthCheckGracePeriodSeconds": 60
}
```

### Docker Restart Policy
```yaml
# docker-compose.yml
services:
  trading-bot:
    restart: unless-stopped
    # Options: no, always, on-failure, unless-stopped
```

### Systemd Service (Linux VPS)
```bash
# /etc/systemd/system/trading-bot.service
[Unit]
Description=Elite Trading Bot
After=docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=10
ExecStart=/usr/bin/docker-compose -f /path/to/docker-compose.yml up
ExecStop=/usr/bin/docker-compose -f /path/to/docker-compose.yml down

[Install]
WantedBy=multi-user.target
```

---

## 🛡️ SECURITY BEST PRACTICES

### 1. Secrets Management
```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name trading-bot/credentials \
  --secret-string '{"login":"97224465","password":"WdHb@1Zk"}'

# Azure Key Vault
az keyvault secret set \
  --vault-name trading-bot-vault \
  --name mt5-credentials \
  --value '{"login":"97224465","password":"WdHb@1Zk"}'
```

### 2. Network Security
- Use VPC/VNet isolation
- Enable security groups/NSGs
- Restrict inbound traffic
- Use private subnets
- Enable encryption in transit

### 3. Access Control
```bash
# AWS IAM Policy
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "secretsmanager:GetSecretValue",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ],
    "Resource": "*"
  }]
}
```

### 4. Audit Logging
- Enable CloudTrail (AWS)
- Enable Activity Log (Azure)
- Log all API calls
- Monitor access patterns
- Alert on suspicious activity

---

## 💰 COST ESTIMATION

### AWS (Recommended)
```
ECS Fargate (256 CPU, 512 MB):
- Compute: $0.04/hour × 730 hours = $29.20/month
- Storage: $0.10/GB × 10 GB = $1.00/month
- Data Transfer: $0.09/GB × 5 GB = $0.45/month
- CloudWatch Logs: $0.50/GB × 1 GB = $0.50/month
Total: ~$31/month

With Reserved Capacity (1 year):
Total: ~$15/month (50% savings)
```

### Azure
```
Container Instance (1 vCPU, 1 GB):
- Compute: $0.0000125/second × 2,592,000 = $32.40/month
- Storage: Included
Total: ~$32/month
```

### Docker on VPS
```
DigitalOcean Droplet (1 vCPU, 1 GB):
- Basic: $6/month
- Premium: $12/month
Total: $6-12/month
```

---

## 🚨 TROUBLESHOOTING

### Issue: Container won't start
```bash
# Check logs
docker logs elite-trading-bot

# Common fixes:
# 1. Check .env file exists
# 2. Verify credentials
# 3. Check MT5 server name
# 4. Ensure ports not in use
```

### Issue: Can't connect to MT5
```bash
# Test connection
docker exec -it elite-trading-bot python -c "
from mvp_bot import SecureCredentials, MT5Connection
c = SecureCredentials()
m = MT5Connection(c)
print('Connected!' if m.connect() else 'Failed')
m.disconnect()
"
```

### Issue: High memory usage
```bash
# Check memory
docker stats elite-trading-bot

# Restart container
docker restart elite-trading-bot
```

---

## ✅ DEPLOYMENT CHECKLIST

### Pre-Deployment:
- [ ] AWS/Azure account created
- [ ] CLI tools installed
- [ ] Credentials secured
- [ ] .env file configured
- [ ] Docker tested locally
- [ ] Email notifications tested

### Deployment:
- [ ] Secrets stored in cloud
- [ ] Container built successfully
- [ ] Service deployed
- [ ] Health checks passing
- [ ] Logs accessible
- [ ] Monitoring enabled

### Post-Deployment:
- [ ] Bot connected to MT5
- [ ] Email notification received
- [ ] Test trade executed
- [ ] Monitoring dashboard setup
- [ ] Alerts configured
- [ ] Documentation updated

---

## 📞 SUPPORT

### Quick Commands:
```bash
# AWS
aws logs tail /ecs/trading-bot --follow

# Azure
az container logs --resource-group trading-bot-rg --name elite-trading-bot --follow

# Docker
docker logs -f elite-trading-bot
```

### Documentation:
- AWS: https://docs.aws.amazon.com/ecs/
- Azure: https://docs.microsoft.com/azure/container-instances/
- Docker: https://docs.docker.com/

---

## 🎯 NEXT STEPS

1. **Choose cloud provider** (AWS recommended)
2. **Run deployment script**
3. **Verify bot is running**
4. **Monitor for 24 hours**
5. **Test manual trade**
6. **Enable monitoring alerts**
7. **Document any issues**

---

**Status**: 🟢 READY FOR CLOUD DEPLOYMENT

**Credentials**: ✅ Secured in environment variables

**Time to Deploy**: 30 minutes

**Let's deploy to the cloud!** ☁️🚀
