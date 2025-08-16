#!/usr/bin/env python3
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from listings.models import Listing
import random

class Command(BaseCommand):
    help = 'Seed the database with sample listings'

    def handle(self, *args, **kwargs):
        # Create some users
        for i in range(3):
            User.objects.get_or_create(username=f'user{i}', defaults={'password': 'password123'})
        
        users = User.objects.all()
        # Create listings
        for i in range(10):
            Listing.objects.create(
                title=f"Listing {i+1}",
                description="A sample description.",
                price_per_night=random.randint(50, 300),
                address=f"{random.randint(1, 999)} Main St",
                host=random.choice(users)
            )
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
