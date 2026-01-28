#!/usr/bin/env python3
"""Fetch schedule API response for a given year/week and print JSON. No server needed."""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unified_app import create_app

app = create_app()
with app.test_client() as c:
    r = c.get("/planning/api/calendar/schedule/2026/5")
    print("Status:", r.status_code)
    data = r.get_json()
    if data:
        print(json.dumps(data, indent=2, default=str))
    else:
        print(r.data.decode())
