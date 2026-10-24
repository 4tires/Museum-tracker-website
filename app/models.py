from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, CheckConstraint, Numeric, Table, Column, Enum, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin

from .extensions import db, login_manager

from datetime import datetime, date, timezone, time
from decimal import Decimal
from typing import Optional
import enum

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

    opening_hours: Mapped[list["OpeningHours"]] = relationship(
        back_populates="museum", cascade="all, delete-orphan"
    )

class Exhibition(db.Model):
    __tablename__ = "exhibition"

    id: Mapped[int] = mapped_column(primary_key=True)
    museum_id: Mapped[int] = mapped_column(ForeignKey("museum.id"))
    name: Mapped[str] = mapped_column(String(200))
    short_description: Mapped[Optional[str]] = mapped_column(Text)
    long_description: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(String(254))
    image_url: Mapped[Optional[str]] = mapped_column(String(254))
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
        CheckConstraint("rating BETWEEN 1 AND 10", name="ck_museum_review_rating_range"),
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
        CheckConstraint("rating BETWEEN 1 AND 10", name="ck_exhibition_review_rating_range"),
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
        back_populates="museum_pass", passive_deletes=True
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="museum_pass", passive_deletes="all"
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
    is_student: Mapped[bool] = mapped_column(default=False)

class DurationUnit(enum.Enum):
    hours = "hours"
    days = "days"
    months = "months"
    years = "years"

class PassPrice(AudienceConditionsMixin, db.Model):
    __tablename__ = "pass_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    pass_id: Mapped[int] = mapped_column(ForeignKey("passes.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(100))  # "Adult", "Child 5-12", ...
    duration_unit: Mapped[DurationUnit] = mapped_column(
        Enum(DurationUnit, native_enum=False, create_constraint=True, name="duration_unit")
    )
    duration_value: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    notes: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_pass_price_nonneg"),
        CheckConstraint(
            "min_age IS NULL OR max_age IS NULL OR min_age <= max_age",
            name="ck_pass_price_age_range",
        ),
        CheckConstraint("min_age IS NULL OR min_age >= 0", name="ck_pass_price_min_age"),
        CheckConstraint("duration_value > 0", name="ck_pass_price_duration_positive"),
        UniqueConstraint("pass_id", "label", "duration_value", "duration_unit", name="uq_pass_price_label"),
    )

    museum_pass: Mapped["MuseumPass"] = relationship(back_populates="prices")

class Weekday(enum.IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

class ScheduleConditionsMixin:
    # Free type of rules
    ## Free on day of the week
    weekday: Mapped[Optional[int]] = mapped_column(Integer)
    start_time: Mapped[Optional[time]] = mapped_column(Time)
    end_time: Mapped[Optional[time]] = mapped_column(Time)
    ## Free on the Nth weekday of the month (1-5), or the last one (-1)
    week_of_month: Mapped[Optional[int]]

    ## Free on annual date
    month: Mapped[Optional[int]]
    day: Mapped[Optional[int]]

    ## Free on holidays
    holidays: Mapped[bool] = mapped_column(default=False)

    # Recurring month range where the rule is valid
    month_from: Mapped[Optional[int]]
    month_to: Mapped[Optional[int]]

class Ticket(AudienceConditionsMixin, ScheduleConditionsMixin, db.Model):
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
        UniqueConstraint("museum_id", "label", name="uq_ticket_museum_label"),
        CheckConstraint("price >= 0", name="ck_ticket_price_nonneg"),
        CheckConstraint(
            "min_age IS NULL OR max_age IS NULL OR min_age <= max_age",
            name="ck_ticket_age_range",
        ),
        CheckConstraint("min_age IS NULL OR min_age >= 0", name="ck_ticket_min_age"),
        CheckConstraint(
            "(weekday IS NULL AND month IS NULL AND day IS NULL AND NOT holidays) "
            "OR (weekday IS NOT NULL AND month IS NULL AND day IS NULL AND NOT holidays) "
            "OR (weekday IS NULL AND month IS NOT NULL AND day IS NOT NULL AND NOT holidays) "
            "OR (weekday IS NULL AND month IS NULL AND day IS NULL AND holidays)",
            name="ck_ticket_schedule_kind",
        ),
        CheckConstraint(
            "week_of_month IS NULL OR (weekday IS NOT NULL "
            "AND (week_of_month = -1 OR week_of_month BETWEEN 1 AND 5))",
            name="ck_ticket_week_of_month",
        ),
        CheckConstraint("weekday IS NULL OR weekday BETWEEN 0 AND 6", name="ck_free_rule_weekday"),
        CheckConstraint("month IS NULL OR month BETWEEN 1 AND 12", name="ck_free_rule_month"),
        CheckConstraint("day IS NULL OR day BETWEEN 1 AND 31", name="ck_free_rule_day"),
        CheckConstraint(
            "start_time IS NULL OR end_time IS NULL OR start_time < end_time",
            name="ck_ticket_time_range",
        ),
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
    Column("exhibition_id", ForeignKey("exhibition.id"), primary_key=True),
)

class OpeningHours(ScheduleConditionsMixin, db.Model):
    __tablename__ = "opening_hours"

    id: Mapped[int] = mapped_column(primary_key=True)
    museum_id: Mapped[int] = mapped_column(ForeignKey("museum.id", ondelete="CASCADE"))
    # start_time / end_time (from the mixin) are the opening and closing times
    last_entry: Mapped[Optional[time]] = mapped_column(Time)

    is_closed: Mapped[bool] = mapped_column(default=False)
    is_special: Mapped[bool] = mapped_column(default=False)   # overrides regular hours
    label: Mapped[Optional[str]] = mapped_column(String(100)) # "Thursday Late"
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # One-off validity window (e.g. a summer schedule for 2027 only)
    valid_from: Mapped[Optional[date]]
    valid_to: Mapped[Optional[date]]

    __table_args__ = (
        CheckConstraint(
            "(is_closed AND start_time IS NULL AND end_time IS NULL AND last_entry IS NULL) "
            "OR (NOT is_closed AND start_time IS NOT NULL AND end_time IS NOT NULL)",
            name="ck_hours_closed_or_times",
        ),
        CheckConstraint("start_time < end_time", name="ck_hours_time_range"),
        CheckConstraint("weekday IS NULL OR weekday BETWEEN 0 AND 6", name="ck_hours_weekday"),
        CheckConstraint(
            "week_of_month IS NULL OR (weekday IS NOT NULL "
            "AND (week_of_month = -1 OR week_of_month BETWEEN 1 AND 5))",
            name="ck_hours_week_of_month",
        ),
        CheckConstraint("month IS NULL OR month BETWEEN 1 AND 12", name="ck_hours_month"),
        CheckConstraint("day IS NULL OR day BETWEEN 1 AND 31", name="ck_hours_day"),
        CheckConstraint("(month IS NULL) = (day IS NULL)", name="ck_hours_month_day_pair"),
        CheckConstraint(
            "(month_from IS NULL AND month_to IS NULL) "
            "OR (month_from BETWEEN 1 AND 12 AND month_to BETWEEN 1 AND 12 "
            "AND month_from <= month_to)",
            name="ck_hours_month_range",
        ),
        CheckConstraint(
            "NOT holidays OR (weekday IS NULL AND month IS NULL AND day IS NULL)",
            name="ck_hours_holidays_alone",
        ),
        CheckConstraint(
            "valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to",
            name="ck_hours_valid_range",
        ),
    )

    # Relationships
    museum: Mapped["Museum"] = relationship(back_populates="opening_hours")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))