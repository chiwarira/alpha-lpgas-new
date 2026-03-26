import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Invoice, Payment, Client


# Descriptions to skip - these are not EFT payments from clients
SKIP_DESCRIPTIONS = [
    'carried forward', 'brought forward', 'provisional statement',
    'yoco', 'maintenance fee', 'vat ',
]

# Prefixes that indicate outgoing payments / expenses (not client payments)
EXPENSE_KEYWORDS = [
    'oscar gas', 'linkgas', 'blouwinkel', 'cylinders', 'cylinder',
    'fuel', 'wages', 'salary', 'rent', 'reimbursement', 'loan',
    'deposit', 'nedbank send', 'instant payment fee',
    'sasol', 'shell', 'digitalocean', 'google workspa', 'afrihost',
    'railway', 'openai', 'vodacom', 'mtn', 'cartrack', 'checkers',
    'dischem', 'starbucks', 'windsurf', 'suburban', 'village serv',
    'prepaid electricity', 'schaap', 'lekkerwater', 'paul wages',
    'fanuel', 'grace wages', 'redfern', 'palisade', 'sunnyacres',
    'nomenti gas', 'payfast', 'takealot', 'zororophum', 'netcash',
    'gas cylinders', 'gas contents', 'fungai loan', 'cash deposit',
    'payprop',
]


def similarity_ratio(a, b):
    """Calculate similarity ratio between two strings (case-insensitive)"""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def partial_contains(haystack, needle):
    """Check if any word (3+ chars) from needle appears in haystack"""
    if not haystack or not needle:
        return False
    haystack_lower = haystack.lower()
    needle_lower = needle.lower()
    # Direct substring check
    if needle_lower in haystack_lower or haystack_lower in needle_lower:
        return True
    # Check individual words
    words = [w for w in re.split(r'[\s,./\-]+', needle_lower) if len(w) >= 3]
    matched_words = sum(1 for w in words if w in haystack_lower)
    if words and matched_words / len(words) >= 0.5:
        return True
    return False


def extract_invoice_number(description):
    """Try to extract an invoice number from the description."""
    if not description:
        return None
    desc = description.upper().strip()
    # Match patterns like: INV-004185, INV 004555, INV004220, inv4239, #004902, 004902
    patterns = [
        r'INV[- ]?(\d{3,6})',        # INV-004185, INV 004555, INV004220
        r'#\s*(\d{3,6})',             # #004902
        r'(\d{4,6})\b',              # standalone 4-6 digit number (only used as fallback)
    ]
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, desc)
        if match:
            num = match.group(1).lstrip('0') or '0'
            return num, (i < 2)  # (number, is_strong_match)
    return None


def is_skip_row(description):
    """Check if this row should be skipped entirely."""
    desc_lower = description.lower().strip()
    for skip in SKIP_DESCRIPTIONS:
        if skip in desc_lower:
            return True
    return False


def is_expense(description):
    """Check if this row is an expense / outgoing payment."""
    desc_lower = description.lower().strip()
    for keyword in EXPENSE_KEYWORDS:
        if keyword in desc_lower:
            return True
    return False


def _score_description_match(invoice, description):
    """
    Score how well a bank description matches an invoice's client info.
    Returns (score, reasons) where score > 0 means some description evidence.
    """
    score = 0
    reasons = []
    description_lower = description.lower() if description else ''
    
    if not description_lower:
        return score, reasons
    
    # 1. Check if invoice number appears in description
    inv_num_raw = invoice.invoice_number  # e.g. INV-004185
    inv_num_digits = inv_num_raw.replace('INV-', '').replace('INV', '').lstrip('0') or '0'
    
    if inv_num_raw.lower() in description_lower:
        score += 60
        reasons.append(f"Invoice number '{inv_num_raw}' found in description")
    else:
        extracted = extract_invoice_number(description)
        if extracted:
            extracted_num, is_strong = extracted
            if extracted_num == inv_num_digits:
                score += 50 if is_strong else 30
                reasons.append(f"Invoice number match: {inv_num_raw}")
    
    # 2. Check client name match
    client_name = invoice.client.name
    if client_name:
        # Split client name into parts and check each
        name_parts = [p for p in client_name.lower().split() if len(p) >= 3]
        name_in_desc = any(part in description_lower for part in name_parts)
        
        if name_in_desc:
            score += 35
            reasons.append(f"Client name '{client_name}' found in description")
        elif partial_contains(description, client_name):
            score += 30
            reasons.append(f"Client name '{client_name}' matches description")
        else:
            name_similarity = similarity_ratio(client_name, description)
            if name_similarity > 0.55:
                score += int(name_similarity * 25)
                reasons.append(f"Client name similarity: {int(name_similarity * 100)}%")
    
    # 3. Check client address match
    client_address = invoice.client.address
    if client_address:
        # Extract key address components (numbers and street names)
        addr_parts = [p for p in re.split(r'[\s,./\-]+', client_address.lower()) if len(p) >= 2]
        desc_parts = [p for p in re.split(r'[\s,./\-]+', description_lower) if len(p) >= 2]
        
        # Count how many address parts appear in description
        matched_parts = sum(1 for p in addr_parts if p in description_lower)
        
        if addr_parts and matched_parts >= 2:
            # At least 2 address components match (e.g. street number + street name)
            score += 35
            reasons.append(f"Address '{client_address}' matches description")
        elif addr_parts and matched_parts == 1 and any(p.isdigit() for p in addr_parts if p in description_lower):
            # A street number matches - weaker signal but still useful with name
            score += 15
            reasons.append(f"Partial address match: '{client_address}'")
        elif partial_contains(description, client_address):
            score += 25
            reasons.append(f"Address '{client_address}' matches description")
        else:
            addr_similarity = similarity_ratio(client_address, description)
            if addr_similarity > 0.45:
                score += int(addr_similarity * 20)
                reasons.append(f"Address similarity: {int(addr_similarity * 100)}%")
    
    # 4. Check city match
    client_city = invoice.client.city
    if client_city and len(client_city) >= 3:
        if client_city.lower() in description_lower:
            score += 10
            reasons.append(f"City '{client_city}' found in description")
    
    return score, reasons


def find_matching_invoices(description, amount, payment_date):
    """
    Find potential invoice matches.
    
    Primary matching criteria (at least one must match):
      1. Client name found in description
      2. Client address found in description
      3. Invoice number found in description
    
    Secondary filter (used to boost/rank, not to match alone):
      - Exact amount match between payment and invoice balance
    
    Invoices with NO primary match are never returned.
    """
    amount_decimal = Decimal(str(amount))
    
    # Get all unpaid/partially paid invoices where issue_date <= payment_date
    unpaid_invoices = Invoice.objects.filter(
        Q(status='unpaid') | Q(status='partially_paid'),
        issue_date__lte=payment_date,
    ).select_related('client')
    
    matches = []
    
    for invoice in unpaid_invoices:
        desc_score, desc_reasons = _score_description_match(invoice, description)
        
        # Primary criteria: must have at least one description match
        if desc_score <= 0:
            continue
        
        # Secondary: check if amount also matches
        amount_match = abs(amount_decimal - invoice.balance) < Decimal('0.01')
        
        if amount_match:
            # Boost score for exact amount match
            total_score = desc_score + 20
            desc_reasons.append(f"Exact amount match: R{invoice.balance}")
        else:
            total_score = desc_score
            desc_reasons.append(f"Amount mismatch: invoice R{invoice.balance}, payment R{amount_decimal}")
        
        matches.append({
            'invoice': invoice,
            'match_score': total_score,
            'match_reasons': desc_reasons,
            'amount_match': amount_match,
        })
    
    # Sort: amount-matched first, then by score
    matches.sort(key=lambda x: (-int(x['amount_match']), -x['match_score']))
    
    return matches[:5]


def parse_nedbank_date(date_str):
    """Parse Nedbank date format: DDMonYYYY (e.g. 01Feb2026)"""
    date_str = date_str.strip()
    # Try Nedbank format first: DDMonYYYY
    try:
        return datetime.strptime(date_str, '%d%b%Y').date()
    except ValueError:
        pass
    # Fallback formats
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


@login_required
def eft_reconciliation_upload(request):
    """Upload CSV bank statement for EFT reconciliation"""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, 'Please select a CSV file to upload.')
            return render(request, 'core/eft_reconciliation_upload.html')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file.')
            return render(request, 'core/eft_reconciliation_upload.html')
        
        try:
            # Read CSV file
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.reader(io.StringIO(decoded_file))
            
            # Skip Nedbank header rows (4 rows):
            # Row 1: "Statement Enquiry :"
            # Row 2: "Account Number : ,1101466707"
            # Row 3: "Account Description :,Alpha LPG Savvy Plus"
            # Row 4: "Statement Number : ,737,"
            for _ in range(4):
                next(csv_reader, None)
            
            # Process data rows
            # Format: Col0=Date(DDMonYYYY), Col1=Description, Col2=Amount, Col3=RunningBalance
            bank_transactions = []
            skipped_count = 0
            
            for row_num, row in enumerate(csv_reader, start=5):
                if len(row) < 3:
                    continue
                
                try:
                    date_str = row[0].strip()
                    description = row[1].strip()
                    amount_str = row[2].strip() if len(row) > 2 else ''
                    
                    # Skip rows with no date
                    if not date_str:
                        continue
                    
                    # Skip rows with empty amount
                    if not amount_str:
                        continue
                    
                    # Parse date
                    payment_date = parse_nedbank_date(date_str)
                    if not payment_date:
                        continue
                    
                    # Parse amount
                    amount_clean = amount_str.replace('R', '').replace(',', '').replace(' ', '').strip()
                    try:
                        amount = float(amount_clean)
                    except ValueError:
                        continue
                    
                    # Skip negative amounts (debits/expenses)
                    if amount <= 0:
                        continue
                    
                    # Skip non-EFT rows
                    if is_skip_row(description):
                        skipped_count += 1
                        continue
                    
                    # Skip known expenses
                    if is_expense(description):
                        skipped_count += 1
                        continue
                    
                    # Skip YOCO transactions (card payments, not EFT)
                    if description.upper().startswith('YOCO'):
                        skipped_count += 1
                        continue
                    
                    # Find matching invoices (exact amount match required)
                    invoice_matches = find_matching_invoices(description, amount, payment_date)
                    
                    bank_transactions.append({
                        'row_num': row_num,
                        'date': payment_date,
                        'amount': amount,
                        'description': description,
                        'matches': invoice_matches[:5]
                    })
                
                except Exception as e:
                    continue
            
            if not bank_transactions:
                messages.warning(request, 'No EFT transactions found in the CSV file.')
                return render(request, 'core/eft_reconciliation_upload.html')
            
            matched_count = sum(1 for t in bank_transactions if t['matches'])
            
            # Store in session for review page
            request.session['bank_transactions'] = [
                {
                    'row_num': t['row_num'],
                    'date': t['date'].isoformat(),
                    'amount': str(t['amount']),
                    'description': t['description'],
                    'matches': [
                        {
                            'invoice_id': m['invoice'].id,
                            'invoice_number': m['invoice'].invoice_number,
                            'client_name': m['invoice'].client.name,
                            'client_address': m['invoice'].client.address or '',
                            'balance': str(m['invoice'].balance),
                            'issue_date': m['invoice'].issue_date.isoformat(),
                            'match_score': m['match_score'],
                            'match_reasons': m['match_reasons'],
                            'amount_match': m.get('amount_match', False),
                        }
                        for m in t['matches']
                    ]
                }
                for t in bank_transactions
            ]
            
            messages.success(
                request,
                f'Processed {len(bank_transactions)} EFT transactions. '
                f'{matched_count} have invoice matches. '
                f'{skipped_count} non-EFT rows were skipped.'
            )
            return redirect('accounting_forms:eft_reconciliation_review')
        
        except Exception as e:
            messages.error(request, f'Error processing CSV file: {str(e)}')
            return render(request, 'core/eft_reconciliation_upload.html')
    
    return render(request, 'core/eft_reconciliation_upload.html')


@login_required
def eft_reconciliation_review(request):
    """Review and accept/reject EFT payment matches"""
    bank_transactions = request.session.get('bank_transactions', [])
    
    if not bank_transactions:
        messages.warning(request, 'No transactions to review. Please upload a bank statement first.')
        return redirect('accounting_forms:eft_reconciliation_upload')
    
    if request.method == 'POST':
        accepted_count = 0
        
        for transaction in bank_transactions:
            row_num = transaction['row_num']
            action = request.POST.get(f'action_{row_num}')
            
            if action == 'accept':
                selected_invoice_id = request.POST.get(f'invoice_{row_num}')
                
                if selected_invoice_id:
                    try:
                        invoice = Invoice.objects.get(id=int(selected_invoice_id))
                        payment_date = datetime.fromisoformat(transaction['date']).date()
                        amount = Decimal(transaction['amount'])
                        
                        # Create payment record
                        Payment.objects.create(
                            client=invoice.client,
                            invoice=invoice,
                            payment_date=payment_date,
                            amount=amount,
                            payment_method='eft',
                            reference_number=transaction['description'][:100],
                            notes=f"EFT reconciliation from bank statement (Row {row_num})",
                            created_by=request.user
                        )
                        
                        accepted_count += 1
                    
                    except Exception as e:
                        messages.error(request, f'Error creating payment for row {row_num}: {str(e)}')
        
        # Clear session
        if 'bank_transactions' in request.session:
            del request.session['bank_transactions']
        
        if accepted_count > 0:
            messages.success(request, f'Successfully created {accepted_count} EFT payment(s).')
        else:
            messages.info(request, 'No payments were created.')
        
        return redirect('accounting_forms:payment_list')
    
    # Prepare data for template
    transactions_with_invoices = []
    for transaction in bank_transactions:
        matches = []
        for match in transaction['matches']:
            try:
                invoice = Invoice.objects.select_related('client').get(id=match['invoice_id'])
                matches.append({
                    'invoice': invoice,
                    'match_score': match['match_score'],
                    'match_reasons': match['match_reasons'],
                    'amount_match': match.get('amount_match', False),
                })
            except Invoice.DoesNotExist:
                continue
        
        transactions_with_invoices.append({
            'row_num': transaction['row_num'],
            'date': datetime.fromisoformat(transaction['date']),
            'amount': Decimal(transaction['amount']),
            'description': transaction['description'],
            'matches': matches,
            'has_matches': len(matches) > 0,
        })
    
    # Sort: transactions with matches first
    transactions_with_invoices.sort(key=lambda x: (-int(x['has_matches']), -len(x['matches'])))
    
    matched_count = sum(1 for t in transactions_with_invoices if t['has_matches'])
    unmatched_count = len(transactions_with_invoices) - matched_count
    
    context = {
        'transactions': transactions_with_invoices,
        'matched_count': matched_count,
        'unmatched_count': unmatched_count,
        'total_count': len(transactions_with_invoices),
    }
    
    return render(request, 'core/eft_reconciliation_review.html', context)
