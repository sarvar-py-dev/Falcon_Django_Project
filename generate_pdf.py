import os

import django
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'root.settings')
django.setup()

from apps.models.order import Order
from apps.models import SiteSettings


def make_pdf(order: Order):
    data = order.order_items.values_list('product__name', 'quantity', 'product__price')

    # Create a canvas object
    pdf_file = "output.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter

    # Insert bold text in the middle of the top
    title = f"Order Detail #{order.pk}"
    c.setFont("Helvetica-Bold", 18)
    title_width = c.stringWidth(title, 'Helvetica-Bold', 12)
    c.drawString((width - title_width) / 2, height - 40, title)

    c.setFont("Helvetica", 14)
    # Define the starting position of the table
    x_offset = 50
    y_offset = height - 80
    line_height = 25

    # Draw table headers
    headers = ['ID', 'Product name', 'Quantity', 'Price']
    for i, header in enumerate(headers):
        if i == 1:
            c.drawString(x_offset + i * 30, y_offset, header)
        else:
            c.drawString(x_offset + i * 115, y_offset, header)
    total_price = 0
    # Draw table rows
    for index, row in enumerate(data, 1):
        y_offset -= line_height
        total_price += row[-1] * row[-2]
        for i, item in enumerate([index] + list(row)):
            text = str(item)
            if i == 1:
                c.drawString(x_offset + i * 30, y_offset, text)
            else:
                if i == len(row):
                    text += ' $'
                c.drawString(x_offset + i * 115, y_offset, text)

    site = SiteSettings.objects.first()
    if site:
        y_offset -= line_height
        text = f'Tax {site.tax}%: SUMMA'
        c.drawString(x_offset, y_offset, text)

    text = f'Total price: {total_price}$'
    y_offset -= line_height
    c.drawString(x_offset, y_offset, text)

    # Save the PDF
    c.save()

    print(f"PDF created successfully: {pdf_file}")


order_id = 50
order = Order.objects.get(id=order_id)
make_pdf(order)
