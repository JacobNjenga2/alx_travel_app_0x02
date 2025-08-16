from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ListingViewSet, BookingViewSet,
    initiate_payment, verify_payment, payment_status, payment_webhook
)

router = DefaultRouter()
router.register(r'listings', ListingViewSet)
router.register(r'bookings', BookingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Payment endpoints
    path('payments/initiate/', initiate_payment, name='initiate_payment'),
    path('payments/verify/', verify_payment, name='verify_payment'),
    path('payments/<uuid:payment_id>/status/', payment_status, name='payment_status'),
    path('payments/webhook/', payment_webhook, name='payment_webhook'),
]
