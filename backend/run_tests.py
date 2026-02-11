#!/usr/bin/env python
"""
Test runner script for Django IT Management Platform.
Run from the backend directory.
"""
import os
import sys
import subprocess

# Add the backend directory to the path
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run pytest
cmd = [
    sys.executable, '-m', 'pytest', 
    'apps/frontend/tests/', 
    '-v', 
    '--tb=short',
    '--no-header',
    '-q'
]

result = subprocess.run(cmd, capture_output=False)
sys.exit(result.returncode)

