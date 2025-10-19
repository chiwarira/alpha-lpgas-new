from django.http import HttpResponse
from django.template.loader import get_template
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from decimal import Decimal
from .models import CompanySettings


def get_company_settings():
    """Get company settings or return defaults"""
    try:
        return CompanySettings.objects.first()
    except:
        return None


def generate_invoice_pdf(invoice):
    """Generate PDF for an invoice"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
    )
    
    normal_style = styles['Normal']
    
    # Get company settings
    company = get_company_settings()
    
    # Header with company info
    if company and company.logo:
        try:
            logo = Image(company.logo.path, width=50*mm, height=20*mm)
            elements.append(logo)
            elements.append(Spacer(1, 5*mm))
        except:
            pass
    
    # Company details
    company_name = company.company_name if company else "Alpha LPGas"
    company_address = company.address if company else "Sunnyacres Shopping Centre, Fish Hoek"
    company_phone = company.phone if company else "074 454 5665"
    company_email = company.email if company else "info@alphalpgas.co.za"
    company_vat = company.vat_number if company else "9415233222"
    
    elements.append(Paragraph(company_name, title_style))
    elements.append(Paragraph(f"{company_address}", normal_style))
    elements.append(Paragraph(f"Tel: {company_phone} | Email: {company_email}", normal_style))
    elements.append(Paragraph(f"VAT No: {company_vat}", normal_style))
    elements.append(Spacer(1, 10*mm))
    
    # Invoice title and details
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Spacer(1, 5*mm))
    
    # Invoice and client details in two columns
    invoice_data = [
        ['Invoice Number:', invoice.invoice_number, 'Invoice Date:', invoice.invoice_date.strftime('%d %B %Y')],
        ['Client:', invoice.client.name, 'Due Date:', invoice.due_date.strftime('%d %B %Y')],
        ['', invoice.client.address, 'Status:', invoice.get_status_display()],
        ['', f"{invoice.client.city}, {invoice.client.postal_code}", '', ''],
        ['', f"Tel: {invoice.client.phone}", '', ''],
        ['', f"Email: {invoice.client.email}", '', ''],
    ]
    
    if invoice.client.vat_number:
        invoice_data.append(['', f"VAT No: {invoice.client.vat_number}", '', ''])
    
    invoice_table = Table(invoice_data, colWidths=[30*mm, 70*mm, 30*mm, 50*mm])
    invoice_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(invoice_table)
    elements.append(Spacer(1, 10*mm))
    
    # Line items table
    items_data = [['Description', 'Qty', 'Unit Price', 'VAT', 'Total']]
    
    for item in invoice.items.all():
        items_data.append([
            item.description,
            str(item.quantity),
            f"R {item.unit_price:,.2f}",
            f"{item.vat_rate}%",
            f"R {item.total:,.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[90*mm, 20*mm, 25*mm, 20*mm, 25*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals
    totals_data = [
        ['Subtotal (excl. VAT):', f"R {invoice.subtotal_excl_vat:,.2f}"],
        ['VAT:', f"R {invoice.vat_amount:,.2f}"],
    ]
    
    if invoice.discount_amount > 0:
        totals_data.insert(0, ['Discount:', f"R {invoice.discount_amount:,.2f}"])
    
    totals_data.append(['Total:', f"R {invoice.total_amount:,.2f}"])
    totals_data.append(['Paid:', f"R {invoice.paid_amount:,.2f}"])
    totals_data.append(['Balance Due:', f"R {invoice.balance_due:,.2f}"])
    
    totals_table = Table(totals_data, colWidths=[130*mm, 50*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -3), (-1, -3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -3), (-1, -3), 12),
        ('LINEABOVE', (0, -3), (-1, -3), 2, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
    ]))
    
    elements.append(totals_table)
    elements.append(Spacer(1, 10*mm))
    
    # Terms and notes
    if invoice.terms:
        elements.append(Paragraph("Terms & Conditions:", heading_style))
        elements.append(Paragraph(invoice.terms, normal_style))
        elements.append(Spacer(1, 5*mm))
    
    if invoice.notes:
        elements.append(Paragraph("Notes:", heading_style))
        elements.append(Paragraph(invoice.notes, normal_style))
        elements.append(Spacer(1, 5*mm))
    
    # Banking details
    if company and company.bank_name:
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph("Banking Details:", heading_style))
        elements.append(Paragraph(f"Bank: {company.bank_name}", normal_style))
        elements.append(Paragraph(f"Account Holder: {company.account_holder}", normal_style))
        elements.append(Paragraph(f"Account Number: {company.account_number}", normal_style))
        elements.append(Paragraph(f"Branch Code: {company.branch_code}", normal_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and return it
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


def generate_quote_pdf(quote):
    """Generate PDF for a quote"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
    )
    
    normal_style = styles['Normal']
    company = get_company_settings()
    
    # Header
    if company and company.logo:
        try:
            logo = Image(company.logo.path, width=50*mm, height=20*mm)
            elements.append(logo)
            elements.append(Spacer(1, 5*mm))
        except:
            pass
    
    company_name = company.company_name if company else "Alpha LPGas"
    company_address = company.address if company else "Sunnyacres Shopping Centre, Fish Hoek"
    company_phone = company.phone if company else "074 454 5665"
    company_email = company.email if company else "info@alphalpgas.co.za"
    
    elements.append(Paragraph(company_name, title_style))
    elements.append(Paragraph(f"{company_address}", normal_style))
    elements.append(Paragraph(f"Tel: {company_phone} | Email: {company_email}", normal_style))
    elements.append(Spacer(1, 10*mm))
    
    # Quote title
    elements.append(Paragraph("QUOTATION", title_style))
    elements.append(Spacer(1, 5*mm))
    
    # Quote details
    quote_data = [
        ['Quote Number:', quote.quote_number, 'Quote Date:', quote.quote_date.strftime('%d %B %Y')],
        ['Client:', quote.client.name, 'Valid Until:', quote.valid_until.strftime('%d %B %Y')],
        ['', quote.client.address, 'Status:', quote.get_status_display()],
        ['', f"{quote.client.city}, {quote.client.postal_code}", '', ''],
        ['', f"Tel: {quote.client.phone}", '', ''],
    ]
    
    quote_table = Table(quote_data, colWidths=[30*mm, 70*mm, 30*mm, 50*mm])
    quote_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(quote_table)
    elements.append(Spacer(1, 10*mm))
    
    # Line items
    items_data = [['Description', 'Qty', 'Unit Price', 'VAT', 'Total']]
    
    for item in quote.items.all():
        items_data.append([
            item.description,
            str(item.quantity),
            f"R {item.unit_price:,.2f}",
            f"{item.vat_rate}%",
            f"R {item.total:,.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[90*mm, 20*mm, 25*mm, 20*mm, 25*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals
    totals_data = [
        ['Subtotal (excl. VAT):', f"R {quote.subtotal_excl_vat:,.2f}"],
        ['VAT:', f"R {quote.vat_amount:,.2f}"],
    ]
    
    if quote.discount_amount > 0:
        totals_data.insert(0, ['Discount:', f"R {quote.discount_amount:,.2f}"])
    
    totals_data.append(['Total:', f"R {quote.total_amount:,.2f}"])
    
    totals_table = Table(totals_data, colWidths=[130*mm, 50*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
    ]))
    
    elements.append(totals_table)
    elements.append(Spacer(1, 10*mm))
    
    # Terms and notes
    if quote.terms:
        elements.append(Paragraph("Terms & Conditions:", heading_style))
        elements.append(Paragraph(quote.terms, normal_style))
        elements.append(Spacer(1, 5*mm))
    
    if quote.notes:
        elements.append(Paragraph("Notes:", heading_style))
        elements.append(Paragraph(quote.notes, normal_style))
    
    # Build PDF
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


def download_invoice_pdf(request, pk):
    """View to download invoice as PDF"""
    from django.shortcuts import get_object_or_404
    from .models import Invoice
    
    invoice = get_object_or_404(Invoice, pk=pk)
    pdf = generate_invoice_pdf(invoice)
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
    
    return response


def download_quote_pdf(request, pk):
    """View to download quote as PDF"""
    from django.shortcuts import get_object_or_404
    from .models import Quote
    
    quote = get_object_or_404(Quote, pk=pk)
    pdf = generate_quote_pdf(quote)
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="quote_{quote.quote_number}.pdf"'
    
    return response
