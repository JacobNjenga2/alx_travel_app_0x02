import logging
from datetime import datetime
from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Listing, Booking, Payment
from .serializers import (
    ListingSerializer, BookingSerializer, PaymentSerializer,
    PaymentInitiationSerializer, PaymentVerificationSerializer,
    PaymentStatusSerializer
)
from .chapa_service import get_chapa_service, ChapaAPIException
from .tasks import send_payment_confirmation_email, send_payment_failure_notification

logger = logging.getLogger(__name__)

class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing listings.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing bookings.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


# Payment API Endpoints

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """
    Initiate payment for a booking.
    
    This endpoint creates a payment record and initiates the payment process
    with Chapa payment gateway.
    """
    serializer = PaymentInitiationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid payment data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        # Get the booking
        booking = get_object_or_404(Booking, id=data['booking_id'])
        
        # Check if payment already exists for this booking
        if hasattr(booking, 'payment'):
            if booking.payment.status in ['completed', 'processing']:
                return Response({
                    'success': False,
                    'error': 'Payment already exists for this booking',
                    'payment_status': booking.payment.status
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Delete existing failed/cancelled payment
                booking.payment.delete()
        
        # Calculate payment amount
        amount = booking.total_amount or booking.calculate_total_amount()
        
        # Create payment record
        payment = Payment.objects.create(
            booking=booking,
            amount=amount,
            currency='ETB',
            customer_email=data['customer_email'],
            customer_phone=data.get('customer_phone', ''),
            customer_name=data['customer_name'],
            status='pending'
        )
        
        # Prepare payment data for Chapa
        payment_data = {
            'amount': float(amount),
            'currency': 'ETB',
            'customer_email': data['customer_email'],
            'customer_phone': data.get('customer_phone', ''),
            'customer_name': data['customer_name'],
            'reference': payment.chapa_reference,
            'booking_id': booking.id,
            'return_url': data.get('return_url', ''),
            'callback_url': data.get('webhook_url', '')
        }
        
        # Initiate payment with Chapa
        chapa_service = get_chapa_service()
        chapa_response = chapa_service.initiate_payment(payment_data)
        
        if chapa_response['success']:
            # Update payment with Chapa response
            payment.chapa_checkout_url = chapa_response['checkout_url']
            payment.chapa_transaction_id = chapa_response['transaction_id']
            payment.status = 'processing'
            payment.save()
            
            logger.info(f"Payment initiated successfully for booking {booking.id}")
            
            return Response({
                'success': True,
                'message': 'Payment initiated successfully',
                'payment_id': str(payment.id),
                'checkout_url': chapa_response['checkout_url'],
                'reference': payment.chapa_reference,
                'amount': amount,
                'currency': 'ETB'
            }, status=status.HTTP_201_CREATED)
        
        else:
            # Payment initiation failed
            payment.status = 'failed'
            payment.failure_reason = chapa_response.get('error', 'Payment initiation failed')
            payment.save()
            
            logger.error(f"Payment initiation failed for booking {booking.id}: {chapa_response.get('error')}")
            
            return Response({
                'success': False,
                'error': 'Payment initiation failed',
                'details': chapa_response.get('error', 'Unknown error')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """
    Verify payment status with Chapa.
    
    This endpoint verifies the payment status and updates the payment record.
    """
    serializer = PaymentVerificationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid verification data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    transaction_id = serializer.validated_data['transaction_id']
    
    try:
        # Find payment by transaction ID
        payment = get_object_or_404(
            Payment, 
            chapa_transaction_id=transaction_id
        )
        
        # Verify with Chapa
        chapa_service = get_chapa_service()
        verification_result = chapa_service.verify_payment(transaction_id)
        
        if verification_result['success']:
            # Update payment status based on Chapa response
            chapa_status = verification_result.get('status', '').lower()
            
            if chapa_status == 'success':
                payment.status = 'completed'
                payment.paid_at = timezone.now()
                payment.payment_method = verification_result.get('payment_method', '')
                
                # Trigger email notification
                send_payment_confirmation_email.delay(str(payment.id))
                
                logger.info(f"Payment {payment.id} completed successfully")
                
            elif chapa_status in ['failed', 'cancelled']:
                payment.status = 'failed'
                payment.failure_reason = f"Chapa status: {chapa_status}"
                
                # Send failure notification
                send_payment_failure_notification.delay(
                    str(payment.id), 
                    payment.failure_reason
                )
                
            else:
                payment.status = 'pending'
            
            payment.save()
            
            # Return payment status
            status_serializer = PaymentStatusSerializer(payment)
            return Response({
                'success': True,
                'message': 'Payment verification completed',
                'payment': status_serializer.data
            }, status=status.HTTP_200_OK)
        
        else:
            logger.error(f"Payment verification failed for {transaction_id}: {verification_result.get('error')}")
            
            return Response({
                'success': False,
                'error': 'Payment verification failed',
                'details': verification_result.get('error', 'Unknown error')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Payment.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Payment not found',
            'details': f'No payment found with transaction ID: {transaction_id}'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request, payment_id):
    """
    Get payment status by payment ID.
    """
    try:
        payment = get_object_or_404(Payment, id=payment_id)
        
        # Optionally verify with Chapa if payment is still pending/processing
        if payment.status in ['pending', 'processing'] and payment.chapa_transaction_id:
            chapa_service = get_chapa_service()
            current_status = chapa_service.get_payment_status(payment.chapa_transaction_id)
            
            if current_status != payment.status:
                payment.status = current_status
                if current_status == 'completed':
                    payment.paid_at = timezone.now()
                payment.save()
        
        serializer = PaymentStatusSerializer(payment)
        return Response({
            'success': True,
            'payment': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Payment status error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Payment not found',
            'details': str(e)
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def payment_webhook(request):
    """
    Webhook endpoint for Chapa payment notifications.
    
    This endpoint receives payment status updates from Chapa.
    """
    try:
        data = request.data
        transaction_id = data.get('tx_ref')
        
        if not transaction_id:
            return Response({
                'success': False,
                'error': 'Missing transaction reference'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find payment
        payment = Payment.objects.filter(chapa_transaction_id=transaction_id).first()
        
        if not payment:
            logger.warning(f"Webhook received for unknown transaction: {transaction_id}")
            return Response({
                'success': False,
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify payment with Chapa to ensure webhook authenticity
        chapa_service = get_chapa_service()
        verification_result = chapa_service.verify_payment(transaction_id)
        
        if verification_result['success']:
            chapa_status = verification_result.get('status', '').lower()
            
            if chapa_status == 'success':
                payment.status = 'completed'
                payment.paid_at = timezone.now()
                payment.payment_method = verification_result.get('payment_method', '')
                
                # Trigger email notification
                send_payment_confirmation_email.delay(str(payment.id))
                
            elif chapa_status in ['failed', 'cancelled']:
                payment.status = 'failed'
                payment.failure_reason = f"Webhook status: {chapa_status}"
                
                # Send failure notification
                send_payment_failure_notification.delay(
                    str(payment.id), 
                    payment.failure_reason
                )
            
            payment.save()
            
            logger.info(f"Webhook processed for payment {payment.id}: {chapa_status}")
            
            return Response({
                'success': True,
                'message': 'Webhook processed successfully'
            }, status=status.HTTP_200_OK)
        
        else:
            logger.error(f"Webhook verification failed for {transaction_id}")
            return Response({
                'success': False,
                'error': 'Webhook verification failed'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Webhook processing failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
