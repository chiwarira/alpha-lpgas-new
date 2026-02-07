"""Views for loyalty card functionality"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from .models import Invoice
from .models_loyalty import LoyaltyCard
from .utils_loyalty import generate_loyalty_card_image, send_loyalty_card_whatsapp, get_cylinder_size_from_invoice
import base64


@login_required
def loyalty_card_list(request):
    """List all loyalty cards"""
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Base queryset
    loyalty_cards = LoyaltyCard.objects.filter(is_active=True).select_related('client')
    
    # Apply search filter
    if search_query:
        loyalty_cards = loyalty_cards.filter(
            Q(client__name__icontains=search_query) |
            Q(client__phone__icontains=search_query) |
            Q(cylinder_size__icontains=search_query)
        )
    
    # Order by most recent
    loyalty_cards = loyalty_cards.order_by('-updated_at')
    
    return render(request, 'core/loyalty_card_list.html', {
        'loyalty_cards': loyalty_cards,
        'search_query': search_query,
    })


@login_required
def loyalty_card_detail(request, pk):
    """Display loyalty card detail with send and print options"""
    loyalty_card = get_object_or_404(LoyaltyCard, pk=pk)
    
    # Get recent transactions for this card
    transactions = loyalty_card.transactions.all()[:10]
    
    return render(request, 'core/loyalty_card_detail.html', {
        'loyalty_card': loyalty_card,
        'transactions': transactions,
    })


@login_required
def send_loyalty_card_whatsapp_view(request, pk):
    """Send loyalty card via WhatsApp"""
    loyalty_card = get_object_or_404(LoyaltyCard, pk=pk)
    
    # Generate the loyalty card image
    image_bytes = generate_loyalty_card_image(loyalty_card)
    
    # Get client phone number
    phone_number = loyalty_card.client.phone
    if not phone_number:
        messages.error(request, 'Client does not have a phone number on file.')
        return redirect('accounting_forms:loyalty_card_detail', pk=pk)
    
    # Format phone number
    clean_phone = ''.join(filter(str.isdigit, phone_number))
    
    # Prepare message
    stamps = loyalty_card.stamps
    reward_type = loyalty_card.get_reward_type()
    
    if stamps >= 9:
        if reward_type == 'free':
            message = f"🎉 Congratulations {loyalty_card.client.name}! You've earned a FREE {loyalty_card.cylinder_size} cylinder on your next purchase!"
        else:
            message = f"🎉 Congratulations {loyalty_card.client.name}! You've earned 50% OFF your next {loyalty_card.cylinder_size} cylinder purchase!"
    else:
        remaining = 9 - stamps
        message = f"Thank you for your purchase, {loyalty_card.client.name}! You have {stamps}/9 stamps. Only {remaining} more purchase(s) to earn your reward! 🎁"
    
    # Convert image bytes to base64 for WhatsApp
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    # Construct WhatsApp URL with image and message
    whatsapp_url = f"https://wa.me/{clean_phone}?text={message}"
    
    # Store the image data in session for potential download
    request.session['loyalty_card_image'] = image_base64
    request.session['loyalty_card_phone'] = clean_phone
    request.session['loyalty_card_message'] = message
    
    messages.success(request, f'Loyalty card ready to send! Stamps: {stamps}/9')
    
    # Return JSON response with WhatsApp URL and image data
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'whatsapp_url': whatsapp_url,
            'message': message,
            'stamps': stamps,
            'phone': clean_phone,
            'image_base64': image_base64
        })
    
    # Redirect back to loyalty card detail
    return redirect('accounting_forms:loyalty_card_detail', pk=pk)


@login_required
def download_loyalty_card(request, pk):
    """Download loyalty card image"""
    loyalty_card = get_object_or_404(LoyaltyCard, pk=pk)
    
    # Generate the loyalty card image
    image_bytes = generate_loyalty_card_image(loyalty_card)
    
    # Return as downloadable PNG
    response = HttpResponse(image_bytes, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="loyalty_card_{loyalty_card.client.name}_{loyalty_card.cylinder_size}.png"'
    
    return response
