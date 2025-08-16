#!/usr/bin/env python3
"""Models for listings app."""

import uuid
from django.db import models
from django.contrib.auth.models import User

class Listing(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.CharField(max_length=255)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Booking(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking for {self.listing.title} by {self.user.username}"
    
    def calculate_total_amount(self):
        """Calculate total amount based on nights and price per night."""
        if self.check_in and self.check_out:
            nights = (self.check_out - self.check_in).days
            return self.listing.price_per_night * nights
        return 0
    
    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.calculate_total_amount()
        super().save(*args, **kwargs)

class Review(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('listing', 'user')

    def __str__(self):
        return f"Review by {self.user.username} for {self.listing.title}"


class Payment(models.Model):
    """Model to track payment transactions for bookings."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Core payment fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ETB')  # Ethiopian Birr for Chapa
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Chapa-specific fields
    chapa_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    chapa_checkout_url = models.URLField(blank=True, null=True)
    chapa_reference = models.CharField(max_length=255, unique=True, blank=True)
    
    # Additional payment metadata
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    failure_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    # Customer info for Chapa
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_name = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - {self.status} ({self.amount} {self.currency})"
    
    def save(self, *args, **kwargs):
        # Generate a unique reference if not provided
        if not self.chapa_reference:
            self.chapa_reference = f"TRV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
