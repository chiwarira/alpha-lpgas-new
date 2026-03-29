import json
import logging
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models_whatsapp import (
    WhatsAppConversation, WhatsAppMessage, WhatsAppOrderIntent, WhatsAppConfig
)
from .serializers_whatsapp import (
    WhatsAppConversationSerializer, WhatsAppMessageSerializer,
    WhatsAppOrderIntentSerializer, WhatsAppConfigSerializer
)
from .services.whatsapp_ai_service import WhatsAppAIService
from .services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """
    Webhook endpoint for receiving WhatsApp messages
    
    This endpoint handles:
    1. Webhook verification (GET)
    2. Incoming messages (POST)
    """
    
    def get(self, request):
        """
        Webhook verification
        
        WhatsApp will send a GET request with:
        - hub.mode: 'subscribe'
        - hub.verify_token: your verification token
        - hub.challenge: random string to echo back
        """
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        config = WhatsAppConfig.load()
        
        if mode == 'subscribe' and token == config.webhook_verify_token:
            logger.info('WhatsApp webhook verified successfully')
            return HttpResponse(challenge, content_type='text/plain')
        else:
            logger.warning('WhatsApp webhook verification failed')
            return HttpResponse('Verification failed', status=403)
    
    def post(self, request):
        """
        Handle incoming WhatsApp messages
        
        WhatsApp sends POST requests with message data
        """
        try:
            # Parse incoming data
            data = json.loads(request.body)
            logger.info(f'Received WhatsApp webhook: {json.dumps(data, indent=2)}')
            
            # Check if config is active
            config = WhatsAppConfig.load()
            if not config.is_active:
                logger.info('WhatsApp integration is disabled')
                return JsonResponse({'status': 'disabled'}, status=200)
            
            # Extract message data
            if 'entry' not in data:
                return JsonResponse({'status': 'no_entry'}, status=200)
            
            for entry in data['entry']:
                if 'changes' not in entry:
                    continue
                
                for change in entry['changes']:
                    if change.get('field') != 'messages':
                        continue
                    
                    value = change.get('value', {})
                    
                    # Handle incoming messages
                    if 'messages' in value:
                        for message in value['messages']:
                            self._process_message(message, value)
                    
                    # Handle message status updates
                    if 'statuses' in value:
                        for status_update in value['statuses']:
                            self._process_status_update(status_update)
            
            return JsonResponse({'status': 'success'}, status=200)
        
        except Exception as e:
            logger.error(f'Error processing WhatsApp webhook: {str(e)}', exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    def _process_message(self, message: dict, value: dict):
        """Process incoming message"""
        try:
            message_type = message.get('type')
            message_id = message.get('id')
            timestamp = datetime.fromtimestamp(int(message.get('timestamp', 0)))
            from_number = message.get('from')
            
            # Only process text messages for now
            if message_type != 'text':
                logger.info(f'Skipping non-text message type: {message_type}')
                return
            
            message_content = message.get('text', {}).get('body', '')
            
            if not message_content:
                logger.warning('Empty message content')
                return
            
            # Process with AI service
            ai_service = WhatsAppAIService()
            result = ai_service.process_incoming_message(
                phone_number=from_number,
                message_content=message_content,
                whatsapp_message_id=message_id,
                timestamp=timestamp
            )
            
            # Send response if available
            if result.get('response'):
                whatsapp_service = WhatsAppService()
                send_result = whatsapp_service.send_text_message(
                    to=from_number,
                    message=result['response']
                )
                
                if not send_result.get('success'):
                    logger.error(f'Failed to send WhatsApp message: {send_result.get("error")}')
            
            # Mark message as read
            whatsapp_service = WhatsAppService()
            whatsapp_service.mark_as_read(message_id)
            
            logger.info(f'Processed message {message_id} - Action: {result.get("action")}')
        
        except Exception as e:
            logger.error(f'Error processing message: {str(e)}', exc_info=True)
    
    def _process_status_update(self, status_update: dict):
        """Process message status update (delivered, read, etc.)"""
        try:
            message_id = status_update.get('id')
            status_value = status_update.get('status')
            
            # Update message status in database
            message = WhatsAppMessage.objects.filter(
                whatsapp_message_id=message_id
            ).first()
            
            if message:
                if status_value == 'delivered':
                    message.delivered = True
                elif status_value == 'read':
                    message.read = True
                message.save()
                
                logger.info(f'Updated message {message_id} status to {status_value}')
        
        except Exception as e:
            logger.error(f'Error processing status update: {str(e)}', exc_info=True)


class WhatsAppConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing WhatsApp conversations"""
    queryset = WhatsAppConversation.objects.all()
    serializer_class = WhatsAppConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter conversations"""
        queryset = WhatsAppConversation.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by requires_human
        requires_human = self.request.query_params.get('requires_human')
        if requires_human is not None:
            queryset = queryset.filter(requires_human=requires_human.lower() == 'true')
        
        # Filter by client
        client_id = self.request.query_params.get('client_id')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        return queryset.order_by('-last_message_at')
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message to the conversation"""
        conversation = self.get_object()
        message_text = request.data.get('message')
        
        if not message_text:
            return Response(
                {'error': 'Message text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Send via WhatsApp
            whatsapp_service = WhatsAppService()
            result = whatsapp_service.send_text_message(
                to=conversation.phone_number,
                message=message_text
            )
            
            if not result.get('success'):
                return Response(
                    {'error': result.get('error')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Save message to database
            message = WhatsAppMessage.objects.create(
                conversation=conversation,
                direction='outbound',
                message_type='text',
                content=message_text,
                whatsapp_message_id=result['data']['messages'][0]['id'],
                whatsapp_timestamp=datetime.now()
            )
            
            return Response(
                WhatsAppMessageSerializer(message).data,
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            logger.error(f'Error sending message: {str(e)}', exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def assign_to_human(self, request, pk=None):
        """Assign conversation to a human agent"""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if user_id:
            conversation.assigned_to_id = user_id
        
        conversation.status = 'escalated'
        conversation.requires_human = True
        conversation.save()
        
        return Response(
            WhatsAppConversationSerializer(conversation).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark conversation as resolved"""
        conversation = self.get_object()
        conversation.status = 'resolved'
        conversation.requires_human = False
        conversation.save()
        
        return Response(
            WhatsAppConversationSerializer(conversation).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def pending_human_review(self, request):
        """Get conversations requiring human review"""
        conversations = WhatsAppConversation.objects.filter(
            requires_human=True,
            status='escalated'
        ).order_by('-last_message_at')
        
        serializer = self.get_serializer(conversations, many=True)
        return Response(serializer.data)


class WhatsAppMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing WhatsApp messages"""
    queryset = WhatsAppMessage.objects.all()
    serializer_class = WhatsAppMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter messages"""
        queryset = WhatsAppMessage.objects.all()
        
        # Filter by conversation
        conversation_id = self.request.query_params.get('conversation_id')
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        
        # Filter by direction
        direction = self.request.query_params.get('direction')
        if direction:
            queryset = queryset.filter(direction=direction)
        
        return queryset.order_by('created_at')


class WhatsAppOrderIntentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing order intents"""
    queryset = WhatsAppOrderIntent.objects.all()
    serializer_class = WhatsAppOrderIntentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter order intents"""
        queryset = WhatsAppOrderIntent.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by conversation
        conversation_id = self.request.query_params.get('conversation_id')
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        
        return queryset.order_by('-created_at')


class WhatsAppConfigView(View):
    """View for WhatsApp configuration"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get WhatsApp configuration"""
        config = WhatsAppConfig.load()
        serializer = WhatsAppConfigSerializer(config)
        return JsonResponse(serializer.data)
    
    def post(self, request):
        """Update WhatsApp configuration"""
        config = WhatsAppConfig.load()
        data = json.loads(request.body)
        
        serializer = WhatsAppConfigSerializer(config, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        
        return JsonResponse(serializer.errors, status=400)
