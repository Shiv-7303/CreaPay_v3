import subprocess
try:
    subprocess.run(["git", "add", "app/blueprints/auth/__init__.py", "app/templates/dashboard/index.html"], check=True)
    subprocess.run(["git", "commit", "-m", "feat(dev): add toggle pro button in dashboard sidebar for testing"], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
