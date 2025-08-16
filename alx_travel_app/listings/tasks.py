#!/usr/bin/env python3
"""
Celery tasks for the listings app.

This module contains background tasks for email notifications and other
asynchronous operations related to bookings and payments.
"""

import logging
from typing import Dict, Any

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

from .models import Payment, Booking

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_payment_confirmation_email(self, payment_id: str):
    """
    Send payment confirmation email to customer.
    
    Args:
        payment_id: UUID of the payment record
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        booking = payment.booking
        
        # Prepare email context
        context = {
            'payment': payment,
            'booking': booking,
            'listing': booking.listing,
            'customer_name': payment.customer_name,
            'total_nights': (booking.check_out - booking.check_in).days,
            'confirmation_date': timezone.now(),
        }
        
        # Prepare email content
        subject = f"Payment Confirmation - Booking #{booking.id}"
        
        # Plain text email content
        message = f"""
Dear {payment.customer_name},

Thank you for your payment! Your booking has been confirmed.

Booking Details:
- Property: {booking.listing.title}
- Address: {booking.listing.address}
- Check-in: {booking.check_in}
- Check-out: {booking.check_out}
- Guests: {booking.guests}
- Total Amount Paid: {payment.amount} {payment.currency}

Payment Details:
- Payment ID: {payment.id}
- Reference: {payment.chapa_reference}
- Payment Method: {payment.payment_method or 'N/A'}
- Paid At: {payment.paid_at}

We look forward to hosting you!

Best regards,
ALX Travel Team
"""
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.customer_email],
            fail_silently=False,
        )
        
        logger.info(f"Payment confirmation email sent successfully for payment {payment_id}")
        return {'status': 'success', 'payment_id': payment_id}
        
    except Payment.DoesNotExist:
        logger.error(f"Payment {payment_id} not found for email confirmation")
        return {'status': 'error', 'message': 'Payment not found'}
        
    except Exception as e:
        logger.error(f"Failed to send payment confirmation email for {payment_id}: {str(e)}")
        
        # Retry the task with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries
            logger.info(f"Retrying email send in {countdown} seconds (attempt {self.request.retries + 1})")
            raise self.retry(countdown=countdown)
        
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True, max_retries=3)
def send_booking_reminder_email(self, booking_id: int, days_before: int = 1):
    """
    Send booking reminder email to customer.
    
    Args:
        booking_id: ID of the booking
        days_before: Number of days before check-in to send reminder
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if booking has a completed payment
        if not hasattr(booking, 'payment') or booking.payment.status != 'completed':
            logger.warning(f"Booking {booking_id} does not have completed payment, skipping reminder")
            return {'status': 'skipped', 'message': 'No completed payment found'}
        
        payment = booking.payment
        
        # Prepare email context
        context = {
            'booking': booking,
            'listing': booking.listing,
            'payment': payment,
            'customer_name': payment.customer_name,
            'days_before': days_before,
            'check_in_date': booking.check_in,
        }
        
        # Prepare email content
        subject = f"Booking Reminder - Check-in in {days_before} day{'s' if days_before != 1 else ''}"
        
        message = f"""
Dear {payment.customer_name},

This is a friendly reminder about your upcoming stay!

Booking Details:
- Property: {booking.listing.title}
- Address: {booking.listing.address}
- Check-in: {booking.check_in}
- Check-out: {booking.check_out}
- Guests: {booking.guests}

Your check-in is in {days_before} day{'s' if days_before != 1 else ''}. We're excited to host you!

If you have any questions, please don't hesitate to contact us.

Safe travels,
ALX Travel Team
"""
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.customer_email],
            fail_silently=False,
        )
        
        logger.info(f"Booking reminder email sent successfully for booking {booking_id}")
        return {'status': 'success', 'booking_id': booking_id}
        
    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} not found for reminder email")
        return {'status': 'error', 'message': 'Booking not found'}
        
    except Exception as e:
        logger.error(f"Failed to send booking reminder email for {booking_id}: {str(e)}")
        
        # Retry the task with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries
            logger.info(f"Retrying reminder email send in {countdown} seconds (attempt {self.request.retries + 1})")
            raise self.retry(countdown=countdown)
        
        return {'status': 'error', 'message': str(e)}


@shared_task
def send_payment_failure_notification(payment_id: str, failure_reason: str = None):
    """
    Send payment failure notification to customer.
    
    Args:
        payment_id: UUID of the failed payment
        failure_reason: Reason for payment failure
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        booking = payment.booking
        
        # Prepare email content
        subject = f"Payment Failed - Booking #{booking.id}"
        
        message = f"""
Dear {payment.customer_name},

We're sorry to inform you that your payment for the following booking could not be processed:

Booking Details:
- Property: {booking.listing.title}
- Check-in: {booking.check_in}
- Check-out: {booking.check_out}
- Amount: {payment.amount} {payment.currency}

Reason: {failure_reason or 'Payment processing failed'}

Please try again or contact our support team if you need assistance.

Best regards,
ALX Travel Team
"""
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.customer_email],
            fail_silently=False,
        )
        
        logger.info(f"Payment failure notification sent for payment {payment_id}")
        return {'status': 'success', 'payment_id': payment_id}
        
    except Exception as e:
        logger.error(f"Failed to send payment failure notification for {payment_id}: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_expired_payments():
    """
    Clean up expired pending payments (older than 24 hours).
    """
    from datetime import timedelta
    
    try:
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        expired_payments = Payment.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )
        
        count = expired_payments.count()
        
        if count > 0:
            expired_payments.update(
                status='cancelled',
                failure_reason='Payment expired after 24 hours'
            )
            
            logger.info(f"Cleaned up {count} expired payments")
        
        return {'status': 'success', 'cleaned_up': count}
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired payments: {str(e)}")
        return {'status': 'error', 'message': str(e)}
