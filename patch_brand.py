with open('app/models/brand.py', 'r') as f:
    content = f.read()
if 'phone =' not in content:
    content = content.replace("email = db.Column(db.String(255), nullable=True)", "email = db.Column(db.String(255), nullable=True)\n    phone = db.Column(db.String(20), nullable=True)")
    with open('app/models/brand.py', 'w') as f:
        f.write(content)
