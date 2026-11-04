"""Views for loyalty card functionality"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Max
from django.views.decorators.http import require_POST
from .models import Invoice, CompanySettings
from .models_loyalty import LoyaltyCard, LoyaltyTransaction, REWARD_PERCENT_CHOICES
from .utils_loyalty import generate_loyalty_card_image, generate_loyalty_card_pdf, send_loyalty_card_whatsapp, get_cylinder_size_from_invoice, reward_description
import base64

REWARD_FILTERS = {
    'full': Q(full_rewards__gt=0),
    'half': Q(half_rewards__gt=0),
    'any': Q(full_rewards__gt=0) | Q(half_rewards__gt=0),
    'eligible': Q(stamps__gte=9),
}


def _reward_count(percent):
    return Count('transactions', filter=Q(transactions__transaction_type='reward_claimed', transactions__reward_percent=percent))


def _build_loyalty_message(loyalty_card):
    """Build WhatsApp message for a loyalty card using CompanySettings template."""
    settings = CompanySettings.load()
    stamps = loyalty_card.stamps
    remaining = max(0, 9 - stamps)

    if stamps >= 9:
        # Reward message
        reward_type_display = reward_description(settings.loyalty_reward_percent)
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
    
    reward_filter = request.GET.get('rewards', '')
    
    # Base queryset
    loyalty_cards = LoyaltyCard.objects.filter(is_active=True).select_related('client').annotate(
        full_rewards=_reward_count(100),
        half_rewards=_reward_count(50),
        last_reward_at=Max('transactions__created_at', filter=Q(transactions__transaction_type='reward_claimed')),
    )
    
    # Apply search filter
    if search_query:
        loyalty_cards = loyalty_cards.filter(
            Q(client__name__icontains=search_query) |
            Q(client__phone__icontains=search_query) |
            Q(cylinder_size__icontains=search_query)
        )
    if reward_filter in REWARD_FILTERS:
        loyalty_cards = loyalty_cards.filter(REWARD_FILTERS[reward_filter])
    
    # Order by most recent
    loyalty_cards = loyalty_cards.order_by('-updated_at')

    rewards = LoyaltyTransaction.objects.filter(transaction_type='reward_claimed')
    
    return render(request, 'core/loyalty_card_list.html', {
        'loyalty_cards': loyalty_cards,
        'search_query': search_query,
        'reward_filter': reward_filter,
        'reward_percent': CompanySettings.load().loyalty_reward_percent,
        'reward_percent_choices': REWARD_PERCENT_CHOICES,
        'total_full_rewards': rewards.filter(reward_percent=100).count(),
        'total_half_rewards': rewards.filter(reward_percent=50).count(),
    })


@login_required
@require_POST
def loyalty_settings_update(request):
    """Switch the loyalty reward between 50% and 100% off one bottle."""
    if not request.user.is_staff:
        messages.error(request, 'Only staff administrators can change the loyalty reward.')
        return redirect('accounting_forms:loyalty_card_list')
    try:
        percent = int(request.POST.get('loyalty_reward_percent', ''))
    except ValueError:
        percent = None
    if percent not in dict(REWARD_PERCENT_CHOICES):
        messages.error(request, 'Invalid reward percentage.')
        return redirect('accounting_forms:loyalty_card_list')
    settings = CompanySettings.load()
    settings.loyalty_reward_percent = percent
    settings.save()
    messages.success(request, f'Loyalty reward set to {percent}% off one bottle on the 10th purchase. Applies to new invoices.')
    return redirect('accounting_forms:loyalty_card_list')


@login_required
def loyalty_reward_history(request):
    """Every loyalty reward given, newest first, filterable by 100% / 50%."""
    percent = request.GET.get('percent', '')
    search_query = request.GET.get('search', '')
    rewards = LoyaltyTransaction.objects.filter(transaction_type='reward_claimed').select_related(
        'loyalty_card__client', 'invoice', 'created_by'
    ).order_by('-invoice__issue_date', '-created_at')
    if percent in ('50', '100'):
        rewards = rewards.filter(reward_percent=int(percent))
    if search_query:
        rewards = rewards.filter(
            Q(loyalty_card__client__name__icontains=search_query) |
            Q(loyalty_card__client__phone__icontains=search_query) |
            Q(invoice__invoice_number__icontains=search_query)
        )
    return render(request, 'core/loyalty_reward_history.html', {
        'rewards': rewards[:500],
        'percent': percent,
        'search_query': search_query,
    })


@login_required
def loyalty_card_detail(request, pk):
    """Display loyalty card detail with send and print options"""
    loyalty_card = get_object_or_404(LoyaltyCard, pk=pk)
    
    # Get recent transactions for this card
    transactions = loyalty_card.transactions.exclude(transaction_type='reversal').select_related('invoice')[:10]
    rewards = loyalty_card.reward_transactions().select_related('invoice').order_by('-invoice__issue_date', '-created_at')
    
    return render(request, 'core/loyalty_card_detail.html', {
        'loyalty_card': loyalty_card,
        'transactions': transactions,
        'rewards': rewards,
        'full_rewards': sum(1 for r in rewards if r.reward_percent == 100),
        'half_rewards': sum(1 for r in rewards if r.reward_percent == 50),
        'reward_percent': CompanySettings.load().loyalty_reward_percent,
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
    """Download loyalty card as PDF"""
    loyalty_card = get_object_or_404(LoyaltyCard, pk=pk)
    
    # Generate the loyalty card PDF
    pdf_data = generate_loyalty_card_pdf(loyalty_card)
    
    # Return as downloadable PDF
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="loyalty_card_{loyalty_card.client.name}_{loyalty_card.cylinder_size}.pdf"'
    
    return response
