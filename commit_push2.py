import subprocess

try:
    subprocess.run(["git", "add", "migrations/"], check=True)
    subprocess.run(["git", "add", "app/models/user.py", "app/blueprints/dashboard/__init__.py", "app/blueprints/payments/__init__.py"], check=True)
    subprocess.run(["git", "commit", "-m", "feat: setup subscriptions backend, razorpay webhook, and user plan expiry"], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
