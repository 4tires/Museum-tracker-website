from datetime import datetime, date, timezone
from decimal import Decimal
from flask_login import UserMixin
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, CheckConstraint, Numeric, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
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
    name: Mapped[str] = mapped_column(String(200))
    # slug: Mapped[str] = mapped_column(String(220))
    country: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(String(254))
    image_url: Mapped[Optional[str]] = mapped_column(String(254))
    address: Mapped[str] = mapped_column(String(254))
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("name", "city", name="uq_museum"),
    )

    # Relationships
    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="museum", cascade="all, delete-orphan"
    )
    exhibitions: Mapped[list["Exhibition"]] = relationship(
        back_populates="museum", cascade="all, delete-orphan"
    )

class Exhibition(db.Model):
    __tablename__ = "exhibitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    museum_id: Mapped[int] = mapped_column(ForeignKey("museum.id"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(String(254))
    is_permanent: Mapped[bool] = mapped_column(default=False)
    start_date: Mapped[Optional[date]]
    end_date: Mapped[Optional[date]]

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR start_date <= end_date",
            name="ck_exhibition_date_range",
        ),
        CheckConstraint("NOT is_permanent OR end_date IS NULL", name="ck_permanent_wth_date"),
        UniqueConstraint("museum_id", "name", name="uq_exhibition_museum_name")
    )

    # Relationships
    museum: Mapped["Museum"] = relationship(back_populates="exhibitions")
    tickets: Mapped[list["Ticket"]] = relationship(
        secondary="ticket_exhibition", back_populates="exhibitions"
    )


# Museum tables
class MuseumVisit(db.Model):
    __tablename__ = "museum_visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    museum_id: Mapped[int] = mapped_column(ForeignKey("museum.id"))
    visit_date: Mapped[date] = mapped_column()

    # Unique rows with [user, museum]
    __table_args__ = (
        UniqueConstraint("user_id", "museum_id", "visit_date", name="uq_user_museum_visit"),
    )

    # Relationships
    user: Mapped["User"] = relationship(backref="museum_visits")
    museum: Mapped["Museum"] = relationship(backref="museum_visits")

class MuseumWishlist(db.Model):
    __tablename__ = "museum_wishlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    museum_id: Mapped[int] = mapped_column(ForeignKey("museum.id"))

    # Unique rows with [user, museum]
    __table_args__ = (
        UniqueConstraint("user_id", "museum_id", name="uq_user_museum_wish"),
    )

    # Relationships
    user: Mapped["User"] = relationship(backref="museum_wishlist")
    museum: Mapped["Museum"] = relationship(backref="museum_wishlist")

class MuseumReview(db.Model):
    __tablename__ = "museum_reviews"

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
    user: Mapped["User"] = relationship(backref="museum_reviews")
    museum: Mapped["Museum"] = relationship(backref="museum_reviews")

# Exhibition tables
class ExhibitionVisit(db.Model):
    __tablename__ = "exhibition_visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    exhibition_id: Mapped[int] = mapped_column(ForeignKey("exhibition.id"))
    visit_date: Mapped[date] = mapped_column()

    # Unique rows with [user, exhibition]
    __table_args__ = (
        UniqueConstraint("user_id", "exhibition_id", "visit_date", name="uq_user_exhibition_visit"),
    )

    # Relationships
    user: Mapped["User"] = relationship(backref="exhibition_visits")
    exhibition: Mapped["Exhibition"] = relationship(backref="exhibition_visits")

class ExhibitionWishlist(db.Model):
    __tablename__ = "exhibition_wishlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    exhibition_id: Mapped[int] = mapped_column(ForeignKey("exhibition.id"))

    # Unique rows with [user, exhibition]
    __table_args__ = (
        UniqueConstraint("user_id", "exhibition_id", name="uq_user_exhibition_wish"),
    )

    # Relationships
    user: Mapped["User"] = relationship(backref="exhibition_wishlist")
    exhibition: Mapped["Exhibition"] = relationship(backref="exhibition_wishlist")

class ExhibitionReview(db.Model):
    __tablename__ = "exhibition_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    exhibition_id: Mapped[int] = mapped_column(ForeignKey("exhibition.id"))
    rating: Mapped[Optional[int]] = mapped_column(default=None)
    review: Mapped[Optional[str]] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Unique rows with [user, exhibition] and rating check
    __table_args__ = (
        UniqueConstraint("user_id", "exhibition_id", name="uq_user_exhibition_review"),
        CheckConstraint("rating BETWEEN 1 AND 10", name="ck_review_rating_range"),
    )

    # Relationships
    user: Mapped["User"] = relationship(backref="exhibition_reviews")
    exhibition: Mapped["Exhibition"] = relationship(backref="exhibition_reviews")

class MuseumPass(db.Model):
    __tablename__ = "passes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True) # Include period in the name (e.g. "24h", "48h", "72h", "Year")
    website: Mapped[Optional[str]] = mapped_column(String(254))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    prices: Mapped[list["PassPrice"]] = relationship(
        back_populates="museum_pass", passive_deletes="True"
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="passes", passive_deletes="all"
    )

    # Repr
    def __repr__(self) -> str:
        return f"Pass(id={self.id!r}, name={self.name!r})"

# Share conditions between class Ticket and class Pass Price
class AudienceConditionsMixin:
    resident_country: Mapped[Optional[str]] = mapped_column(String(2))
    resident_municipality: Mapped[Optional[str]] = mapped_column(String(100))
    min_age: Mapped[Optional[int]]
    max_age: Mapped[Optional[int]]

class PassPrice(AudienceConditionsMixin, db.Model):
    __tablename__ = "pass_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    pass_id: Mapped[int] = mapped_column(ForeignKey("passes.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(100))  # "Adult", "Child 5-12", ...
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    notes: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_pass_price_nonneg"),
        CheckConstraint(
            "min_age IS NULL OR max_age IS NULL OR min_age <= max_age",
            name="ck_pass_price_age_range",
        ),
        CheckConstraint("min_age IS NULL OR min_age >= 0", name="ck_min_age")
    )

    museum_pass: Mapped["MuseumPass"] = relationship(back_populates="prices")

class Ticket(AudienceConditionsMixin, db.Model):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    museum_id: Mapped[int] = mapped_column(ForeignKey("museum.id"))
    label: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    pass_id: Mapped[Optional[int]] = mapped_column(ForeignKey("passes.id", ondelete="RESTRICT"))

    # Constraints
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_ticket_price_nonneg"),
        CheckConstraint(
            "min_age IS NULL OR max_age IS NULL OR min_age <= max_age",
            name="ck_ticket_age_range",
        ),
        CheckConstraint("min_age IS NULL OR min_age >= 0", name="ck_min_age")
    )

    # Relationships
    museum: Mapped["Museum"] = relationship(back_populates="tickets")
    museum_pass: Mapped[Optional["MuseumPass"]] = relationship(back_populates="tickets")
    exhibitions: Mapped[list["Exhibition"]] = relationship(
        secondary="ticket_exhibition", back_populates="tickets"
    )

# Middle table: which exhibitions a ticket gives access to.
ticket_exhibition = Table(
    "ticket_exhibition",
    db.metadata,
    Column("ticket_id", ForeignKey("tickets.id"), primary_key=True),
    Column("exhibition_id", ForeignKey("exhibitions.id"), primary_key=True),
)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))