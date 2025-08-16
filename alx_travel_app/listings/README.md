# ALX Travel App 0x02

## 🧭 Overview
This project demonstrates database modeling, API serialization, and data seeding in Django.  
It is part of the "Database Modeling and Data Seeding in Django" task for the ALX program.  
The app focuses on listing travel accommodations, bookings, and reviews—exposing them via serializers and prepopulating the database with a custom seed command.

---

## ✨ Features

### 📦 Django Models
- **Listing**: Represents an accommodation or property.
- **Booking**: Represents a reservation for a listing.
- **Review**: Represents user feedback for a listing.

### 🔗 Serializers
- **ListingSerializer**: Converts `Listing` model to and from JSON.
- **BookingSerializer**: Converts `Booking` model to and from JSON.

These serializers enable REST API endpoints for external interaction.

### 🌱 Data Seeder
Custom management command to generate sample listings, bookings, and reviews for development/testing.

> Run with:
```bash
python manage.py seed
```

## 🧩 Models

### Listing
- id: Auto-incrementing primary key
- name: Name of the property/listing
- location: Location/address
- price_per_night: Decimal price
- description: Optional description

### Booking
- id: Auto-incrementing primary key
- listing: ForeignKey to Listing
- user: Name or identifier of the person booking
- check_in: Date
- check_out: Date

### Review
- id: Auto-incrementing primary key
- listing: ForeignKey to Listing
- user: Name or identifier of reviewer
- rating: Integer
- comment: Text review

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- Django 3.2+
(Recommend using a virtual environment)

### Setup
```bash
# Install dependencies
pip install django

# (Optional: create and activate a virtual environment)

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Seed the database
python manage.py seed

# Start the development server
python manage.py runserver
```

## 🤝 Contributing
Pull requests are welcome!
For major changes, please open an issue first to discuss what you'd like to improve.

## 📄 License
This project is licensed for ALX learning purposes.

## ✍️ Author
Jacob N. / ALX Student
