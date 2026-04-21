with open("app/blueprints/dashboard/__init__.py", "r") as f:
    content = f.read()

route = """
@dashboard_bp.route('/upgrade')
@login_required
def upgrade():
    return render_template('dashboard/upgrade.html')
"""

if "def upgrade():" not in content:
    content += route

with open("app/blueprints/dashboard/__init__.py", "w") as f:
    f.write(content)
