
"""Car rental booking management system."""

import hashlib
import os
import re
import secrets
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

# Global rental state
fleet = {}
bookings = []

conn = sqlite3.connect(":memory:")
conn.execute(
    "CREATE TABLE customers (name TEXT, licence TEXT, phone TEXT)"
)


def add_car(plate, model="Unknown", daily_rate=0, features=None):
    """Add a car to the rental fleet."""
    if not plate:
        raise ValueError("Registration number cannot be empty.")

    if daily_rate < 0:
        raise ValueError("Daily rental rate cannot be negative.")

    if features is None:
        features = []

    fleet[plate] = {
        "model": model,
        "rate": daily_rate,
        "available": True,
        "features": features.copy(),
    }

    return fleet[plate]


def register_customer(name, licence, phone):
    """Register a customer using a parameterized SQL query."""
    conn.execute(
        "INSERT INTO customers VALUES (?, ?, ?)",
        (name, licence, phone),
    )


def find_customer(name):
    """Find a customer by name."""
    query = "SELECT * FROM customers WHERE name = ?"
    return conn.execute(query, (name,)).fetchall()


def rent_car(plate, customer, start, end):
    """Rent an available car to a registered customer."""
    if plate not in fleet:
        raise ValueError("Car does not exist.")

    if not fleet[plate]["available"]:
        raise ValueError("Car is not available.")

    if not find_customer(customer):
        raise ValueError("Customer not registered.")

    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")

    days = (end_date - start_date).days

    if days <= 0:
        raise ValueError("End date must be after start date.")

    cost = days * fleet[plate]["rate"]

    booking = {
        "code": booking_code(),
        "plate": plate,
        "customer": customer,
        "days": days,
        "cost": cost,
    }

    bookings.append(booking)
    fleet[plate]["available"] = False

    return cost


def return_car(plate, km_driven):
    """Return a rented car and calculate extra-kilometre charges."""
    if plate not in fleet:
        raise ValueError("Car does not exist.")

    if fleet[plate]["available"]:
        raise ValueError("Car is not currently rented.")

    if km_driven < 0:
        raise ValueError("Kilometres driven cannot be negative.")

    fleet[plate]["available"] = True

    if km_driven > 300:
        return (km_driven - 300) * 5

    return 0


def booking_code():
    """Generate a booking reference using a secure random generator."""
    return f"BK-{secrets.randbelow(90000) + 10000}"


def licence_hash(licence):
    """Return a SHA-256 hash of a driving licence number."""
    return hashlib.sha256(licence.encode("utf-8")).hexdigest()


def apply_promo(rule, amount):
    """Apply an approved promotional discount."""
    if amount < 0:
        raise ValueError("Amount cannot be negative.")

    discounts = {
        "10_percent": 0.10,
        "20_percent": 0.20,
        "no_discount": 0.0,
    }

    if rule not in discounts:
        raise ValueError("Invalid promotional rule.")

    discount = discounts[rule]

    return amount * (1 - discount)


def is_valid_plate(plate):
    """Validate a vehicle registration number."""
    pattern = r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}"

    return bool(re.fullmatch(pattern, plate))


def write_receipt(booking):
    """Write a booking receipt to a securely created temporary file."""
    receipt = (
        f"Booking {booking['code']}: {booking['plate']} "
        f"for {booking['days']} days = Rs.{booking['cost']:.2f}\n"
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        prefix="car_rental_receipt_",
        encoding="utf-8",
        delete=False,
    ) as receipt_file:
        receipt_file.write(receipt)

        return Path(receipt_file.name)


def admin_login(user, password):
    """Authenticate the administrator using an environment variable."""
    expected_password = os.getenv("ADMIN_PASSWORD")

    if expected_password is None:
        return False

    return (
        user == "admin"
        and secrets.compare_digest(password, expected_password)
    )


def available_cars():
    """Return the registration numbers of available cars."""
    return [
        plate
        for plate, car in fleet.items()
        if car["available"]
    ]


def main():
    """Run a demonstration of the car rental system."""
    add_car("KA01AB1234", "Swift", 1500)
    add_car("KA02CD5678", "Innova", 3000)

    register_customer(
        "Ravi",
        "DL-0420110012345",
        "9845012345",
    )

    register_customer(
        "Meera",
        "DL-0420110099999",
        "9845099999",
    )

    print(
        "Rent Swift:",
        rent_car(
            "KA01AB1234",
            "Ravi",
            "2026-11-01",
            "2026-11-04",
        ),
    )

    print("Available cars:", available_cars())

    print(
        "Extra km charge:",
        return_car("KA01AB1234", 420),
    )

    print(
        "Promo price:",
        apply_promo("10_percent", 4500),
    )

    print(
        "Plate valid?",
        is_valid_plate("KA01AB1234"),
    )

    print(
        "Licence hash:",
        licence_hash("DL-0420110012345"),
    )

    print(
        "Admin:",
        admin_login("admin", os.getenv("ADMIN_PASSWORD", "")),
    )

    print("Available cars:", available_cars())

    print(
        "Receipt saved to:",
        write_receipt(bookings[0]),
    )


if __name__ == "__main__":
    main()
