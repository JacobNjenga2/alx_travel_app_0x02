#!/usr/bin/env python3
"""
Chapa Payment Gateway Service

This module handles all interactions with the Chapa API for payment processing.
"""

import requests
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)


class ChapaPaymentService:
    """Service class for Chapa payment gateway integration."""
    
    def __init__(self):
        self.secret_key = getattr(settings, 'CHAPA_SECRET_KEY', None)
        self.base_url = getattr(settings, 'CHAPA_BASE_URL', 'https://api.chapa.co/v1')
        
        if not self.secret_key:
            raise ValueError("CHAPA_SECRET_KEY not configured in settings")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Chapa API requests."""
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Chapa API."""
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers()
        
        try:
            logger.info(f"Making {method} request to Chapa: {url}")
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            logger.info(f"Chapa API response status: {response.status_code}")
            
            # Log response for debugging (without sensitive data)
            if response.status_code >= 400:
                logger.error(f"Chapa API error: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Chapa API request failed: {str(e)}")
            raise ChapaAPIException(f"Payment gateway error: {str(e)}")
        except ValueError as e:
            logger.error(f"Chapa API JSON decode error: {str(e)}")
            raise ChapaAPIException(f"Invalid response from payment gateway")
    
    def initiate_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate payment with Chapa.
        
        Args:
            payment_data: Dictionary containing payment information
            
        Returns:
            Dict containing Chapa response with checkout URL and transaction ID
        """
        
        # Prepare Chapa payment request
        chapa_data = {
            "amount": str(payment_data['amount']),
            "currency": payment_data.get('currency', 'ETB'),
            "email": payment_data['customer_email'],
            "first_name": payment_data['customer_name'].split()[0] if payment_data['customer_name'] else '',
            "last_name": ' '.join(payment_data['customer_name'].split()[1:]) if len(payment_data['customer_name'].split()) > 1 else '',
            "phone_number": payment_data.get('customer_phone', ''),
            "tx_ref": payment_data['reference'],
            "callback_url": payment_data.get('callback_url', ''),
            "return_url": payment_data.get('return_url', ''),
            "description": f"Payment for booking {payment_data.get('booking_id', '')}",
            "meta": {
                "booking_id": payment_data.get('booking_id'),
                "customer_name": payment_data['customer_name']
            }
        }
        
        # Remove empty fields
        chapa_data = {k: v for k, v in chapa_data.items() if v}
        
        logger.info(f"Initiating Chapa payment for reference: {payment_data['reference']}")
        
        try:
            response = self._make_request('POST', 'transaction/initialize', chapa_data)
            
            if response.get('status') == 'success':
                return {
                    'success': True,
                    'checkout_url': response['data']['checkout_url'],
                    'transaction_id': response['data']['tx_ref'],
                    'reference': payment_data['reference'],
                    'message': 'Payment initiated successfully'
                }
            else:
                logger.error(f"Chapa payment initiation failed: {response}")
                return {
                    'success': False,
                    'error': response.get('message', 'Payment initiation failed'),
                    'details': response
                }
                
        except Exception as e:
            logger.error(f"Payment initiation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify payment status with Chapa.
        
        Args:
            transaction_id: Transaction reference to verify
            
        Returns:
            Dict containing payment verification result
        """
        logger.info(f"Verifying Chapa payment: {transaction_id}")
        
        try:
            response = self._make_request('GET', f'transaction/verify/{transaction_id}')
            
            if response.get('status') == 'success':
                payment_data = response['data']
                
                return {
                    'success': True,
                    'status': payment_data.get('status'),
                    'amount': Decimal(str(payment_data.get('amount', '0'))),
                    'currency': payment_data.get('currency'),
                    'transaction_id': payment_data.get('tx_ref'),
                    'reference': payment_data.get('reference'),
                    'payment_method': payment_data.get('type'),
                    'created_at': payment_data.get('created_at'),
                    'updated_at': payment_data.get('updated_at'),
                    'raw_response': payment_data
                }
            else:
                logger.error(f"Chapa payment verification failed: {response}")
                return {
                    'success': False,
                    'error': response.get('message', 'Payment verification failed'),
                    'details': response
                }
                
        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_status(self, transaction_id: str) -> str:
        """
        Get simplified payment status.
        
        Args:
            transaction_id: Transaction reference
            
        Returns:
            Payment status string
        """
        verification_result = self.verify_payment(transaction_id)
        
        if verification_result['success']:
            chapa_status = verification_result.get('status', '').lower()
            
            # Map Chapa status to our internal status
            status_mapping = {
                'success': 'completed',
                'pending': 'pending',
                'failed': 'failed',
                'cancelled': 'cancelled'
            }
            
            return status_mapping.get(chapa_status, 'pending')
        
        return 'failed'


class ChapaAPIException(Exception):
    """Custom exception for Chapa API errors."""
    pass


# Convenience function for getting service instance
def get_chapa_service() -> ChapaPaymentService:
    """Get Chapa service instance."""
    return ChapaPaymentService()
