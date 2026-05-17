#!/usr/bin/env python3
"""Streamlit Cloud entry point — runs dashboard/app.py via import."""
import sys, os, runpy

repo_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(repo_root)
sys.path.insert(0, repo_root)

# Run dashboard/app.py as if it were __main__
runpy.run_path(os.path.join(repo_root, "dashboard", "app.py"), run_name="__main__")
