---
title: Sentinel AI Privacy Gateway
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.55.0
app_file: app.py
pinned: false
---

# 🛡️ Sentinel AI Privacy Gateway

An **Enterprise-Grade Multi-Tenant AI Security Gateway** that provides **real-time PII redaction** and **secure AI interactions**. Perfect for organizations that need to protect sensitive data while leveraging AI capabilities.

## 🚀 Features

### 🔐 **Security First**
- **Real-time PII Detection**: Emails, phones, Indian IDs (PAN/Aadhaar)
- **Multi-tenant Architecture**: Complete user data isolation
- **Secure Authentication**: Hashed passwords with salt
- **Audit Trail**: Comprehensive logging for compliance

### 🌐 **Dual Inference Support**
- **Local Ollama**: For development and private deployment
- **Hugging Face Cloud**: For scalable production deployment
- **Auto-detection**: Automatically selects best available backend

### 🎯 **Enterprise Features**
- **User Management**: Registration, login, session management
- **Privacy Dashboard**: Real-time PII blocking statistics
- **Chat History**: Persistent, encrypted conversation storage
- **Compliance Ready**: Export capabilities and audit logs

## 🛠️ Installation

### Local Development
```bash
# Clone the repository
git clone https://github.com/yourusername/sentinel-ai-gateway.git
cd sentinel-ai-gateway

# Install dependencies
pip install -r requirements.txt

# Start Ollama (for local inference)
ollama serve
ollama pull llama3.2:1b

# Run the application
streamlit run app.py
```

### Hugging Face Spaces Deployment
1. Fork this repository
2. Create a new Hugging Face Space
3. Connect your GitHub repository
4. Add `HUGGINGFACE_API_TOKEN` to Space secrets
5. Deploy! 🚀

## 🔧 Configuration

### Environment Variables
```bash
# For Hugging Face Inference
HUGGINGFACE_API_TOKEN=your_token_here

# For local development (optional)
OLLAMA_HOST=http://localhost:11434
```

## 📊 Usage

### 1. **User Registration**
- Create account with username/password
- Automatic session initialization
- Secure password hashing

### 2. **Secure Chat**
- Send messages with PII (email, phone, PAN, Aadhaar)
- Automatic redaction before AI processing
- Real-time PII blocking statistics

### 3. **Privacy Dashboard**
- Monitor PII detection rates
- View audit logs
- Export compliance reports

## 🔍 PII Detection

### Supported Types
| Type | Pattern | Example |
|------|---------|---------|
| Email | RFC 5322 | `user@domain.com` |
| Phone | Indian format | `+91-9876543210` |
| PAN | Indian format | `ABCDE1234F` |
| Aadhaar | Multiple formats | `2345-6789-0123` |

## 🚀 Deployment

### Hugging Face Spaces
This application is optimized for Hugging Face Spaces deployment:

- **CPU Basic**: Free tier available
- **GPU Support**: Enhanced performance
- **Auto-scaling**: Built-in load balancing
- **Secrets Management**: Secure API key storage

### Docker Support
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

---

**⭐ If this project helps you, please give it a star on GitHub!**

Made with ❤️ for secure AI interactions
