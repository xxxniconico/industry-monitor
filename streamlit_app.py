#!/usr/bin/env python3
"""Streamlit Cloud entry point — delegates to dashboard/app.py"""
import subprocess, sys, os
subprocess.check_call([sys.executable, "-m", "streamlit", "run", "dashboard/app.py", "--server.port", os.environ.get("PORT", "8501")])
