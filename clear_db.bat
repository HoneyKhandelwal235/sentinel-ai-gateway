@echo off
taskkill /f /im streamlit.exe >nul 2>&1
timeout /t 2 >nul
del /f /q identity_vault.db* >nul 2>&1
echo Database cleared successfully
