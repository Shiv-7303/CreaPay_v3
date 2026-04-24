import sys

with open("app/templates/dashboard/index.html", "r") as f:
    html = f.read()

# Re-inject the impersonation banner manually if it got removed during restore
banner = """    {% if session.get('impersonator_id') %}
    <div class="bg-red-600 text-white text-center py-2 px-4 flex justify-between items-center z-50">
        <span class="font-medium text-sm">⚠️ Impersonating: {{ current_user.email }}</span>
        <form action="{{ url_for('admin.stop_impersonation') }}" method="POST" class="inline">
            <button type="submit" class="bg-white text-red-600 hover:bg-gray-100 text-xs font-bold py-1 px-3 rounded shadow-sm transition">
                Return to Admin
            </button>
        </form>
    </div>
    {% endif %}"""

if "session.get('impersonator_id')" not in html:
    html = html.replace('<body class="bg-gray-50 font-sans antialiased text-gray-900">\n', '<body class="bg-gray-50 font-sans antialiased text-gray-900">\n\n' + banner + '\n')
    with open("app/templates/dashboard/index.html", "w") as f:
        f.write(html)
