with open("app/config.py", "r") as f:
    lines = f.readlines()

out = []
for line in lines:
    if "if not os.environ.get('DATABASE_URL'):" in line:
        out.append("    # Fallback safely to sqlite\n")
        out.append("    basedir = os.path.abspath(os.path.dirname(__file__))\n")
        out.append("    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')\n")
    elif "basedir = os.path.abspath" in line or "SQLALCHEMY_DATABASE_URI = 'sqlite" in line:
        pass
    else:
        out.append(line)

with open("app/config.py", "w") as f:
    f.writelines(out)
