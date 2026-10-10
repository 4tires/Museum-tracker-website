"""Barebones seed script.

Run with:
    python seed.py            # add seed data (skips anything that already exists)
    python seed.py --reset    # drop and recreate all tables first, then seed

Adjust the imports and fields below to match your own app and models.
"""
import sys

# TODO: change these imports to match your project layout
from app import create_app, db
from app.models import User, Museum


def reset_db():
    """Wipe all tables. Fine for early development with SQLite."""
    db.drop_all()
    db.create_all()
    # If you use Flask-Migrate, you may prefer deleting the .db file and
    # running `flask db upgrade` instead of create_all().


def get_or_create(model, defaults=None, **lookup):
    """Return an existing row matching `lookup`, or create it.
    Keeps the script safe to run more than once."""
    instance = db.session.execute(
        db.select(model).filter_by(**lookup)
    ).scalar_one_or_none()
    if instance:
        return instance
    instance = model(**lookup, **(defaults or {}))
    db.session.add(instance)
    return instance


def seed_users():
    # TODO: match your User fields (and hash the password the way your app does)
    admin = get_or_create(
        User,
        username="paulo",
        defaults={"email": "paulo@example.com", "is_admin": True},
    )
    # admin.set_password("change-me")  # if your model has a helper like this
    return {"admin": admin}


def seed_museums():
    # TODO: match your Museum fields
    museums = [
        {"name": "Museum One", "city": "Lisbon", "country": "Portugal"},
        {"name": "Museum Two", "city": "Leiden", "country": "Netherlands"},
    ]
    for data in museums:
        get_or_create(Museum, name=data["name"], defaults=data)


def main():
    app = create_app()
    with app.app_context():
        if "--reset" in sys.argv:
            reset_db()

        seed_users()
        seed_museums()
        # TODO: add seed_reviews() etc. as you add models

        db.session.commit()
        print("Seeding done.")


if __name__ == "__main__":
    main()
