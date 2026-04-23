with open("app/templates/dashboard/index.html", "r") as f:
    content = f.read()

import re

# Resolve the first conflict
content = re.sub(
    r"<<<<<<< HEAD\n\s*<button onclick=\"sendReminder\('\{\{ deal\.id \}\}'\)\" class=\"w-full text-center py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition text-sm font-medium\">\n=======\n(.*?)>>>>>>> jules-temp",
    r"\1",
    content,
    flags=re.DOTALL
)

# Resolve the second conflict
content = re.sub(
    r"<<<<<<< HEAD\n\s*async function sendReminder\(dealId\) \{\n\s*const res = await fetch\(`/deals/\$\{dealId\}/remind`, \{ method: 'POST' \}\);\n\s*if \(res\.ok\) \{\n\s*alert\(\"Reminder sent successfully!\"\);\n=======\n(.*?)",
    r"\1",
    content,
    flags=re.DOTALL
)

with open("app/templates/dashboard/index.html", "w") as f:
    f.write(content)
