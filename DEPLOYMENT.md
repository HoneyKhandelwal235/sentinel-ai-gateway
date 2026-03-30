# 🚀 Deployment Guide

## 📋 Prerequisites

- **GitHub Account**: For repository hosting
- **Hugging Face Account**: For Spaces deployment
- **Python 3.8+**: Development environment
- **Git**: Version control

## 🌐 Hugging Face Spaces Deployment

### Step 1: Prepare Your Repository
```bash
# Ensure your repository is clean
git status
git add .
git commit -m "Ready for Hugging Face deployment"
git push origin main
```

### Step 2: Create Hugging Face Space
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Choose **"Streamlit"** as SDK
4. Select **"CPU Basic"** (free tier)
5. Name your space (e.g., `sentinel-ai-gateway`)
6. Choose **"Public"** visibility

### Step 3: Connect GitHub Repository
1. In your Space, go to **"Settings"** tab
2. Under **"Repository"**, click **"Connect to GitHub"**
3. Authorize Hugging Face to access your GitHub
4. Select your `sentinel-ai-gateway` repository
5. Choose **"main"** branch
6. Click **"Connect"**

### Step 4: Configure Secrets
1. In your Space, go to **"Settings"** → **"Variables and secrets"**
2. Click **"New secret"**
3. Add `HUGGINGFACE_API_TOKEN`:
   - **Name**: `HUGGINGFACE_API_TOKEN`
   - **Value**: Your Hugging Face API token
   - **Type**: `Secret`

### Step 5: Deploy
1. Your Space will automatically build and deploy
2. Wait for the build to complete (2-5 minutes)
3. Your app will be live at: `https://your-username-sentinel-ai-gateway.hf.space`

## 🔧 Configuration Options

### Environment Variables
```bash
# Required for Hugging Face Inference
HUGGINGFACE_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Custom model
MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.2

# Optional: Debug mode
DEBUG=false
LOG_LEVEL=INFO
```

### Space Hardware
- **CPU Basic**: Free, 2 vCPU, 16GB RAM
- **CPU Upgrade**: $0.06/hour, 8 vCPU, 32GB RAM
- **GPU Basic**: $0.10/hour, 1 T4 GPU, 16GB RAM

## 🐳 Docker Deployment

### Build Docker Image
```bash
# Build the image
docker build -t sentinel-ai-gateway .

# Run locally
docker run -p 8501:8501 \
  -e HUGGINGFACE_API_TOKEN=your_token_here \
  sentinel-ai-gateway
```

### Docker Compose
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - HUGGINGFACE_API_TOKEN=${HUGGINGFACE_API_TOKEN}
    volumes:
      - ./data:/app/data
    restart: unless-stopped

volumes:
  data:
```

## ☁️ Cloud Deployment Options

### AWS ECS
```bash
# Create ECR repository
aws ecr create-repository --repository-name sentinel-ai-gateway

# Build and push
docker build -t sentinel-ai-gateway .
docker tag sentinel-ai-gateway:latest [aws-account-id].dkr.ecr.[region].amazonaws.com/sentinel-ai-gateway:latest
docker push [aws-account-id].dkr.ecr.[region].amazonaws.com/sentinel-ai-gateway:latest

# Deploy to ECS
aws ecs create-service --cluster sentinel-cluster --service-name sentinel-gateway --task-definition sentinel-task --desired-count 1
```

### Google Cloud Run
```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/[project-id]/sentinel-ai-gateway

# Deploy to Cloud Run
gcloud run deploy sentinel-ai-gateway --image gcr.io/[project-id]/sentinel-ai-gateway --platform managed
```

### Azure Container Instances
```bash
# Create resource group
az group create --name sentinel-rg --location eastus

# Deploy container
az container create \
  --resource-group sentinel-rg \
  --name sentinel-gateway \
  --image sentinel-ai-gateway:latest \
  --ports 8501 \
  --environment-variables HUGGINGFACE_API_TOKEN=your_token
```

## 🔍 Troubleshooting

### Common Issues

#### Build Failures
```bash
# Check logs in Hugging Face Space
# Go to Settings → Logs

# Common fixes:
# - Ensure requirements.txt has correct versions
# - Check for syntax errors in Python files
# - Verify all imports are available
```

#### Runtime Errors
```bash
# Check Space health
curl https://your-space.hf.space/_stcore/health

# Common fixes:
# - Verify HUGGINGFACE_API_TOKEN is set
# - Check model availability
# - Ensure sufficient memory limits
```

#### Performance Issues
```bash
# Optimize for CPU Basic:
# - Use smaller models (Mistral-7B instead of larger models)
# - Implement caching
# - Optimize PII detection patterns
```

## 📊 Monitoring

### Hugging Face Metrics
- **CPU Usage**: Monitor in Space dashboard
- **Memory Usage**: Check for memory leaks
- **Request Rate**: Monitor API limits
- **Error Rate**: Track application errors

### Custom Monitoring
```python
# Add to app.py
import time
import logging

# Performance tracking
@st.cache_data(ttl=300)  # 5 minutes
def get_performance_metrics():
    return {
        "cpu_usage": get_cpu_usage(),
        "memory_usage": get_memory_usage(),
        "active_users": get_active_users(),
        "requests_per_minute": get_request_rate()
    }
```

## 🔒 Security Considerations

### Production Hardening
1. **HTTPS Only**: Ensure SSL termination
2. **Rate Limiting**: Implement request throttling
3. **Input Validation**: Sanitize all user inputs
4. **Secrets Management**: Never commit API keys
5. **Regular Updates**: Keep dependencies updated

### Environment Security
```bash
# Use read-only secrets
st.secrets["HUGGINGFACE_API_TOKEN"]  # ✅ Correct

# Never hardcode secrets
API_TOKEN = "hf_xxxxx"  # ❌ Wrong
```

## 🚀 CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Hugging Face

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Hugging Face
        uses: huggingface/huggingfacehub-deploy@v0
        with:
          hf_token: ${{ secrets.HF_TOKEN }}
          space_name: your-username/sentinel-ai-gateway
```

### Automated Testing
```yaml
# .github/workflows/test.yml
name: Test and Deploy

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
      
      - name: Run tests
        run: pytest tests/
      
      - name: Deploy
        if: github.ref == 'refs/heads/main'
        run: |
          # Deployment commands
```

## 📈 Scaling Guidelines

### Horizontal Scaling
- **Load Balancer**: Use multiple Space replicas
- **Database**: Consider PostgreSQL for high traffic
- **Caching**: Implement Redis for session storage
- **CDN**: Use CloudFlare for static assets

### Performance Optimization
```python
# Implement connection pooling
import requests.adapters

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20
)
session.mount('https://', adapter)

# Cache PII patterns
@st.cache_data(ttl=3600)
def load_pii_patterns():
    return load_patterns_from_config()
```

## 🎯 Success Metrics

### Key Performance Indicators
- **Response Time**: <5 seconds for AI responses
- **Uptime**: >99.5% availability
- **Error Rate**: <1% of requests
- **User Satisfaction**: >4.5/5 rating

### Monitoring Setup
```python
# Add to app.py
def track_metrics():
    metrics = {
        "response_time": st.session_state.get('avg_response_time', 0),
        "error_count": st.session_state.get('error_count', 0),
        "active_users": len(get_active_sessions()),
        "pii_detections": st.session_state.get('total_pii_detected', 0)
    }
    
    # Send to monitoring service
    send_metrics_to_datadog(metrics)
```

## 🆘 Support and Maintenance

### Regular Maintenance
1. **Weekly**: Update dependencies
2. **Monthly**: Review logs and metrics
3. **Quarterly**: Security audit
4. **Annually**: Architecture review

### Emergency Procedures
1. **Down Detection**: Automated alerts
2. **Rollback**: Previous version deployment
3. **Communication**: User notification
4. **Recovery**: Service restoration

---

## 🎉 Deployment Complete!

Once deployed, your **Sentinel AI Privacy Gateway** will be:

- **🌐 Live**: Accessible via public URL
- **🔒 Secure**: PII protection enabled
- **📊 Monitored**: Performance tracking
- **🚀 Scalable**: Ready for user growth

### Next Steps
1. **Test**: Verify all functionality works
2. **Monitor**: Set up alerts and dashboards
3. **Optimize**: Tune performance based on usage
4. **Scale**: Upgrade resources as needed

**🎯 Your Enterprise AI Security Gateway is now production-ready!**
