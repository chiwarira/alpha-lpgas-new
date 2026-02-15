"""Views for loyalty card functionality"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from .models import Invoice, CompanySettings
from .models_loyalty import LoyaltyCard
from .utils_loyalty import generate_loyalty_card_image, send_loyalty_card_whatsapp, get_cylinder_size_from_invoice
import base64


def _build_loyalty_message(loyalty_card):
    """Build WhatsApp message for a loyalty card using CompanySettings template."""
    settings = CompanySettings.load()
    stamps = loyalty_card.stamps
    remaining = max(0, 9 - stamps)
    reward_type_raw = loyalty_card.get_reward_type()

    if stamps >= 9:
        # Reward message
        reward_type_display = 'a FREE cylinder' if reward_type_raw == 'free' else '50% OFF'
        template = settings.whatsapp_loyalty_reward_message
        message = template.format(
            client_name=loyalty_card.client.name,
            company_name=settings.company_name,
            cylinder_size=loyalty_card.cylinder_size,
            reward_type=reward_type_display,
        )
    else:
        # Progress message
        reward_text = f"Only {remaining} more purchase(s) to earn your reward!"
        template = settings.whatsapp_loyalty_message
        message = template.format(
            client_name=loyalty_card.client.name,
            company_name=settings.company_name,
            cylinder_size=loyalty_card.cylinder_size,
            stamps=stamps,
            remaining=remaining,
            reward_text=reward_text,
        )
    return message


def _format_phone(phone_number):
    """Format a South African phone number for WhatsApp (27...)."""
    clean = ''.join(filter(str.isdigit, phone_number))
    if clean.startswith('0'):
        clean = '27' + clean[1:]
    elif not clean.startswith('27'):
        clean = '27' + clean
    return clean


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
    
    # Get client phone number
    phone_number = loyalty_card.client.phone
    if not phone_number:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Client does not have a phone number on file.'})
        messages.error(request, 'Client does not have a phone number on file.')
        return redirect('accounting_forms:loyalty_card_detail', pk=pk)
    
    # Format phone number for WhatsApp
    formatted_phone = _format_phone(phone_number)
    
    # Build message from CompanySettings template
    message = _build_loyalty_message(loyalty_card)
    
    stamps = loyalty_card.stamps
    
    # Return JSON response for AJAX calls
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': message,
            'stamps': stamps,
            'phone': formatted_phone,
        })
    
    messages.success(request, f'Loyalty card ready to send! Stamps: {stamps}/9')
    return redirect('accounting_forms:loyalty_card_detail', pk=pk)


@login_required
def download_loyalty_card(request, pk):
    """Download loyalty card image"""
    loyalty_card = get_object_or_404(LoyaltyCard, pk=pk)
    
    # Generate the loyalty card image (returns BytesIO)
    image_buffer = generate_loyalty_card_image(loyalty_card)
    image_data = image_buffer.read()
    
    # Return as downloadable PNG
    response = HttpResponse(image_data, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="loyalty_card_{loyalty_card.client.name}_{loyalty_card.cylinder_size}.png"'
    
    return response
