# alx_travel_app_0x00

## Models

- **Listing**: Contains fields such as title, description, price_per_night, address, and host.
- **Booking**: Links a user to a listing with check-in/check-out dates and number of guests.
- **Review**: User reviews for listings, with a rating and a comment.

## Seeding

To seed the database with sample data:

```sh
python manage.py seed
