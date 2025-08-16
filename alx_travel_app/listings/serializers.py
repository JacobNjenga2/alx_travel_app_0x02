#!/usr/bin/env python3
"""Serializers for listings app."""

from rest_framework import serializers
from .models import Listing, Booking, Review, Payment

class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('id', 'chapa_transaction_id', 'chapa_checkout_url', 
                           'chapa_reference', 'created_at', 'updated_at', 'paid_at')


class PaymentInitiationSerializer(serializers.Serializer):
    """Serializer for payment initiation request."""
    
    booking_id = serializers.IntegerField()
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=20, required=False)
    customer_name = serializers.CharField(max_length=100)
    return_url = serializers.URLField(required=False)
    webhook_url = serializers.URLField(required=False)


class PaymentVerificationSerializer(serializers.Serializer):
    """Serializer for payment verification request."""
    
    transaction_id = serializers.CharField(max_length=255)


class PaymentStatusSerializer(serializers.ModelSerializer):
    """Serializer for payment status response."""
    
    booking_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = ('id', 'status', 'amount', 'currency', 'chapa_reference',
                 'payment_method', 'created_at', 'updated_at', 'paid_at',
                 'booking_details')
    
    def get_booking_details(self, obj):
        return {
            'booking_id': obj.booking.id,
            'listing_title': obj.booking.listing.title,
            'check_in': obj.booking.check_in,
            'check_out': obj.booking.check_out,
            'guests': obj.booking.guests
        }
