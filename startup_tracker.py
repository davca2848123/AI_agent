"""Startup Failure Tracker

Tracks consecutive startup failures and enforces waiting period.
"""

import os
import time
import json

FAILURE_FILE = ".startup_failures"

def record_failure():
    """Record a startup failure."""
    data = load_failures()
    data["count"] += 1
    data["last_failure"] = time.time()
    save_failures(data)
    return data["count"]

def record_success():
    """Record successful startup (resets counter)."""
    if os.path.exists(FAILURE_FILE):
        os.remove(FAILURE_FILE)

def load_failures():
    """Load failure data."""
    if os.path.exists(FAILURE_FILE):
        try:
            with open(FAILURE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"count": 0, "last_failure": 0}

def save_failures(data):
    """Save failure data."""
    with open(FAILURE_FILE, 'w') as f:
        json.dump(data, f)

def check_should_wait(retry_limit=3, wait_hours=6):
    """Check if we should wait before starting.
    
    Returns:
        tuple: (should_wait: bool, wait_remaining_seconds: float)
    """
    data = load_failures()
    
    if data["count"] < retry_limit:
        return (False, 0)
    
    # Check if enough time has passed
    elapsed = time.time() - data["last_failure"]
    wait_seconds = wait_hours * 3600
    
    if elapsed >= wait_seconds:
        # Wait period over, reset
        record_success()
        return (False, 0)
    else:
        # Still waiting
        remaining = wait_seconds - elapsed
        return (True, remaining)
