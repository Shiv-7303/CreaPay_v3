with open("app/templates/dashboard/index.html", "r") as f:
    content = f.read()

import re

# Update button to pass phone and invoice info
if "sendReminder('{{ deal.id }}'" in content:
    content = content.replace("sendReminder('{{ deal.id }}')", "sendReminder('{{ deal.id }}', '{{ deal.brand.phone or '' }}', '{{ deal.invoice.invoice_number if deal.invoice else '' }}', '{{ deal.amount }}', '{{ deal.due_date.strftime('%b %d, %Y') }}', '{{ deal.invoice.pdf_url if deal.invoice else '' }}')")

# Update JS function
old_js = """        async function sendReminder(dealId) {
            const res = await fetch(`/deals/${dealId}/remind`, { method: 'POST' });
            if (res.ok) {
                alert("Reminder sent successfully!");
            } else {
                alert("Failed to send reminder.");
            }
        }"""

new_js = """        async function sendReminder(dealId, phone, invoiceNumber, amount, dueDate, pdfUrl) {
            // Send email via backend task
            const res = await fetch(`/deals/${dealId}/remind`, { method: 'POST' });
            
            if (res.ok) {
                // Trigger WhatsApp if phone exists
                if (phone) {
                    const message = `Hi, friendly reminder: invoice ${invoiceNumber} for ₹${amount} is due ${dueDate}. PDF: ${pdfUrl}`;
                    const waUrl = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
                    window.open(waUrl, '_blank');
                } else {
                    alert("Email reminder sent. (WhatsApp skipped: No phone number saved for brand)");
                }
            } else {
                alert("Failed to send reminder.");
            }
        }"""

content = content.replace(old_js, new_js)

with open("app/templates/dashboard/index.html", "w") as f:
    f.write(content)
