"""Utility functions for loyalty program"""
from decimal import Decimal
from PIL import Image, ImageDraw, ImageFont
import io
import os
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.graphics.shapes import Drawing, Circle
from reportlab.graphics import renderPDF
from .models_loyalty import LoyaltyCard, LoyaltyTransaction
from .models import CompanySettings


def get_cylinder_size_from_invoice(invoice):
    """Extract cylinder size from invoice items"""
    # Check invoice items for cylinder products
    for item in invoice.items.all():
        if item.product and item.product.name:
            name_lower = item.product.name.lower()
            if '5kg' in name_lower or '5 kg' in name_lower:
                return '5kg'
            elif '9kg' in name_lower or '9 kg' in name_lower:
                return '9kg'
            elif '14kg' in name_lower or '14 kg' in name_lower:
                return '14kg'
            elif '19kg' in name_lower or '19 kg' in name_lower:
                return '19kg'
            elif '48kg' in name_lower or '48 kg' in name_lower:
                return '48kg'
    return None


def process_loyalty_stamp(invoice):
    """Process loyalty stamp for an invoice - stamps all cylinder sizes and uses smallest size for reward"""
    from .models import Invoice
    
    # Count cylinders by size
    cylinder_counts = {
        '5kg': 0,
        '9kg': 0,
        '14kg': 0,
        '19kg': 0,
        '48kg': 0
    }
    
    # Count all cylinder sizes in this invoice
    for item in invoice.items.all():
        if item.product and item.product.name:
            name_lower = item.product.name.lower()
            if '5kg' in name_lower or '5 kg' in name_lower:
                cylinder_counts['5kg'] += int(item.quantity)
            elif '9kg' in name_lower or '9 kg' in name_lower:
                cylinder_counts['9kg'] += int(item.quantity)
            elif '14kg' in name_lower or '14 kg' in name_lower:
                cylinder_counts['14kg'] += int(item.quantity)
            elif '19kg' in name_lower or '19 kg' in name_lower:
                cylinder_counts['19kg'] += int(item.quantity)
            elif '48kg' in name_lower or '48 kg' in name_lower:
                cylinder_counts['48kg'] += int(item.quantity)
    
    # Find the smallest cylinder size purchased in this invoice
    # Order: 5kg < 9kg < 14kg < 19kg < 48kg
    smallest_size = None
    total_cylinders = 0
    size_order = ['5kg', '9kg', '14kg', '19kg', '48kg']
    
    for size in size_order:
        if cylinder_counts[size] > 0:
            if smallest_size is None:
                smallest_size = size
            total_cylinders += cylinder_counts[size]
    
    # If no cylinders found, return None
    if smallest_size is None or total_cylinders == 0:
        return None
    
    # Get or create loyalty card for the smallest cylinder size
    loyalty_card, created = LoyaltyCard.objects.get_or_create(
        client=invoice.client,
        cylinder_size=smallest_size,
        is_active=True,
        defaults={'stamps': 0}
    )
    
    # Check if this invoice already has a loyalty transaction
    existing_transaction = LoyaltyTransaction.objects.filter(
        invoice=invoice,
        transaction_type='stamp'
    ).first()
    
    if existing_transaction:
        return loyalty_card  # Already processed
    
    # Add stamps for all cylinders (regardless of size)
    stamps_before = loyalty_card.stamps
    for _ in range(total_cylinders):
        loyalty_card.add_stamp()
    stamps_after = loyalty_card.stamps
    
    # Build notes describing what was purchased
    cylinder_details = []
    for size in size_order:
        if cylinder_counts[size] > 0:
            cylinder_details.append(f"{cylinder_counts[size]} x {size}")
    
    notes = f'{total_cylinders} stamp(s) added for invoice {invoice.invoice_number} ({", ".join(cylinder_details)}). Reward will be for {smallest_size} cylinder.'
    
    # Create transaction record
    LoyaltyTransaction.objects.create(
        loyalty_card=loyalty_card,
        invoice=invoice,
        transaction_type='stamp',
        stamps_before=stamps_before,
        stamps_after=stamps_after,
        notes=notes,
        created_by=invoice.created_by
    )
    
    return loyalty_card


def generate_loyalty_card_pdf(loyalty_card):
    """Generate loyalty card as PDF with invoice-style header and footer"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Get company settings
    company = CompanySettings.objects.first()
    company_name = company.company_name if company else "Alpha LPGas"
    company_reg = company.registration_number if company else "2023/822513/07"
    company_vat = company.vat_number if company else "9415233222"
    company_phone = company.phone if company else "074 454 5665"
    company_email = company.email if company else "info@alphalpgas.co.za"
    
    # Header with logo and company details (same as invoice)
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'alpha-lpgas-logo.png')
    
    header_data = []
    if os.path.exists(logo_path):
        try:
            logo = RLImage(logo_path, width=90*mm, height=17.5*mm)
            company_details_style = ParagraphStyle(
                'CompanyDetails',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#333333'),
                leading=14,
            )
            small_text_style = ParagraphStyle(
                'SmallText',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#333333'),
            )
            # Left: Logo and company info, Right: Loyalty card info
            header_data = [[
                [logo, 
                 Paragraph(f"{company_name}<br/>Reg No: {company_reg}<br/>VAT No: {company_vat}<br/>Tel: {company_phone}<br/>Email: {company_email}", company_details_style)],
                [Paragraph(f"<b>Loyalty Card</b><br/>{loyalty_card.cylinder_size}<br/><br/><b>Client:</b><br/>{loyalty_card.client.name}<br/><br/><b>Stamps:</b><br/>{loyalty_card.stamps}/9", small_text_style)]
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
    
    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=24,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=10,
        textColor=colors.HexColor('#0033CC'),
    )
    elements.append(Paragraph("LOYALTY CARD", title_style))
    elements.append(Spacer(1, 5*mm))
    
    # Subtitle
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=10,
        textColor=colors.HexColor('#666666'),
    )
    elements.append(Paragraph(f"Collect 9 stamps and get your reward!", subtitle_style))
    elements.append(Spacer(1, 10*mm))
    
    # Create stamp grid (3x3)
    stamp_data = []
    stamps_filled = loyalty_card.stamps
    
    for row in range(3):
        row_data = []
        for col in range(3):
            stamp_num = row * 3 + col + 1
            if stamp_num <= stamps_filled:
                # Filled stamp - show checkmark
                row_data.append(Paragraph(f"<para align='center'><font size='40' color='#0033CC'>✓</font><br/><font size='10'>Stamp {stamp_num}</font></para>", styles['Normal']))
            else:
                # Empty stamp - show number
                row_data.append(Paragraph(f"<para align='center'><font size='40' color='#CCCCCC'>○</font><br/><font size='10'>Stamp {stamp_num}</font></para>", styles['Normal']))
        stamp_data.append(row_data)
    
    stamp_table = Table(stamp_data, colWidths=[60*mm, 60*mm, 60*mm], rowHeights=[40*mm, 40*mm, 40*mm])
    stamp_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9F9F9')),
    ]))
    
    elements.append(stamp_table)
    elements.append(Spacer(1, 10*mm))
    
    # Reward info
    reward_type = loyalty_card.get_reward_type()
    if stamps_filled >= 9:
        if reward_type == 'free':
            reward_text = f"🎉 Congratulations! You've earned a FREE {loyalty_card.cylinder_size} cylinder!"
        else:
            reward_text = f"🎉 Congratulations! You've earned 50% OFF your next {loyalty_card.cylinder_size} cylinder!"
        reward_color = '#00CC00'
    else:
        remaining = 9 - stamps_filled
        reward_text = f"Collect {remaining} more stamp(s) to earn your reward!"
        reward_color = '#0033CC'
    
    reward_style = ParagraphStyle(
        'Reward',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        textColor=colors.HexColor(reward_color),
    )
    elements.append(Paragraph(reward_text, reward_style))
    elements.append(Spacer(1, 15*mm))
    
    # Footer message (same as invoice)
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
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


def generate_loyalty_card_image(loyalty_card, logo_path='c:/Users/Chiwarira/CascadeProjects/alpha-lpgas-new/backend/static/alpha-lpgas-logo.png'):
    """Generate loyalty card image with stamped circles (DEPRECATED - use generate_loyalty_card_pdf instead)"""
    # Load the base loyalty card template
    base_image_path = 'c:/Users/Chiwarira/CascadeProjects/alpha-lpgas-new/Back.png'
    
    try:
        img = Image.open(base_image_path).convert('RGBA')
    except FileNotFoundError:
        # Create a simple loyalty card if template not found
        img = Image.new('RGBA', (726, 1024), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((100, 50), "ALPHA LPGas Loyalty Card", fill=(0, 0, 0, 255))
    
    # Load logo for stamping
    try:
        logo = Image.open(logo_path).convert('RGBA')
        # Resize logo to fit in circle (approximately 80x80 pixels)
        logo = logo.resize((80, 80), Image.Resampling.LANCZOS)
    except FileNotFoundError:
        # Create a simple stamp if logo not found
        logo = Image.new('RGBA', (80, 80), (255, 0, 0, 128))
        draw = ImageDraw.Draw(logo)
        draw.ellipse([0, 0, 80, 80], fill=(255, 0, 0, 128))
    
    # Circle positions (approximate based on the template image)
    # Positions are (x, y) for center of each circle
    circle_positions = [
        (420, 345),  # Circle 1
        (610, 345),  # Circle 2
        (420, 465),  # Circle 3
        (610, 465),  # Circle 4
        (420, 585),  # Circle 5
        (610, 585),  # Circle 6
        (420, 705),  # Circle 7
        (610, 705),  # Circle 8
        (420, 825),  # Circle 9
    ]
    
    # Stamp the circles based on number of stamps
    for i in range(min(loyalty_card.stamps, 9)):
        x, y = circle_positions[i]
        # Center the logo on the circle
        paste_x = x - logo.width // 2
        paste_y = y - logo.height // 2
        img.paste(logo, (paste_x, paste_y), logo)
    
    # Add client name and cylinder size text
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw client name (approximate position)
    draw.text((175, 320), loyalty_card.client.name[:25], fill=(0, 0, 0, 255), font=font)
    
    # Draw cylinder size (approximate position)
    draw.text((175, 510), loyalty_card.cylinder_size, fill=(0, 0, 0, 255), font=font)
    
    # Draw date of issue (approximate position)
    from datetime import date
    draw.text((175, 710), date.today().strftime('%Y-%m-%d'), fill=(0, 0, 0, 255), font=font_small)
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr


def send_loyalty_card_whatsapp(loyalty_card, phone_number=None):
    """Send loyalty card image via WhatsApp"""
    # Generate the loyalty card image
    image_bytes = generate_loyalty_card_image(loyalty_card)
    
    # Get client phone number
    if not phone_number:
        phone_number = loyalty_card.client.phone
    
    if not phone_number:
        return False
    
    # Format phone number (remove spaces, dashes, etc.)
    clean_phone = ''.join(filter(str.isdigit, phone_number))
    
    # Prepare message
    stamps = loyalty_card.stamps
    reward_type = loyalty_card.get_reward_type()
    
    if stamps >= 9:
        if reward_type == 'free':
            message = f"🎉 Congratulations! You've earned a FREE {loyalty_card.cylinder_size} cylinder on your next purchase!"
        else:
            message = f"🎉 Congratulations! You've earned 50% OFF your next {loyalty_card.cylinder_size} cylinder purchase!"
    else:
        remaining = 9 - stamps
        message = f"Thank you for your purchase! You have {stamps}/9 stamps. Only {remaining} more purchase(s) to earn your reward! 🎁"
    
    # TODO: Integrate with WhatsApp API (Twilio, WhatsApp Business API, etc.)
    # For now, we'll just return the message and image path
    # You'll need to implement actual WhatsApp sending based on your setup
    
    return {
        'success': True,
        'phone': clean_phone,
        'message': message,
        'image': image_bytes,
        'stamps': stamps
    }
