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
    import os
    from django.conf import settings
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    company_name_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#0033CC'),
        fontName='Helvetica-Bold',
        spaceAfter=2
    )
    
    small_text_style = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#333333'),
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#0033CC'),
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    
    # Get company settings
    company = get_company_settings()
    company_name = company.company_name if company else "Alpha LPGas"
    company_reg = company.registration_number if company else "2023/822513/07"
    company_vat = company.vat_number if company else "9415233222"
    company_phone = company.phone if company else "074 454 5665"
    company_email = company.email if company else "info@alphalpgas.co.za"
    
    # Header with logo and invoice details
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'alpha-lpgas-logo.png')
    
    header_data = []
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=40*mm, height=15*mm)
            # Left: Logo and company info, Right: Invoice details
            header_data = [[
                [logo, 
                 Paragraph(company_name, company_name_style),
                 Paragraph(f"Reg No: {company_reg}<br/>VAT No: {company_vat}<br/>Tel: {company_phone}<br/>Email: {company_email}", small_text_style)],
                [Paragraph(f"<b>Invoice No:</b><br/>{invoice.invoice_number}<br/><br/><b>Issue Date:</b><br/>{invoice.issue_date.strftime('%B %d, %Y')}<br/><br/><b>Due Date:</b><br/>{invoice.due_date.strftime('%B %d, %Y')}<br/><br/><b>Status:</b><br/>{invoice.get_status_display().upper()}", small_text_style)]
            ]]
        except:
            pass
    
    if header_data:
        header_table = Table(header_data, colWidths=[110*mm, 70*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(header_table)
    
    elements.append(Spacer(1, 10*mm))
    
    # INVOICE title centered
    invoice_title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Normal'],
        fontSize=20,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=10
    )
    elements.append(Paragraph("INVOICE", invoice_title_style))
    elements.append(Spacer(1, 8*mm))
    
    # Client Information and Banking Details side by side
    client_info = f"""<b>Client Information</b><br/>
    <b>Name:</b> {invoice.client.name}<br/>
    <b>Address:</b> {invoice.client.address}<br/>
    <b>Phone:</b> {invoice.client.phone}<br/>
    <b>Email:</b> {invoice.client.email if invoice.client.email else 'No email provided'}"""
    
    banking_info = f"""<b>Banking Details</b><br/>
    <b>Name:</b> {company_name}<br/>
    <b>Bank:</b> Nedbank<br/>
    <b>Acc No:</b> 1191 646 707<br/>
    <b>Acc Type:</b> Current<br/>
    <b>Branch Code:</b> 125009<br/>
    <font color='#CC0066'><i>Please use your address as reference</i></font>"""
    
    info_data = [[
        Paragraph(client_info, small_text_style),
        Paragraph(banking_info, small_text_style)
    ]]
    
    info_table = Table(info_data, colWidths=[90*mm, 90*mm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10*mm))
    
    # Invoice Items heading
    elements.append(Paragraph("Invoice Items", heading_style))
    
    # Line items table with Code column
    items_data = [['Code', 'Description', 'Quantity', 'Price (incl. VAT)', 'VAT', 'Total']]
    
    for item in invoice.items.all():
        items_data.append([
            item.product.sku if hasattr(item.product, 'sku') else 'P001',
            item.description,
            f"{item.quantity:.2f}",
            f"R{item.unit_price:,.2f}",
            f"R{item.tax_amount:,.2f}",
            f"R{item.total:,.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[20*mm, 70*mm, 25*mm, 30*mm, 20*mm, 25*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals - right aligned
    totals_data = [
        ['', '', '', '', 'Total VAT:', f"R{invoice.tax_amount:,.2f}"],
        ['', '', '', '', 'Total:', f"R{invoice.total_amount:,.2f}"],
    ]
    
    totals_table = Table(totals_data, colWidths=[20*mm, 70*mm, 25*mm, 30*mm, 20*mm, 25*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (4, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (4, 0), (-1, -1), 10),
        ('LINEABOVE', (4, 0), (-1, 0), 1, colors.black),
        ('LINEABOVE', (4, 1), (-1, 1), 2, colors.black),
    ]))
    
    elements.append(totals_table)
    elements.append(Spacer(1, 10*mm))
    
    # Customer Notes section
    elements.append(Paragraph("Customer Notes", heading_style))
    
    # Get payment info from invoice
    payments = invoice.payments.all()
    payment_method = payments.first().get_payment_method_display() if payments.exists() else 'Not specified'
    cylinders_collected = 'Not specified'  # This would come from invoice data if available
    
    notes_data = [
        ['Payment Method:', payment_method],
        ['Cylinders Collected:', cylinders_collected],
        ['Notes:', invoice.notes if invoice.notes else '-']
    ]
    
    notes_table = Table(notes_data, colWidths=[40*mm, 140*mm])
    notes_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(notes_table)
    elements.append(Spacer(1, 15*mm))
    
    # Footer message
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#CC0066'),
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    elements.append(Paragraph("Always striving for customer satisfaction!", footer_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and return it
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


def generate_quote_pdf(quote):
    """Generate PDF for a quote"""
    import os
    from django.conf import settings
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    company_name_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#0033CC'),
        fontName='Helvetica-Bold',
        spaceAfter=2
    )
    
    small_text_style = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#333333'),
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#0033CC'),
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    
    # Get company settings
    company = get_company_settings()
    company_name = company.company_name if company else "Alpha LPGas"
    company_reg = company.registration_number if company else "2023/822513/07"
    company_vat = company.vat_number if company else "9415233222"
    company_phone = company.phone if company else "074 454 5665"
    company_email = company.email if company else "info@alphalpgas.co.za"
    
    # Header with logo and quote details
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'alpha-lpgas-logo.png')
    
    header_data = []
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=40*mm, height=15*mm)
            header_data = [[
                [logo, 
                 Paragraph(company_name, company_name_style),
                 Paragraph(f"Reg No: {company_reg}<br/>VAT No: {company_vat}<br/>Tel: {company_phone}<br/>Email: {company_email}", small_text_style)],
                [Paragraph(f"<b>Quote No:</b><br/>{quote.quote_number}<br/><br/><b>Issue Date:</b><br/>{quote.issue_date.strftime('%B %d, %Y')}<br/><br/><b>Valid Until:</b><br/>{quote.expiry_date.strftime('%B %d, %Y')}<br/><br/><b>Status:</b><br/>{quote.get_status_display().upper()}", small_text_style)]
            ]]
        except:
            pass
    
    if header_data:
        header_table = Table(header_data, colWidths=[110*mm, 70*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(header_table)
    
    elements.append(Spacer(1, 10*mm))
    
    # QUOTATION title centered
    quote_title_style = ParagraphStyle(
        'QuoteTitle',
        parent=styles['Normal'],
        fontSize=20,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=10
    )
    elements.append(Paragraph("QUOTATION", quote_title_style))
    elements.append(Spacer(1, 8*mm))
    
    # Client Information
    client_info = f"""<b>Client Information</b><br/>
    <b>Name:</b> {quote.client.name}<br/>
    <b>Address:</b> {quote.client.address}<br/>
    <b>Phone:</b> {quote.client.phone}<br/>
    <b>Email:</b> {quote.client.email if quote.client.email else 'No email provided'}"""
    
    elements.append(Paragraph(client_info, small_text_style))
    elements.append(Spacer(1, 10*mm))
    
    # Quote Items heading
    elements.append(Paragraph("Quote Items", heading_style))
    
    # Line items table with Code column
    items_data = [['Code', 'Description', 'Quantity', 'Price (incl. VAT)', 'VAT', 'Total']]
    
    for item in quote.items.all():
        items_data.append([
            item.product.sku if hasattr(item.product, 'sku') else 'P001',
            item.description,
            f"{item.quantity:.2f}",
            f"R{item.unit_price:,.2f}",
            f"R{item.tax_amount:,.2f}",
            f"R{item.total:,.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[20*mm, 70*mm, 25*mm, 30*mm, 20*mm, 25*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals - right aligned
    totals_data = [
        ['', '', '', '', 'Total VAT:', f"R{quote.tax_amount:,.2f}"],
        ['', '', '', '', 'Total:', f"R{quote.total_amount:,.2f}"],
    ]
    
    totals_table = Table(totals_data, colWidths=[20*mm, 70*mm, 25*mm, 30*mm, 20*mm, 25*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (4, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (4, 0), (-1, -1), 10),
        ('LINEABOVE', (4, 0), (-1, 0), 1, colors.black),
        ('LINEABOVE', (4, 1), (-1, 1), 2, colors.black),
    ]))
    
    elements.append(totals_table)
    elements.append(Spacer(1, 10*mm))
    
    # Footer message
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#CC0066'),
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    elements.append(Paragraph("Always striving for customer satisfaction!", footer_style))
    
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


def generate_client_statement_pdf(client, start_date, end_date):
    """Generate PDF statement for a client with date range"""
    from .models import Invoice, Payment, CreditNote
    from django.db.models import Q, Sum
    import os
    from django.conf import settings
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    company_name_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#0033CC'),
        fontName='Helvetica-Bold',
        spaceAfter=2
    )
    
    small_text_style = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#333333'),
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#0033CC'),
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    
    # Get company settings
    company = get_company_settings()
    company_name = company.company_name if company else "Alpha LPGas"
    company_reg = company.registration_number if company else "2023/822513/07"
    company_vat = company.vat_number if company else "9415233222"
    company_phone = company.phone if company else "074 454 5665"
    company_email = company.email if company else "info@alphalpgas.co.za"
    company_address = company.address if company else "Sunny Acres Shopping Centre"
    company_city = company.city if company else "Sunnyacres, Western Cape"
    
    # Header with logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'alpha-lpgas-logo.png')
    
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=40*mm, height=15*mm)
            elements.append(logo)
            elements.append(Paragraph(company_name, company_name_style))
        except:
            elements.append(Paragraph(company_name, company_name_style))
    else:
        elements.append(Paragraph(company_name, company_name_style))
    
    # Company details
    company_info = f"Company Reg No: {company_reg}<br/>"
    company_info += f"Company VAT No: {company_vat}<br/>"
    company_info += f"{company_address}<br/>"
    company_info += f"{company_city}<br/>"
    company_info += f"Cell: {company_phone}<br/>"
    company_info += f"Email: {company_email}"
    
    elements.append(Paragraph(company_info, small_text_style))
    elements.append(Spacer(1, 10*mm))
    
    # STATEMENT title - right aligned
    statement_title_style = ParagraphStyle(
        'StatementTitle',
        parent=styles['Normal'],
        fontSize=16,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0033CC'),
        alignment=TA_RIGHT,
        spaceAfter=10
    )
    elements.append(Paragraph('STATEMENT', statement_title_style))
    
    # Statement details - right aligned
    statement_info = f"""<b>Date:</b> {end_date.strftime('%d.%m.%Y')}<br/>
    <b>Statement #:</b> SA-{client.customer_id.replace('CUST-', '')}-{end_date.strftime('%Y%m%d')}<br/>
    <b>Customer ID:</b> {client.customer_id}<br/>
    <b>Start Date:</b> {start_date.strftime('%d.%m.%Y')}<br/>
    <b>End Date:</b> {end_date.strftime('%d.%m.%Y')}<br/>
    <b>Page:</b> 1 of 1"""
    
    statement_info_style = ParagraphStyle(
        'StatementInfo',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_RIGHT,
    )
    elements.append(Paragraph(statement_info, statement_info_style))
    elements.append(Spacer(1, 8*mm))
    
    # Client information - "To:" section
    elements.append(Paragraph("To:", heading_style))
    client_info = f"""<b>{client.name}</b><br/>
    {client.address}<br/>
    Phone: {client.phone}<br/>
    Email: {client.email if client.email else 'N/A'}"""
    
    elements.append(Paragraph(client_info, small_text_style))
    elements.append(Spacer(1, 10*mm))
    
    # Account Summary section (right side box)
    elements.append(Paragraph("Account Summary", heading_style))
    
    # Calculate balance brought forward (all unpaid invoices before start_date)
    balance_bf_invoices = Invoice.objects.filter(
        client=client,
        issue_date__lt=start_date
    )
    
    balance_bf = Decimal('0.00')
    for inv in balance_bf_invoices:
        balance_bf += inv.balance
    
    # Calculate totals first for summary
    invoices = Invoice.objects.filter(
        client=client,
        issue_date__gte=start_date,
        issue_date__lte=end_date
    )
    
    payments = Payment.objects.filter(
        invoice__client=client,
        payment_date__gte=start_date,
        payment_date__lte=end_date
    )
    
    credit_notes = CreditNote.objects.filter(
        client=client,
        issue_date__gte=start_date,
        issue_date__lte=end_date
    )
    
    total_credits = sum(inv.total_amount for inv in invoices)
    total_debits = sum(pmt.amount for pmt in payments) + sum(cn.total_amount for cn in credit_notes)
    current_balance = balance_bf + total_credits - total_debits
    
    # Summary box
    summary_data = [
        ['Previous Balance:', f"R{balance_bf:,.2f}"],
        ['Credits:', f"R{total_credits:,.2f}"],
        ['Debits:', f"R{total_debits:,.2f}"],
        ['', ''],
        ['Total Balance Due:', f"R{current_balance:,.2f}"],
        ['Payment Due Date:', '27-04-2025'],
        ['', ''],
        ['Balance:', 'Status']
    ]
    
    summary_table = Table(summary_data, colWidths=[40*mm, 40*mm])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LINEABOVE', (0, 4), (-1, 4), 1, colors.black),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 4), (-1, 4), 11),
        ('TEXTCOLOR', (0, 4), (-1, 4), colors.HexColor('#0033CC')),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 10*mm))
    
    # Transactions table
    transactions_data = [['Date', 'Invoice #', 'Description', 'Debit', 'Credit', 'Balance']]
    
    # Add balance brought forward
    running_balance = balance_bf
    if balance_bf != 0:
        transactions_data.append([
            start_date.strftime('%Y-%m-%d'),
            '',
            'Balance b/f (unpaid invoices from previous period(s))',
            '',
            '',
            f"R{running_balance:,.2f}"
        ])
    
    # Get all transactions in the period
    # Invoices
    invoices = Invoice.objects.filter(
        client=client,
        issue_date__gte=start_date,
        issue_date__lte=end_date
    ).order_by('issue_date')
    
    # Payments
    payments = Payment.objects.filter(
        invoice__client=client,
        payment_date__gte=start_date,
        payment_date__lte=end_date
    ).order_by('payment_date')
    
    # Credit Notes
    credit_notes = CreditNote.objects.filter(
        client=client,
        issue_date__gte=start_date,
        issue_date__lte=end_date
    ).order_by('issue_date')
    
    # Combine and sort all transactions
    transactions = []
    
    for inv in invoices:
        transactions.append({
            'date': inv.issue_date,
            'type': 'invoice',
            'description': f'Invoice',
            'reference': inv.invoice_number,
            'debit': inv.total_amount,
            'credit': Decimal('0.00')
        })
    
    for pmt in payments:
        transactions.append({
            'date': pmt.payment_date,
            'type': 'payment',
            'description': f'Payment - {pmt.get_payment_method_display()}',
            'reference': pmt.payment_number,
            'debit': Decimal('0.00'),
            'credit': pmt.amount
        })
    
    for cn in credit_notes:
        transactions.append({
            'date': cn.issue_date,
            'type': 'credit_note',
            'description': 'Credit Note',
            'reference': cn.credit_note_number,
            'debit': Decimal('0.00'),
            'credit': cn.total_amount
        })
    
    # Sort by date
    transactions.sort(key=lambda x: x['date'])
    
    # Add transactions to table
    for trans in transactions:
        running_balance += trans['debit'] - trans['credit']
        
        debit_str = f"R{trans['debit']:,.2f}" if trans['debit'] > 0 else ''
        credit_str = f"R{trans['credit']:,.2f}" if trans['credit'] > 0 else ''
        
        # Add status badge for payments
        description = trans['description']
        if trans['type'] == 'invoice':
            description = f"Invoice {trans['reference']}"
        elif trans['type'] == 'payment':
            description = f"Receipt {trans['reference']}"
        
        transactions_data.append([
            trans['date'].strftime('%Y-%m-%d'),
            trans['reference'],
            description,
            debit_str,
            credit_str,
            f"R{running_balance:,.2f}"
        ])
    
    # Create transactions table
    trans_table = Table(transactions_data, colWidths=[25*mm, 30*mm, 60*mm, 20*mm, 20*mm, 25*mm])
    trans_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
    ]))
    
    elements.append(trans_table)
    elements.append(Spacer(1, 15*mm))
    
    # Footer messages
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#0033CC'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph("Make all EFT's payable to Alpha LPGas", footer_style))
    elements.append(Spacer(1, 3*mm))
    
    thank_you_style = ParagraphStyle(
        'ThankYou',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    elements.append(Paragraph("Thank you for your business!", thank_you_style))
    elements.append(Spacer(1, 5*mm))
    
    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )
    contact_text = f"Should you have any enquiries concerning this statement, please contact Grace on 074-454-9665<br/>"
    contact_text += f"Sunny Acres Shopping Centre, Lekkerwater, Sunnyacres, Western Cape<br/>"
    contact_text += f"Tel: 074-454-9665 | Email: info@alphalpgas.co.za | Web: www.alphalpgas.co.za"
    elements.append(Paragraph(contact_text, contact_style
        ))
    
    # Build PDF
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf
