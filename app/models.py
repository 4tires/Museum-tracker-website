from datetime import datetime, date, timezone
from flask_login import UserMixin
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r})"

class Museum(db.Model):
    __tablename__ = "museum"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    # slug: Mapped[str] = mapped_column(String(30))
    country: Mapped[str] = mapped_column(String(30))
    city: Mapped[str] = mapped_column(String(30))
    description: Mapped[Optional[str]] = mapped_column(String(500))
    website: Mapped[Optional[str]] = mapped_column(String(254))
    image_url: Mapped[Optional[str]] = mapped_column(String(254))
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

class Visit(db.Model):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    museum_id: Mapped[int] = mapped_column(ForeignKey("museum.id"))
    visit_date: Mapped[date] = mapped_column()

    # Unique rows with [user, museum]
    __table_args__ = (
        UniqueConstraint("user_id", "museum_id", "visit_date", name="uq_user_museum_visit"),
    )

    # Relationships
    user: Mapped["User"] = relationship(backref="visits")
    museum: Mapped["Museum"] = relationship(backref="visits")

class Wishlist(db.Model):
    __tablename__ = "wishlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    museum_id: Mapped[int] = mapped_column(ForeignKey("museum.id"))

    # Unique rows with [user, museum]
    __table_args__ = (
        UniqueConstraint("user_id", "museum_id", name="uq_user_museum_wish"),
    )

    # Relationships
    user: Mapped["User"] = relationship(backref="wishlist")
    museum: Mapped["Museum"] = relationship(backref="wishlist")

class Review(db.Model):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    museum_id: Mapped[int] = mapped_column(ForeignKey("museum.id"))
    rating: Mapped[Optional[int]] = mapped_column(default=None)
    review: Mapped[Optional[str]] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Unique rows with [user, museum] and rating check
    __table_args__ = (
        UniqueConstraint("user_id", "museum_id", name="uq_user_museum_review"),
        CheckConstraint("rating BETWEEN 1 AND 10", name="ck_review_rating_range"),
    )

    # Relationships
    user: Mapped["User"] = relationship(backref="reviews")
    museum: Mapped["Museum"] = relationship(backref="reviews")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))