#!/usr/bin/env python3
"""
Thin wrapper: runs the centralized scheduled posting executor.

All date validation and publishing is handled by scheduled_posting_executor.py.
This script exists for backward compatibility (e.g. monitoring, legacy cron).
"""

import os
import sys
import importlib.util

# Add project root to path
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
sys.path.insert(0, _project_root)

if __name__ == "__main__":
    # Delegate to centralized scheduler (load by path so scripts need not be a package)
    spec = importlib.util.spec_from_file_location(
        "scheduled_posting_executor",
        os.path.join(_script_dir, "scheduled_posting_executor.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()
