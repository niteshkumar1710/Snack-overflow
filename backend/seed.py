import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.snack import Snack

DEMO_USERS = [
    {
        "name": "Demo Admin",
        "email": "admin@example.com",
        "password": "Admin@123",
        "role": "admin",
    },
    {
        "name": "Demo Member",
        "email": "member@example.com",
        "password": "Member@123",
        "role": "member",
    },
]

SAMPLE_SNACKS = [
    # Sweet
    {
        "name": "Dark Chocolate Almonds",
        "category": "sweet",
        "quantity": 20,
        "low_stock_threshold": 5,
        "image_url": "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "Gummy Bears",
        "category": "sweet",
        "quantity": 2,
        "low_stock_threshold": 5,
        "image_url": "https://images.unsplash.com/photo-1582058091505-f87a2e55a40f?auto=format&fit=crop&w=400&q=80",
    },
    # Savoury
    {
        "name": "Artisan Pretzels",
        "category": "savoury",
        "quantity": 25,
        "low_stock_threshold": 5,
        "image_url": "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "Sea Salt Potato Chips",
        "category": "savoury",
        "quantity": 4,
        "low_stock_threshold": 5,
        "image_url": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "White Cheddar Popcorn",
        "category": "savoury",
        "quantity": 0,
        "low_stock_threshold": 5,
        "image_url": "https://images.unsplash.com/photo-1578849278619-e73505e9610f?auto=format&fit=crop&w=400&q=80",
    },
    # Drink
    {
        "name": "Cold Brew Coffee",
        "category": "drink",
        "quantity": 16,
        "low_stock_threshold": 5,
        "image_url": "https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "Sparkling Lime Water",
        "category": "drink",
        "quantity": 3,
        "low_stock_threshold": 5,
        "image_url": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "Oat Milk Latte",
        "category": "drink",
        "quantity": 0,
        "low_stock_threshold": 5,
        "image_url": "https://images.unsplash.com/photo-1541167760496-1628856ab772?auto=format&fit=crop&w=400&q=80",
    },
    # Healthy-ish
    {
        "name": "Roasted Mixed Nuts",
        "category": "healthy-ish",
        "quantity": 18,
        "low_stock_threshold": 5,
        "image_url": "https://images.unsplash.com/photo-1536591375315-1b836890ba4e?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "Dried Mango Slices",
        "category": "healthy-ish",
        "quantity": 1,
        "low_stock_threshold": 5,
        "image_url": "https://images.unsplash.com/photo-1601493700631-2b16ec4b4716?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "Granola Energy Bars",
        "category": "healthy-ish",
        "quantity": 0,
        "low_stock_threshold": 5,
        "image_url": "https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?auto=format&fit=crop&w=400&q=80",
    },
]


def seed_database(db: Session) -> None:
    """Idempotently seed demo users and sample snacks into the database."""
    print("--- Seeding Demo Users ---")
    for user_data in DEMO_USERS:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing_user:
            user = User(
                name=user_data["name"],
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                role=user_data["role"],
            )
            db.add(user)
            print(f"Created user: {user.email} (Role: {user.role})")
        else:
            # Update password hash and role to guarantee valid credentials
            existing_user.name = user_data["name"]
            existing_user.password_hash = hash_password(user_data["password"])
            existing_user.role = user_data["role"]
            print(f"User already exists, refreshed: {existing_user.email}")

    db.commit()

    print("\n--- Seeding Sample Snacks ---")
    for snack_data in SAMPLE_SNACKS:
        existing_snack = db.query(Snack).filter(Snack.name == snack_data["name"]).first()
        if not existing_snack:
            snack = Snack(
                name=snack_data["name"],
                category=snack_data["category"],
                quantity=snack_data["quantity"],
                low_stock_threshold=snack_data["low_stock_threshold"],
                image_url=snack_data.get("image_url"),
            )
            db.add(snack)
            print(f"Created snack: '{snack.name}' | Qty: {snack.quantity} ({snack.status})")
        else:
            existing_snack.quantity = snack_data["quantity"]
            existing_snack.low_stock_threshold = snack_data["low_stock_threshold"]
            # Only set seed image if snack doesn't already have one
            if not existing_snack.image_url:
                existing_snack.image_url = snack_data.get("image_url")
            print(f"Snack already exists, refreshed: '{existing_snack.name}' | Qty: {existing_snack.quantity}")

    db.commit()
    print("\nDatabase seeding completed successfully!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
