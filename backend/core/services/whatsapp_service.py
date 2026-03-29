import requests
import json
from typing import Dict, Optional
from django.conf import settings
from ..models_whatsapp import WhatsAppConfig


class WhatsAppService:
    """Service for sending messages via WhatsApp Business API"""
    
    def __init__(self):
        self.config = WhatsAppConfig.load()
        self.base_url = f"https://graph.facebook.com/v18.0/{self.config.phone_number_id}"
        self.headers = {
            'Authorization': f'Bearer {self.config.access_token}',
            'Content-Type': 'application/json'
        }
    
    def send_text_message(self, to: str, message: str) -> Dict:
        """
        Send a text message via WhatsApp
        
        Args:
            to: Recipient phone number (with country code)
            message: Message text to send
            
        Returns:
            Dict with response data or error
        """
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'response': response.text if 'response' in locals() else None
            }
    
    def send_template_message(self, to: str, template_name: str, 
                             language_code: str = 'en', 
                             components: Optional[list] = None) -> Dict:
        """
        Send a template message via WhatsApp
        
        Args:
            to: Recipient phone number
            template_name: Name of approved template
            language_code: Language code (default: 'en')
            components: Template components (parameters, buttons, etc.)
            
        Returns:
            Dict with response data or error
        """
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'response': response.text if 'response' in locals() else None
            }
    
    def send_document(self, to: str, document_url: str, 
                     caption: Optional[str] = None, 
                     filename: Optional[str] = None) -> Dict:
        """
        Send a document (PDF, etc.) via WhatsApp
        
        Args:
            to: Recipient phone number
            document_url: URL of the document to send
            caption: Optional caption
            filename: Optional filename
            
        Returns:
            Dict with response data or error
        """
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {
                "link": document_url
            }
        }
        
        if caption:
            payload["document"]["caption"] = caption
        
        if filename:
            payload["document"]["filename"] = filename
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'response': response.text if 'response' in locals() else None
            }
    
    def send_image(self, to: str, image_url: str, 
                  caption: Optional[str] = None) -> Dict:
        """
        Send an image via WhatsApp
        
        Args:
            to: Recipient phone number
            image_url: URL of the image to send
            caption: Optional caption
            
        Returns:
            Dict with response data or error
        """
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {
                "link": image_url
            }
        }
        
        if caption:
            payload["image"]["caption"] = caption
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'response': response.text if 'response' in locals() else None
            }
    
    def mark_as_read(self, message_id: str) -> Dict:
        """
        Mark a message as read
        
        Args:
            message_id: WhatsApp message ID
            
        Returns:
            Dict with response data or error
        """
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
