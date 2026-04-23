import subprocess
import os

try:
    subprocess.run(["git", "add", "app/templates/dashboard/index.html"], check=True)
    subprocess.run(["git", "commit", "-m", "fix: resolve razorpay button integration and dynamic modal text logic"], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
