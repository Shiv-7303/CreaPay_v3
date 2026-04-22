import subprocess
try:
    subprocess.run(["git", "add", "app/blueprints/payments/__init__.py"], check=True)
    subprocess.run(["git", "commit", "-m", "fix: handle missing razorpay keys to show correct alert in frontend"], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
