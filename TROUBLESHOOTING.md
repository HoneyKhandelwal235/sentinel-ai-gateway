# 🔧 Hugging Face Space Troubleshooting

## 🚨 **Current Issue: Service Unavailable**

Your Space is not loading properly. Follow these steps to fix:

## 🔍 **Step 1: Check Build Status**

1. **Visit Space Settings**: https://huggingface.co/spaces/honeyk5/sentinel-ai-gateway/settings
2. **Check "Build and Deploy" section**
3. **Look for red indicators**:
   - ❌ Build failed
   - ❌ Deployment error
   - ❌ Runtime error

## 🔍 **Step 2: Check Runtime Logs**

1. **In Settings, click "Logs" tab**
2. **Look for these errors**:
   - `ModuleNotFoundError`: Missing dependencies
   - `ImportError`: Library conflicts
   - `StreamlitSecretNotFoundError`: Secrets configuration
   - `sqlite3.OperationalError`: Database issues

## 🔧 **Common Fixes**

### **Fix 1: Requirements.txt Issues**
If you see missing package errors:

```bash
# Check if all requirements are in requirements.txt
pip install -r requirements.txt --dry-run
```

### **Fix 2: Secrets Configuration**
If you see secrets errors:

1. **Add Space Secrets**:
   - Go to Settings → Variables and secrets
   - Add: `HUGGINGFACE_API_TOKEN`
   - Value: Your actual Hugging Face API token

2. **Check README Metadata**:
   - Ensure `sdk: streamlit` is present
   - Verify `app_file: app.py` is correct

### **Fix 3: Database Issues**
If you see database errors:

```python
# The app will create database automatically
# No manual setup required
```

### **Fix 4: Resource Limits**
If app crashes on startup:

1. **Check Space Hardware**:
   - Free tier: CPU Basic, 16GB RAM
   - Your app needs more? Upgrade to CPU Upgrade

2. **Optimize App**:
   - Reduce model size
   - Add error handling
   - Implement caching

## 🚀 **Quick Re-deployment**

If all else fails:

### **Option 1: Force Rebuild**
1. **Push small change**:
   ```bash
   echo "# Small fix" >> README.md
   git add README.md
   git commit -m "Trigger rebuild"
   git push space main
   ```

### **Option 2: Create New Space**
1. **Duplicate settings** from current space
2. **Create new space** with same name
3. **Delete old space** after new one works

### **Option 3: Local Test**
```bash
# Test locally to ensure app works
streamlit run app.py
```

## 📞 **Get Help**

If issues persist:

1. **Check Hugging Face Status**: https://status.huggingface.co/
2. **Community Forum**: https://discuss.huggingface.co/
3. **GitHub Issues**: Create issue in repository

## 🎯 **Expected Working State**

When fixed, your space should show:
- ✅ **Green "Running" indicator**
- ✅ **Streamlit interface** loads
- ✅ **User registration** works
- ✅ **PII detection** functions
- ✅ **AI responses** from Hugging Face

## 🔄 **Recovery Commands**

```bash
# Check current status
git status

# Force redeploy
git push space main --force

# Reset to working version
git reset --hard HEAD~1
git push space main --force
```
