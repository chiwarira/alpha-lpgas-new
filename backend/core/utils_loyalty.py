"""Utility functions for loyalty program"""
import re
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


SIZE_ORDER = ['5kg', '9kg', '14kg', '19kg', '48kg']
LOYALTY_REWARD_SKU = 'LOYALTY-REWARD'


def _size_from_name(name):
    """Map a product name to a cylinder size (matches whole numbers so '19kg' isn't read as '9kg')."""
    match = re.search(r'(?<!\d)(\d+)\s?kg', name.lower())
    size = f'{match.group(1)}kg' if match else None
    return size if size in SIZE_ORDER else None


def _is_gas_product(product):
    if not product or not product.name:
        return False
    name_lower = product.name.lower()
    return 'gas exchange' in name_lower or 'gas refill' in name_lower


def _qualifying_items(invoice):
    """Paid Gas Exchange / Gas Refill lines with a known cylinder size: [(item, size), ...]"""
    result = []
    for item in invoice.items.select_related('product'):
        if not _is_gas_product(item.product) or item.product.sku == LOYALTY_REWARD_SKU:
            continue
        if item.quantity <= 0 or item.unit_price <= 0:
            continue
        size = _size_from_name(item.product.name)
        if size:
            result.append((item, size))
    return result


def get_cylinder_size_from_invoice(invoice):
    """Extract cylinder size from invoice items"""
    for item in invoice.items.all():
        if item.product and item.product.name:
            size = _size_from_name(item.product.name)
            if size:
                return size
    return None


def reward_description(percent):
    """Human-readable reward, e.g. 'a FREE gas bottle' or '50% OFF one gas bottle'."""
    return 'a FREE gas bottle' if percent >= 100 else f'{percent}% OFF one gas bottle'


def get_loyalty_reward_product():
    """Internal product used for the reward discount line (hidden from dropdowns and the website)."""
    from .models import Product
    product, _ = Product.objects.get_or_create(
        sku=LOYALTY_REWARD_SKU,
        defaults={
            'name': 'Loyalty Reward',
            'description': 'Loyalty programme discount',
            'unit_price': Decimal('0'),
            'tax_rate': Decimal('15'),
            'is_active': False,
            'show_on_website': False,
            'available_for_invoicing': False,
        }
    )
    return product


def process_loyalty_stamp(invoice, reward_percent=None):
    """Add stamps for an invoice and apply the loyalty reward when the 10th bottle is reached.

    Each paid Gas Exchange / Gas Refill bottle earns one stamp. Once a card holds
    STAMPS_REQUIRED stamps, the next bottle is the reward bottle: the cheapest bottle
    on the invoice gets `reward_percent`% off (via a negative 'Loyalty Reward' line),
    the card resets to 0 and any remaining bottles start the new card.
    """
    from .models_loyalty import STAMPS_REQUIRED

    qualifying = _qualifying_items(invoice)
    if not qualifying:
        return None

    if LoyaltyTransaction.objects.filter(invoice=invoice, transaction_type='stamp').exists():
        return LoyaltyCard.objects.filter(client=invoice.client, is_active=True).first()

    sizes = {size for _, size in qualifying}
    smallest_size = min(sizes, key=SIZE_ORDER.index)

    # Get or create loyalty card for the client (one card per client)
    loyalty_card, _ = LoyaltyCard.objects.get_or_create(
        client=invoice.client,
        is_active=True,
        defaults={'stamps': 0, 'cylinder_size': smallest_size}
    )
    if not loyalty_card.cylinder_size or SIZE_ORDER.index(smallest_size) < SIZE_ORDER.index(loyalty_card.cylinder_size):
        loyalty_card.cylinder_size = smallest_size

    total_bottles = sum(int(item.quantity) for item, _ in qualifying)
    stamps_before = loyalty_card.stamps
    count, rewards = stamps_before, 0
    for _ in range(total_bottles):
        if count >= STAMPS_REQUIRED:
            rewards += 1
            count = 0
        else:
            count += 1
    loyalty_card.stamps = count
    loyalty_card.save()

    cylinder_details = {}
    for item, size in qualifying:
        cylinder_details[size] = cylinder_details.get(size, 0) + int(item.quantity)
    details = ', '.join(f'{qty} x {size}' for size, qty in sorted(cylinder_details.items(), key=lambda kv: SIZE_ORDER.index(kv[0])))
    stamped = total_bottles - rewards
    notes = f'{stamped} stamp(s) added for invoice {invoice.invoice_number} ({details}).'
    if rewards:
        notes += f' {rewards} bottle(s) rewarded; card reset.'

    LoyaltyTransaction.objects.create(
        loyalty_card=loyalty_card,
        invoice=invoice,
        transaction_type='stamp',
        stamps_before=stamps_before,
        stamps_after=count,
        notes=notes,
        created_by=invoice.created_by
    )

    loyalty_card.rewards_applied = rewards
    if rewards:
        percent = reward_percent or CompanySettings.load().loyalty_reward_percent
        _apply_rewards(invoice, loyalty_card, qualifying, rewards, percent)
    return loyalty_card


def _apply_rewards(invoice, loyalty_card, qualifying, rewards, percent):
    """Discount the `rewards` cheapest bottles on the invoice."""
    from .models import InvoiceItem
    from .models_loyalty import STAMPS_REQUIRED

    reward_product = get_loyalty_reward_product()
    remaining = rewards
    for item, size in sorted(qualifying, key=lambda pair: pair[0].unit_price):
        if not remaining:
            break
        qty = min(remaining, int(item.quantity))
        remaining -= qty
        discount = (item.unit_price * Decimal(percent) / Decimal('100')).quantize(Decimal('0.01'))
        reward_line = InvoiceItem.objects.create(
            invoice=invoice,
            product=reward_product,
            description=f'Loyalty reward: {percent}% off {item.product.name} (10th purchase)',
            quantity=qty,
            unit_price=-discount,
            tax_rate=item.tax_rate,
        )
        for _ in range(qty):
            LoyaltyTransaction.objects.create(
                loyalty_card=loyalty_card,
                invoice=invoice,
                transaction_type='reward_claimed',
                stamps_before=STAMPS_REQUIRED,
                stamps_after=0,
                reward_percent=percent,
                reward_amount=discount,
                reward_item=reward_line,
                notes=f'{percent}% off 1 x {item.product.name} (R{discount}) on invoice {invoice.invoice_number}',
                created_by=invoice.created_by,
            )
    invoice.calculate_totals()


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
    reward_percent = loyalty_card.reward_percent
    if stamps_filled >= 9:
        reward_text = f"🎉 Congratulations! You've earned {reward_description(reward_percent)} on your next purchase!"
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
    elements.append(Spacer(1, 10*mm))
    
    # Reward terms
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        leading=12,
    )
    disclaimer_text = f"* Every gas exchange earns a stamp. Your 10th gas exchange gets {reward_percent}% off one bottle (the lowest-priced bottle on that order)."
    elements.append(Paragraph(disclaimer_text, disclaimer_style))
    elements.append(Spacer(1, 8*mm))
    
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


def reprocess_loyalty_stamp(invoice, old_client=None):
    """Reprocess loyalty stamp when invoice is edited or reassigned
    
    Args:
        invoice: The invoice being edited
        old_client: The previous client if invoice was reassigned (None if same client)
    """
    # Keep the reward percentage the invoice was originally given, even if the setting changed since
    previous_reward = LoyaltyTransaction.objects.filter(
        invoice=invoice, transaction_type='reward_claimed', reward_percent__isnull=False
    ).first()
    reward_percent = previous_reward.reward_percent if previous_reward else None

    # If invoice was reassigned to a different client, remove stamps from old client
    if old_client and old_client != invoice.client:
        remove_loyalty_stamp(invoice, old_client)

    remove_loyalty_stamp(invoice, log_reversal=False)
    
    # Now process the invoice with updated items
    return process_loyalty_stamp(invoice, reward_percent=reward_percent)


def _recalculate_card_cylinder_size(loyalty_card):
    """Recalculate the smallest cylinder size based on all transactions for this card
    Only considers Gas Exchange and Gas Refill products.
    """
    sizes = set()
    transactions = LoyaltyTransaction.objects.filter(
        loyalty_card=loyalty_card,
        transaction_type='stamp'
    ).exclude(invoice__isnull=True).select_related('invoice')
    for transaction in transactions:
        sizes.update(size for _, size in _qualifying_items(transaction.invoice))
    
    # Update card's cylinder size (set to None if no qualifying products remain)
    loyalty_card.cylinder_size = min(sizes, key=SIZE_ORDER.index) if sizes else None
    loyalty_card.save()


def remove_loyalty_stamp(invoice, client=None, log_reversal=True, recalculate_totals=True):
    """Remove loyalty stamps (and any reward this invoice generated) when an invoice is
    deleted, edited or reassigned.
    
    Args:
        invoice: The invoice being deleted or reassigned
        client: Specific client to remove stamps from (defaults to invoice.client)
        log_reversal: Record a 'reversal' transaction for the audit trail
        recalculate_totals: Recalculate invoice totals after removing reward lines
    """
    if client is None:
        client = invoice.client
    
    transaction = LoyaltyTransaction.objects.filter(
        invoice=invoice,
        transaction_type='stamp',
        loyalty_card__client=client
    ).select_related('loyalty_card').first()
    
    if not transaction:
        return None

    loyalty_card = transaction.loyalty_card
    # stamps_after - stamps_before is negative when the invoice triggered a reward (card reset)
    delta = transaction.stamps_after - transaction.stamps_before
    loyalty_card.stamps = max(0, loyalty_card.stamps - delta)
    loyalty_card.save()

    # Undo rewards generated for this invoice (backfilled historical rewards point at a real gas
    # line rather than a Loyalty Reward line and are left alone)
    rewards = LoyaltyTransaction.objects.filter(
        invoice=invoice,
        transaction_type='reward_claimed',
        loyalty_card=loyalty_card,
        reward_item__product__sku=LOYALTY_REWARD_SKU,
    )
    reward_line_ids = set(rewards.values_list('reward_item_id', flat=True))
    rewards_removed = rewards.count()
    rewards.delete()
    if reward_line_ids:
        for line in invoice.items.filter(pk__in=reward_line_ids):
            line.order_items.all().delete()
            line.delete()
        if recalculate_totals:
            invoice.calculate_totals()

    if log_reversal:
        notes = f'Reversed {transaction.stamps_before}->{transaction.stamps_after} stamps - Invoice {invoice.invoice_number} deleted or reassigned'
        if rewards_removed:
            notes += f' ({rewards_removed} reward(s) cancelled)'
        LoyaltyTransaction.objects.create(
            loyalty_card=loyalty_card,
            invoice=None,  # Don't reference invoice to prevent cascade deletion
            transaction_type='reversal',
            stamps_before=transaction.stamps_after,
            stamps_after=loyalty_card.stamps,
            notes=notes,
            created_by=transaction.created_by
        )

    transaction.delete()
    _recalculate_card_cylinder_size(loyalty_card)
    return loyalty_card


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
    
    if stamps >= 9:
        message = f"🎉 Congratulations! You've earned {reward_description(loyalty_card.reward_percent)} on your next purchase!"
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
