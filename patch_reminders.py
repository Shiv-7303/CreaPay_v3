with open("app/tasks/reminders.py", "r") as f:
    content = f.read()

if "db.session.get" not in content:
    content = content.replace("Deal.query.get(deal_id)", "db.session.get(Deal, deal_id)")

with open("app/tasks/reminders.py", "w") as f:
    f.write(content)
