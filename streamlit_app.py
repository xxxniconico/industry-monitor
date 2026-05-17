#!/usr/bin/env python3
"""Streamlit Cloud entry point"""
import sys, os
_dp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard", "app.py")
_code = compile(open(_dp).read(), _dp, "exec")
# Set __file__ to dashboard/app.py so ROOT = Path(__file__).parent.parent works
_ns = {"__name__": "__main__", "__file__": _dp}
exec(_code, _ns)
