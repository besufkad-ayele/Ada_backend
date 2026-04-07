"""
Keep-Alive Script for Render Free Tier
Pings the backend periodically to prevent it from sleeping.

Usage:
    python keep_alive.py

Environment Variables:
    BACKEND_URL: Your Render backend URL (required)
    PING_INTERVAL: Seconds between pings (default: 840 = 14 minutes)
"""
import requests
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")
PING_INTERVAL = int(os.getenv("PING_INTERVAL", "840"))  # 14 minutes

if not BACKEND_URL:
    raise ValueError("BACKEND_URL environment variable is required")


def ping_server():
    """Send a ping to the health endpoint."""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/health",
            timeout=30,
            headers={"User-Agent": "KeepAlive/1.0"}
        )
        
        if response.status_code == 200:
            print(f"✅ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ping successful")
            return True
        else:
            print(f"⚠️  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                  f"Unexpected status: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ping timeout")
        return False
    except Exception as e:
        print(f"❌ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ping failed: {e}")
        return False


def main():
    """Main keep-alive loop."""
    print("=" * 60)
    print("🔄 Kuraz AI Keep-Alive Service")
    print(f"   Target: {BACKEND_URL}")
    print(f"   Interval: {PING_INTERVAL} seconds ({PING_INTERVAL // 60} minutes)")
    print("=" * 60)
    
    while True:
        ping_server()
        time.sleep(PING_INTERVAL)


if __name__ == "__main__":
    main()
