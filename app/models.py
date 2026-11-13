from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, CheckConstraint, Numeric, Table, Column, Enum, Integer, Time, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_security import UserMixin, RoleMixin

from .extensions import db

from datetime import datetime, date, timezone, time
from decimal import Decimal
from typing import Optional
import enum

roles_users = Table(
    "roles_users", db.metadata,
    Column("user_id", ForeignKey("user_account.id"), primary_key=True),
    Column("role_id", ForeignKey("role.id"), primary_key=True),
)

class Role(RoleMixin, db.Model):
    __tablename__ = "role"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    def __repr__(self) -> str:
        return f"Role(id={self.id!r}, name={self.name!r})"
    
    def __str__(self) -> str:
        return f"{self.name}"

class User(UserMixin, db.Model):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    birth_date: Mapped[date]
    is_student: Mapped[bool] = mapped_column(default=False)
    resident_country: Mapped[str] = mapped_column(String(50))
    resident_municipality: Mapped[str] = mapped_column(String(50))

    # Flask Security
    active: Mapped[bool] = mapped_column(default=True)
    fs_uniquifier: Mapped[str] = mapped_column(String(64), unique=True)
    roles: Mapped[list["Role"]] = relationship(secondary=roles_users, backref="users")

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r})"

    def __str__(self) -> str:
        return f"{self.username}"

# Museum tables
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
    notes: Mapped[Optional[str]] = mapped_column(Text)
    address: Mapped[str] = mapped_column(String(254))
    has_lockers: Mapped[Optional[bool]]          # None = unknown, False = confirmed no
    locker_notes: Mapped[Optional[str]]          # size limits, coin/deposit, large luggage
    payment_notes: Mapped[Optional[str]] = mapped_column(Text)   # exceptions, e.g. "Card only above €5"

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
    
    audioguides: Mapped[list["Audioguide"]] = relationship(
        back_populates="museum", cascade="all, delete-orphan"
    )
    guided_visits: Mapped[list["GuidedVisit"]] = relationship(
        back_populates="museum", cascade="all, delete-orphan"
    )
    # Languages of the museum's display texts (uses the museum_language table below)
    languages: Mapped[list["Language"]] = relationship(secondary="museum_language")

    payment_methods: Mapped[list["PaymentMethod"]] = relationship(
        secondary="museum_payment_method", back_populates="museums"
    )

    def __repr__(self) -> str:
        return f"Museum(id={self.id!r}, name={self.name!r}, city={self.city!r})"

    def __str__(self) -> str:
        return f"{self.name} ({self.city})"

class PaymentMethod(db.Model):
    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)   # "cash", "mbway"
    name: Mapped[str] = mapped_column(String(50))                # "MB Way"

    museums: Mapped[list["Museum"]] = relationship(
        secondary="museum_payment_method", back_populates="payment_methods"
    )

    def __repr__(self) -> str:
        return f"PaymentMethod(id={self.id!r}, code={self.code!r})"

    def __str__(self) -> str:
        return self.name

museum_payment_method = Table(
    "museum_payment_method",
    db.metadata,
    Column("museum_id", ForeignKey("museum.id", ondelete="CASCADE"), primary_key=True),
    Column("payment_method_id", ForeignKey("payment_methods.id", ondelete="CASCADE"), primary_key=True),
)

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

    def __repr__(self) -> str:
        return f"MuseumVisit(id={self.id!r}, user_id={self.user_id!r}, museum_id={self.museum_id!r}, visit_date={self.visit_date!r})"

    def __str__(self) -> str:
        return f"{self.user} - {self.museum} ({self.visit_date})"

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

    def __repr__(self) -> str:
        return f"MuseumWishlist(id={self.id!r}, user_id={self.user_id!r}, museum_id={self.museum_id!r})"

    def __str__(self) -> str:
        return f"{self.user} - {self.museum}"

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

    def __repr__(self) -> str:
        return f"MuseumReview(id={self.id!r}, user_id={self.user_id!r}, museum_id={self.museum_id!r})"

    def __str__(self) -> str:
        rating_str = f" ({self.rating}/10)" if self.rating else ""
        return f"{self.user} - {self.museum}{rating_str}"

# Exhibition tables
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
    typical_duration_minutes: Mapped[Optional[int]] # Official recommendation from the museum

    # Constraints
    __table_args__ = (
        UniqueConstraint("museum_id", "name", name="uq_exhibition_museum_name"),
        CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR start_date <= end_date",
            name="ck_exhibition_date_range",
        ),
        CheckConstraint("NOT is_permanent OR end_date IS NULL", name="ck_permanent_wth_date"),
        CheckConstraint("typical_duration_minutes > 0", name="ck_visit_duration_nonneg"),
    )

    # Relationships
    museum: Mapped["Museum"] = relationship(back_populates="exhibitions")
    tickets: Mapped[list["Ticket"]] = relationship(
        secondary="ticket_exhibition", back_populates="exhibitions"
    )

    def __repr__(self) -> str:
        return f"Exhibition(id={self.id!r}, name={self.name!r}, museum_id={self.museum_id!r})"

    def __str__(self) -> str:
        return f"{self.name}"

class ExhibitionVisit(db.Model):
    __tablename__ = "exhibition_visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    exhibition_id: Mapped[int] = mapped_column(ForeignKey("exhibition.id"))
    visit_date: Mapped[date]
    duration_minutes: Mapped[Optional[int]]

    # Unique rows with [user, exhibition]
    __table_args__ = (
        UniqueConstraint("user_id", "exhibition_id", "visit_date", name="uq_user_exhibition_visit"),
        CheckConstraint("duration_minutes > 0", name="ck_visit_duration_nonneg")
    )

    # Relationships
    user: Mapped["User"] = relationship(backref="exhibition_visits")
    exhibition: Mapped["Exhibition"] = relationship(backref="exhibition_visits")

    def __repr__(self) -> str:
        return f"ExhibitionVisit(id={self.id!r}, user_id={self.user_id!r}, exhibition_id={self.exhibition_id!r}, visit_date={self.visit_date!r})"

    def __str__(self) -> str:
        return f"{self.user} - {self.exhibition} ({self.visit_date})"

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

    def __repr__(self) -> str:
        return f"ExhibitionWishlist(id={self.id!r}, user_id={self.user_id!r}, exhibition_id={self.exhibition_id!r})"

    def __str__(self) -> str:
        return f"{self.user} - {self.exhibition}"

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

    def __repr__(self) -> str:
        return f"ExhibitionReview(id={self.id!r}, user_id={self.user_id!r}, exhibition_id={self.exhibition_id!r})"

    def __str__(self) -> str:
        rating_str = f" ({self.rating}/10)" if self.rating else ""
        return f"{self.user} - {self.exhibition}{rating_str}"

class MuseumPass(db.Model):
    __tablename__ = "passes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True) # Include period in the name (e.g. "24h", "48h", "72h", "Year")
    website: Mapped[Optional[str]] = mapped_column(String(254))
    includes_transport: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    prices: Mapped[list["PassPrice"]] = relationship(
        back_populates="museum_pass", passive_deletes=True
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="museum_pass", passive_deletes="all"
    )

    def __repr__(self) -> str:
        return f"MuseumPass(id={self.id!r}, name={self.name!r})"

    def __str__(self) -> str:
        return f"{self.name}"

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

    # Constraints
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

    #Relationships
    museum_pass: Mapped["MuseumPass"] = relationship(back_populates="prices")

    def __repr__(self) -> str:
        return f"PassPrice(id={self.id!r}, label={self.label!r})"

    def __str__(self) -> str:
        return f"{self.label}"

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
    day_from: Mapped[Optional[int]]
    month_to: Mapped[Optional[int]]
    day_to: Mapped[Optional[int]]

class EntryPolicy(enum.Enum):
    # How the user must book/enter the museum.
    anytime = "anytime"               # Walk-in, no reservation needed
    recommended = "recommended"       # Walk-in allowed, but booking recommended to skip lines
    timed_slot = "timed_slot"         # Must reserve a specific time slot in advance

class Validity(enum.Enum):
    single_entry = "single_entry"
    same_day = "same_day"
    period = "period"

class Ticket(AudienceConditionsMixin, ScheduleConditionsMixin, db.Model):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    museum_id: Mapped[int] = mapped_column(ForeignKey("museum.id"))
    label: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    pass_id: Mapped[Optional[int]] = mapped_column(ForeignKey("passes.id", ondelete="RESTRICT"))
    entry_policy: Mapped[EntryPolicy] = mapped_column(
        Enum(EntryPolicy, native_enum=False, create_constraint=True, name="entry_policy"),
        default=EntryPolicy.anytime
    )
    validity: Mapped[Validity] = mapped_column(
        Enum(Validity, native_enum=False, create_constraint=True, name="validity"),
        default=Validity.single_entry,
    )
    validity_value: Mapped[Optional[int]]                 # with validity=period
    validity_unit: Mapped[Optional[DurationUnit]] = mapped_column(
        Enum(DurationUnit, native_enum=False, create_constraint=True, name="ticket_validity_unit")
    )

    # Constraints
    __table_args__ = (
        # Same label may exist in different yearly periods (summer / winter).
        UniqueConstraint(
            "museum_id", "label", "month_from", "day_from", "month_to", "day_to",
            name="uq_ticket_museum_label_period",
        ),
        # NULLs count as distinct in a UNIQUE constraint, so the one above can't
        # catch two year-round rows with the same label. This partial index does.
        Index(
            "uq_ticket_museum_label_year_round", "museum_id", "label",
            unique=True,
            sqlite_where=text("month_from IS NULL"),
            postgresql_where=text("month_from IS NULL"),
        ),
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
        # Yearly period (same rule as opening hours)
        CheckConstraint(
            "(month_from IS NULL AND month_to IS NULL) "
            "OR (month_from BETWEEN 1 AND 12 AND month_to BETWEEN 1 AND 12 "
            "AND month_from <= month_to)",
            name="ck_ticket_month_range",
        ),
        CheckConstraint(
            "(day_from IS NULL OR day_from BETWEEN 1 AND 31) "
            "AND (day_to IS NULL OR day_to BETWEEN 1 AND 31)",
            name="ck_ticket_period_days",
        ),
        CheckConstraint(
            "(validity = 'period' AND validity_value IS NOT NULL AND validity_unit IS NOT NULL) "
            "OR (validity != 'period' AND validity_value IS NULL AND validity_unit IS NULL)",
            name="ck_ticket_validity_period",
        ),
        CheckConstraint(
            "validity_value IS NULL OR validity_value > 0",
            name="ck_ticket_validity_positive",
        ),
    )

    # Relationships
    museum: Mapped["Museum"] = relationship(back_populates="tickets")
    museum_pass: Mapped[Optional["MuseumPass"]] = relationship(back_populates="tickets")
    exhibitions: Mapped[list["Exhibition"]] = relationship(
        secondary="ticket_exhibition", back_populates="tickets"
    )

    def __repr__(self) -> str:
        return f"Ticket(id={self.id!r}, museum_id={self.museum_id!r}, label={self.label!r})"
    def __str__(self) -> str:
        return f"{self.label}"

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
    )

    # Relationships
    museum: Mapped["Museum"] = relationship(back_populates="opening_hours")

    def __repr__(self) -> str:
        return f"OpeningHours(id={self.id!r}, museum_id={self.museum_id!r})"

    def __str__(self) -> str:
        if self.label:
            return self.label
        if self.is_closed:
            return "Closed"
        return f"{self.start_time} - {self.end_time}"

class Language(db.Model):
    __tablename__ = "languages"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True)   # "pt", "en", "pt-BR"
    name: Mapped[str] = mapped_column(String(50))                # "Portuguese"

    # Relationships
    guided_visits: Mapped[list["GuidedVisit"]] = relationship(
        secondary="guided_visit_languages",
        back_populates="languages"
    )

    def __repr__(self) -> str:
        return f"Language(id={self.id!r}, code={self.code!r}, name={self.name!r})"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

# Association table between Museum and Language
museum_language = Table(
    "museum_language",
    db.metadata,
    Column("museum_id", ForeignKey("museum.id"), primary_key=True),
    Column("language_id", ForeignKey("languages.id"), primary_key=True),
)

class AudioguideType(enum.Enum):
    smartphone_app = "smartphone_app"
    web_qr = "web_qr"
    physical_device = "physical_device"

class Audioguide(db.Model):
    __tablename__ = "audioguides"

    id: Mapped[int] = mapped_column(primary_key=True)
    museum_id: Mapped[int] = mapped_column(ForeignKey("museum.id", ondelete="CASCADE"))
    audioguide_type: Mapped[AudioguideType] = mapped_column(
        Enum(AudioguideType, native_enum=False, create_constraint=True, name="audioguide_type")
    )
    requires_own_headphones: Mapped[bool] = mapped_column(default=False)
    deposit_required: Mapped[bool] = mapped_column(default=False)
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2))       # 0 = free
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Constraints
    __table_args__ = (
        UniqueConstraint("museum_id", "audioguide_type", name="uq_audioguide_museum_type"),
        CheckConstraint("price >= 0", name="ck_audioguide_price_nonneg"),
    )

    # Relationships
    museum: Mapped["Museum"] = relationship(back_populates="audioguides")
    languages: Mapped[list["Language"]] = relationship(secondary="audioguide_language")

    def __repr__(self) -> str:
        return f"Audioguide(id={self.id!r}, museum_id={self.museum_id!r}, audioguide_type={self.audioguide_type!r})"

    def __str__(self) -> str:
        return f"{self.audioguide_type}"

# Association table between Audioguide and Language    
audioguide_language = Table(
    "audioguide_language",
    db.metadata,
    Column("audioguide_id", ForeignKey("audioguides.id", ondelete="CASCADE"), primary_key=True),
    Column("language_id", ForeignKey("languages.id"), primary_key=True),
)

class GuidedVisit(ScheduleConditionsMixin, db.Model):
    __tablename__ = "guided_visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    museum_id: Mapped[int] = mapped_column(ForeignKey("museum.id", ondelete="CASCADE"))
    exhibition_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exhibition.id", ondelete="SET NULL")
    )
    
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # --- Tour-specific fields ---
    duration_minutes: Mapped[int]
    max_participants: Mapped[Optional[int]]
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    requires_reservation: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        # 1. Tour specific constraints
        CheckConstraint("duration_minutes > 0", name="ck_guided_visit_duration_positive"),
        CheckConstraint(
            "max_participants IS NULL OR max_participants > 0",
            name="ck_guided_visit_max_participants",
        ),
        CheckConstraint("price IS NULL OR price >= 0", name="ck_guided_visit_price_nonneg"),
        
        # 2. Mixin field validity constraints (allowing NULLs, but restricting ranges if populated)
        CheckConstraint("weekday IS NULL OR weekday BETWEEN 0 AND 6", name="ck_guided_visit_weekday"),
        CheckConstraint(
            "week_of_month IS NULL OR week_of_month IN (-1, 1, 2, 3, 4, 5)",
            name="ck_guided_visit_week_of_month",
        ),
        CheckConstraint("month IS NULL OR month BETWEEN 1 AND 12", name="ck_guided_visit_month"),
        CheckConstraint("day IS NULL OR day BETWEEN 1 AND 31", name="ck_guided_visit_day"),
        
        # 3. The "Must have a valid schedule" constraint
        # A tour MUST have a start_time, AND it must be either a weekly schedule, 
        # a specific date, or a holiday.
        CheckConstraint(
            "start_time IS NOT NULL AND ("
            "weekday IS NOT NULL OR "
            "(month IS NOT NULL AND day IS NOT NULL) OR "
            "holidays = True"
            ")",
            name="ck_guided_visit_has_schedule"
        ),

        # 4. Seasonal validity (if month_from is set, the rest must be set)
        CheckConstraint(
            "month_from IS NULL OR (month_to IS NOT NULL AND day_from IS NOT NULL AND day_to IS NOT NULL)",
            name="ck_guided_visit_seasonal_pair",
        ),
        
        # 5. Unique constraint to prevent duplicate tours at the exact same time
        # Note: Because these fields can be NULL, SQL treats NULLs as distinct. 
        # This is generally fine for preventing obvious duplicates.
        UniqueConstraint(
            "museum_id", "name", "weekday", "week_of_month", "month", "day", "holidays", "start_time", 
            name="uq_guided_visit_slot"
        ),
    )

    # Relationships
    museum: Mapped["Museum"] = relationship(back_populates="guided_visits")
    exhibition: Mapped[Optional["Exhibition"]] = relationship()
    languages: Mapped[list["Language"]] = relationship(
        secondary="guided_visit_languages",
        back_populates="guided_visits",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"GuidedVisit(id={self.id!r}, name={self.name!r})"

    def __str__(self) -> str:
        return f"{self.name}"

guided_visit_languages = Table(
    "guided_visit_languages",
    db.Model.metadata,
    Column("guided_visit_id", ForeignKey("guided_visits.id", ondelete="CASCADE"), primary_key=True),
    Column("language_id", ForeignKey("languages.id", ondelete="CASCADE"), primary_key=True),
)
