#!/usr/bin/env python3
"""Streamlit Cloud entry point"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard"))
import app
app.main()
