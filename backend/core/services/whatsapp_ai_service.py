import json
import re
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import openai
from anthropic import Anthropic
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.apps import apps


class WhatsAppAIService:
    """AI service for processing WhatsApp messages and automating order creation"""
    
    def __init__(self):
        # Get models dynamically to avoid circular imports
        self.WhatsAppConfig = apps.get_model('core', 'WhatsAppConfig')
        self.WhatsAppConversation = apps.get_model('core', 'WhatsAppConversation')
        self.WhatsAppMessage = apps.get_model('core', 'WhatsAppMessage')
        self.WhatsAppOrderIntent = apps.get_model('core', 'WhatsAppOrderIntent')
        self.Client = apps.get_model('core', 'Client')
        self.Product = apps.get_model('core', 'Product')
        self.Invoice = apps.get_model('core', 'Invoice')
        self.InvoiceItem = apps.get_model('core', 'InvoiceItem')
        self.Order = apps.get_model('core', 'Order')
        self.OrderItem = apps.get_model('core', 'OrderItem')
        self.Driver = apps.get_model('core', 'Driver')
        self.DeliveryZone = apps.get_model('core', 'DeliveryZone')
        
        self.config = self.WhatsAppConfig.load()
        self._setup_ai_client()
    
    def _setup_ai_client(self):
        """Initialize AI client based on configuration"""
        if self.config.ai_provider == 'openai':
            openai.api_key = self.config.ai_api_key
            self.ai_client = openai
        elif self.config.ai_provider == 'anthropic':
            self.ai_client = Anthropic(api_key=self.config.ai_api_key)
    
    def process_incoming_message(self, phone_number: str, message_content: str, 
                                 whatsapp_message_id: str, timestamp: datetime) -> Dict:
        """
        Main entry point for processing incoming WhatsApp messages
        
        Returns: Dict with response message and actions taken
        """
        # Get or create conversation
        conversation = self._get_or_create_conversation(phone_number)
        
        # Save incoming message
        message = self.WhatsAppMessage.objects.create(
            conversation=conversation,
            direction='inbound',
            message_type='text',
            content=message_content,
            whatsapp_message_id=whatsapp_message_id,
            whatsapp_timestamp=timestamp
        )
        
        # Check business hours
        if not self._is_business_hours() and self.config.auto_respond_outside_hours:
            return {
                'response': self.config.outside_hours_message,
                'action': 'outside_hours',
                'requires_human': True
            }
        
        # Get conversation history
        conversation_history = self._build_conversation_history(conversation)
        
        # Process with AI
        ai_result = self._process_with_ai(message_content, conversation_history, conversation)
        
        # Update message with AI processing results
        message.ai_processed = True
        message.ai_intent = ai_result.get('intent', '')
        message.ai_extracted_data = ai_result.get('extracted_data', {})
        message.ai_response = ai_result.get('response', '')
        message.save()
        
        # Update conversation context
        conversation.conversation_context.update(ai_result.get('context_update', {}))
        conversation.ai_confidence_score = ai_result.get('confidence', 0)
        conversation.save()
        
        # Handle based on intent
        result = self._handle_intent(ai_result, conversation, message)
        
        # Save outbound message
        if result.get('response'):
            self.WhatsAppMessage.objects.create(
                conversation=conversation,
                direction='outbound',
                message_type='text',
                content=result['response'],
                whatsapp_message_id=f"out_{whatsapp_message_id}",
                whatsapp_timestamp=timezone.now()
            )
        
        return result
    
    def _get_or_create_conversation(self, phone_number: str):
        """Get existing active conversation or create new one"""
        # Clean phone number
        clean_phone = self._clean_phone_number(phone_number)
        
        # Try to find existing active conversation
        conversation = self.WhatsAppConversation.objects.filter(
            phone_number=clean_phone,
            status='active'
        ).first()
        
        if not conversation:
            # Try to find client by phone
            client = self.Client.objects.filter(phone__icontains=clean_phone[-9:]).first()
            
            conversation = self.WhatsAppConversation.objects.create(
                phone_number=clean_phone,
                client=client,
                status='active'
            )
        
        return conversation
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and standardize phone number"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle South African numbers
        if digits.startswith('27'):
            return f"+{digits}"
        elif digits.startswith('0'):
            return f"+27{digits[1:]}"
        else:
            return f"+27{digits}"
    
    def _is_business_hours(self) -> bool:
        """Check if current time is within business hours"""
        now = timezone.localtime().time()
        return self.config.business_hours_start <= now <= self.config.business_hours_end
    
    def _build_conversation_history(self, conversation, limit: int = 10) -> List[Dict]:
        """Build conversation history for AI context"""
        messages = conversation.messages.order_by('-created_at')[:limit]
        
        history = []
        for msg in reversed(messages):
            role = 'user' if msg.direction == 'inbound' else 'assistant'
            history.append({
                'role': role,
                'content': msg.content
            })
        
        return history
    
    def _process_with_ai(self, message: str, history: List[Dict], 
                         conversation) -> Dict:
        """Process message with AI to extract intent and data"""
        
        # Get available products
        products = self.Product.objects.filter(is_active=True, show_on_website=True)
        product_list = "\n".join([
            f"- {p.name} ({p.weight}): R{p.unit_price}"
            for p in products
        ])
        
        # Build enhanced system prompt
        system_prompt = f"""{self.config.system_prompt}

AVAILABLE PRODUCTS:
{product_list}

CURRENT CONVERSATION CONTEXT:
{json.dumps(conversation.conversation_context, indent=2)}

CLIENT INFO:
{f"Name: {conversation.client.name}, Address: {conversation.client.address}" if conversation.client else "New customer - need to collect details"}

INSTRUCTIONS:
1. Analyze the customer's message and determine their intent
2. Extract relevant data (products, quantities, address, etc.)
3. Provide a helpful, friendly response
4. If order details are complete and clear, set intent to 'order_ready'
5. If anything is unclear or missing, ask clarifying questions
6. Set confidence score (0-100) based on how clear the request is

Respond in JSON format:
{{
    "intent": "place_order|check_status|ask_question|order_ready|unclear",
    "confidence": 85,
    "extracted_data": {{
        "products": [
            {{"name": "9kg Gas Cylinder", "quantity": 2, "unit_price": 250.00}}
        ],
        "delivery_address": "123 Main St, Fish Hoek",
        "delivery_notes": "Gate code 1234"
    }},
    "response": "Your friendly response to the customer",
    "context_update": {{"order_stage": "confirming_details"}},
    "requires_human": false,
    "escalation_reason": ""
}}
"""
        
        # Prepare messages for AI
        messages = [
            {'role': 'system', 'content': system_prompt}
        ] + history + [
            {'role': 'user', 'content': message}
        ]
        
        try:
            if self.config.ai_provider == 'openai':
                response = self.ai_client.chat.completions.create(
                    model=self.config.ai_model,
                    messages=messages,
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                ai_response = json.loads(response.choices[0].message.content)
            
            elif self.config.ai_provider == 'anthropic':
                response = self.ai_client.messages.create(
                    model=self.config.ai_model,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[msg for msg in messages if msg['role'] != 'system']
                )
                ai_response = json.loads(response.content[0].text)
            
            return ai_response
        
        except Exception as e:
            # Fallback response on AI error
            return {
                'intent': 'unclear',
                'confidence': 0,
                'extracted_data': {},
                'response': "I'm having trouble processing your request. Let me connect you with a team member who can help.",
                'context_update': {},
                'requires_human': True,
                'escalation_reason': f'AI processing error: {str(e)}'
            }
    
    def _handle_intent(self, ai_result: Dict, conversation, 
                       message) -> Dict:
        """Handle different intents and take appropriate actions"""
        
        intent = ai_result.get('intent', 'unclear')
        confidence = ai_result.get('confidence', 0)
        requires_human = ai_result.get('requires_human', False)
        
        # Check if confidence is too low
        if confidence < self.config.min_confidence_threshold:
            requires_human = True
            ai_result['escalation_reason'] = f'Low confidence: {confidence}%'
        
        # Handle escalation
        if requires_human:
            conversation.requires_human = True
            conversation.escalation_reason = ai_result.get('escalation_reason', 'AI requested human intervention')
            conversation.status = 'escalated'
            conversation.save()
            
            return {
                'response': ai_result.get('response', '') + "\n\nA team member will assist you shortly.",
                'action': 'escalated',
                'requires_human': True
            }
        
        # Handle order_ready intent
        if intent == 'order_ready':
            return self._process_order(ai_result, conversation, message)
        
        # Handle other intents
        return {
            'response': ai_result.get('response', ''),
            'action': intent,
            'requires_human': False
        }
    
    def _process_order(self, ai_result: Dict, conversation,
                      message) -> Dict:
        """Process and create order/invoice from extracted data"""
        
        extracted_data = ai_result.get('extracted_data', {})
        
        # Validate extracted data
        if not extracted_data.get('products') or not extracted_data.get('delivery_address'):
            return {
                'response': "I need a bit more information. Please confirm:\n1. What products and quantities?\n2. Delivery address?",
                'action': 'need_more_info',
                'requires_human': False
            }
        
        try:
            with transaction.atomic():
                # Create order intent record
                order_intent = self.WhatsAppOrderIntent.objects.create(
                    conversation=conversation,
                    message=message,
                    status='confirmed',
                    products_data=extracted_data.get('products', []),
                    delivery_address=extracted_data.get('delivery_address', ''),
                    delivery_notes=extracted_data.get('delivery_notes', ''),
                    confidence_score=ai_result.get('confidence', 0)
                )
                
                # Get or create client
                client = self._get_or_create_client(conversation, extracted_data)
                conversation.client = client
                conversation.save()
                
                # Find delivery zone
                delivery_zone = self._find_delivery_zone(extracted_data.get('delivery_address', ''))
                
                # Calculate totals
                subtotal = Decimal('0.00')
                products_list = []
                
                for product_data in extracted_data.get('products', []):
                    # Find product
                    product = self._find_product(product_data)
                    if product:
                        quantity = Decimal(str(product_data.get('quantity', 1)))
                        item_total = product.unit_price * quantity
                        subtotal += item_total
                        products_list.append({
                            'product': product,
                            'quantity': quantity,
                            'unit_price': product.unit_price
                        })
                
                delivery_fee = delivery_zone.delivery_fee if delivery_zone else Decimal('0.00')
                total = subtotal + delivery_fee
                
                # Update order intent
                order_intent.subtotal = subtotal
                order_intent.delivery_fee = delivery_fee
                order_intent.total = total
                order_intent.delivery_zone = delivery_zone
                order_intent.save()
                
                # Create invoice if enabled
                invoice = None
                if self.config.auto_create_invoices:
                    invoice = self._create_invoice(client, products_list, delivery_zone, extracted_data)
                    order_intent.created_invoice = invoice
                    conversation.created_invoice = invoice
                
                # Create order
                order = self._create_order(client, products_list, delivery_zone, extracted_data, total, subtotal, delivery_fee)
                order_intent.created_order = order
                conversation.created_order = order
                order_intent.save()
                conversation.save()
                
                # Auto-assign driver if enabled
                assigned_driver = None
                if self.config.auto_assign_drivers:
                    assigned_driver = self._assign_driver(order, delivery_zone)
                
                # Mark conversation as resolved
                conversation.status = 'resolved'
                conversation.save()
                
                # Build confirmation message
                response = self._build_order_confirmation(
                    order, invoice, products_list, total, delivery_fee, assigned_driver
                )
                
                return {
                    'response': response,
                    'action': 'order_created',
                    'requires_human': False,
                    'invoice_id': invoice.id if invoice else None,
                    'order_id': order.id if order else None
                }
        
        except Exception as e:
            # Handle errors
            conversation.requires_human = True
            conversation.escalation_reason = f'Error creating order: {str(e)}'
            conversation.status = 'escalated'
            conversation.save()
            
            return {
                'response': "I encountered an issue processing your order. A team member will contact you shortly to complete your order.",
                'action': 'error',
                'requires_human': True,
                'error': str(e)
            }
    
    def _get_or_create_client(self, conversation, 
                             extracted_data: Dict):
        """Get existing client or create new one"""
        
        if conversation.client:
            # Update address if provided
            if extracted_data.get('delivery_address'):
                conversation.client.address = extracted_data['delivery_address']
                conversation.client.save()
            return conversation.client
        
        # Extract name from conversation or use phone
        name = extracted_data.get('customer_name', conversation.phone_number)
        
        # Create new client
        client = self.Client.objects.create(
            name=name,
            phone=conversation.phone_number,
            address=extracted_data.get('delivery_address', ''),
            email=extracted_data.get('email', ''),
            is_active=True
        )
        
        return client
    
    def _find_product(self, product_data: Dict):
        """Find product by name or SKU"""
        name = product_data.get('name', '')
        
        # Try exact match first
        product = self.Product.objects.filter(
            name__iexact=name,
            is_active=True
        ).first()
        
        if product:
            return product
        
        # Try partial match
        product = self.Product.objects.filter(
            name__icontains=name,
            is_active=True
        ).first()
        
        if product:
            return product
        
        # Try matching by weight (e.g., "9kg")
        weight_match = re.search(r'(\d+)\s*kg', name, re.IGNORECASE)
        if weight_match:
            weight = weight_match.group(1) + 'kg'
            product = self.Product.objects.filter(
                weight__icontains=weight,
                is_active=True
            ).first()
        
        return product
    
    def _find_delivery_zone(self, address: str):
        """Find delivery zone based on address"""
        # Simple matching - can be enhanced with geocoding
        for zone in self.DeliveryZone.objects.filter(is_active=True):
            if zone.name.lower() in address.lower():
                return zone
        
        return None
    
    def _create_invoice(self, client, products_list: List[Dict],
                       delivery_zone, extracted_data: Dict):
        """Create invoice from order data"""
        
        invoice = self.Invoice.objects.create(
            client=client,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=7),
            delivery_zone=delivery_zone,
            delivery_note=extracted_data.get('delivery_notes', ''),
            status='unpaid',
            payment_terms='immediate'
        )
        
        # Add invoice items
        for item_data in products_list:
            self.InvoiceItem.objects.create(
                invoice=invoice,
                product=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                tax_rate=item_data['product'].tax_rate
            )
        
        # Calculate totals
        invoice.calculate_totals()
        
        return invoice
    
    def _create_order(self, client, products_list: List[Dict],
                     delivery_zone, extracted_data: Dict,
                     total: Decimal, subtotal: Decimal, delivery_fee: Decimal):
        """Create order from order data"""
        
        order = self.Order.objects.create(
            customer_name=client.name,
            customer_email=client.email,
            customer_phone=client.phone,
            delivery_address=extracted_data.get('delivery_address', client.address),
            delivery_zone=delivery_zone,
            delivery_notes=extracted_data.get('delivery_notes', ''),
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=total,
            payment_method='cash',
            status='confirmed'
        )
        
        # Add order items
        for item_data in products_list:
            self.OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=int(item_data['quantity']),
                unit_price=item_data['unit_price']
            )
        
        return order
    
    def _assign_driver(self, order, delivery_zone):
        """Auto-assign available driver to order"""
        
        # Find available drivers
        available_driver = self.Driver.objects.filter(
            is_active=True,
            status='available'
        ).first()
        
        if available_driver:
            order.assigned_driver = available_driver
            order.status = 'preparing'
            order.save()
            
            # Update driver status
            available_driver.status = 'on_delivery'
            available_driver.save()
        
        return available_driver
    
    def _build_order_confirmation(self, order, invoice,
                                  products_list: List[Dict], total: Decimal,
                                  delivery_fee: Decimal, driver) -> str:
        """Build order confirmation message"""
        
        products_text = "\n".join([
            f"• {item['product'].name} x {item['quantity']} - R{item['unit_price'] * item['quantity']:.2f}"
            for item in products_list
        ])
        
        message = f"""✅ Order Confirmed! 

Order Number: {order.order_number}
{'Invoice: ' + invoice.invoice_number if invoice else ''}

📦 Items:
{products_text}

💰 Summary:
Subtotal: R{order.subtotal:.2f}
Delivery Fee: R{delivery_fee:.2f}
Total: R{total:.2f}

📍 Delivery Address:
{order.delivery_address}

{f'🚚 Driver Assigned: {driver.user.get_full_name()}' if driver else '🚚 Driver will be assigned shortly'}

Estimated Delivery: {order.delivery_zone.estimated_delivery_time if order.delivery_zone else 'Same day'}

Thank you for choosing Alpha LPGas! 🔥"""
        
        return message
