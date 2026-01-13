"""Create a sample SQLite database with product reviews for the example."""

import sqlite3
from pathlib import Path

# Sample product reviews data
SAMPLE_REVIEWS = [
    (
        1,
        "Wireless Headphones",
        5,
        "Amazing sound quality! The noise cancellation is superb and "
        "battery lasts all day. Highly recommend for music lovers.",
    ),
    (
        2,
        "Wireless Headphones",
        2,
        "Disappointed with the build quality. They broke after just 2 "
        "weeks of normal use. Sound is okay but not worth the price.",
    ),
    (
        3,
        "Smart Watch",
        4,
        "Great fitness tracker with accurate heart rate monitoring. "
        "Battery life could be better, but overall very satisfied.",
    ),
    (
        4,
        "Smart Watch",
        5,
        "Best smartwatch I've owned! Seamless integration with my phone, "
        "tons of useful features, and looks professional.",
    ),
    (
        5,
        "Laptop Stand",
        3,
        "Does the job but feels flimsy. The adjustability is limited and "
        "it wobbles a bit. Expected better quality for the price.",
    ),
    (
        6,
        "Laptop Stand",
        5,
        "Perfect for my home office setup! Sturdy construction, multiple "
        "height options, and really helps with posture.",
    ),
    (
        7,
        "USB-C Hub",
        4,
        "Works well with all my devices. All ports function properly and "
        "data transfer is fast. Gets a bit warm during heavy use.",
    ),
    (
        8,
        "USB-C Hub",
        1,
        "Stopped working after a week. One port was DOA and then the whole "
        "hub died. Total waste of money.",
    ),
    (
        9,
        "Mechanical Keyboard",
        5,
        "Typing feels incredible! The switches are responsive and the build "
        "quality is excellent. Worth every penny.",
    ),
    (
        10,
        "Mechanical Keyboard",
        4,
        "Great keyboard for coding. Switches are a bit loud for an office "
        "environment but the tactile feedback is amazing.",
    ),
]


def create_database(db_path: Path | str) -> None:
    """Create SQLite database with sample product reviews.

    Args:
        db_path: Path where the database file should be created
    """
    db_path = Path(db_path)

    # Remove existing database if it exists
    if db_path.exists():
        db_path.unlink()

    # Create database and table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create reviews table
    cursor.execute(
        """
        CREATE TABLE product_reviews (
            review_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Insert sample data
    cursor.executemany(
        """
        INSERT INTO product_reviews
        (review_id, product_name, rating, review_text)
        VALUES (?, ?, ?, ?)
    """,
        SAMPLE_REVIEWS,
    )

    conn.commit()
    conn.close()

    print(f"Created database at {db_path} with {len(SAMPLE_REVIEWS)} reviews")


if __name__ == "__main__":
    # Create database in the data_processing examples directory
    db_path = Path(__file__).parent / "reviews.db"
    create_database(db_path)
