import subprocess
try:
    subprocess.run(["git", "add", "app/templates/dashboard/upgrade.html", "app/blueprints/dashboard/__init__.py"], check=True)
    subprocess.run(["git", "commit", "-m", "feat: complete step 10 pro plan gating and upgrade page"], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
