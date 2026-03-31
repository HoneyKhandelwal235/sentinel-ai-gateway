---
title: Sentinel AI Privacy Gateway
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: "1.31.0"
app_file: app.py
pinned: false
license: mit
---

# 🔒 AI Privacy Gateway - Enterprise Security Solution

A comprehensive, enterprise-grade AI Privacy Gateway that protects Personally Identifiable Information (PII) while enabling secure AI interactions.

## 🏗️ Architecture Overview
The system consists of three core layers:
1. **The Identity Vault (`vault.py`):** Secure SQLite storage for PII mappings.
2. **The Privacy Engine (`engine.py`):** Redacts sensitive data before it leaves your server.
3. **The Interface (`app.py`):** A modern Streamlit dashboard for secure chat.



## 🚀 Deployment Instructions

### 1. GitHub Sync
Push this code to your repository:
```bash
git add .
git commit -m "Fix: Cleaned README and added HF metadata"
git push space main --force