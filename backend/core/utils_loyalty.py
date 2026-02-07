"""Utility functions for loyalty program"""
from decimal import Decimal
from PIL import Image, ImageDraw, ImageFont
import io
from django.core.files.base import ContentFile
from .models_loyalty import LoyaltyCard, LoyaltyTransaction


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
            elif '19kg' in name_lower or '19 kg' in name_lower:
                return '19kg'
            elif '48kg' in name_lower or '48 kg' in name_lower:
                return '48kg'
    return None


def process_loyalty_stamp(invoice):
    """Process loyalty stamp for an invoice"""
    from .models import Invoice
    
    # Get cylinder size from invoice
    cylinder_size = get_cylinder_size_from_invoice(invoice)
    if not cylinder_size:
        return None
    
    # Get or create loyalty card for this client and cylinder size
    loyalty_card, created = LoyaltyCard.objects.get_or_create(
        client=invoice.client,
        cylinder_size=cylinder_size,
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
    
    # Add stamp
    stamps_before = loyalty_card.stamps
    loyalty_card.add_stamp()
    stamps_after = loyalty_card.stamps
    
    # Create transaction record
    LoyaltyTransaction.objects.create(
        loyalty_card=loyalty_card,
        invoice=invoice,
        transaction_type='stamp',
        stamps_before=stamps_before,
        stamps_after=stamps_after,
        notes=f'Stamp added for invoice {invoice.invoice_number}',
        created_by=invoice.created_by
    )
    
    return loyalty_card


def generate_loyalty_card_image(loyalty_card, logo_path='c:/Users/Chiwarira/CascadeProjects/alpha-lpgas-new/backend/static/alpha-lpgas-logo.png'):
    """Generate loyalty card image with stamped circles"""
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
