from flask import abort, redirect, request, url_for
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.template import EndpointLinkRowAction
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user
from flask_security import hash_password, current_user
from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import PasswordField
from wtforms.validators import NumberRange
from datetime import date
from flask_admin.actions import action
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form import rules
from sqlalchemy import inspect

from .pass_prices_admin import PassPricesMixin
from .schedule_forms import (
    EXHIBITION_ARGS, SCHEDULE_ARGS, SCHEDULE_OVERRIDES,
    ScheduleValidationMixin, exhibition_label, exhibition_query,
)


from ..museums.exhibitions import is_archived
from .. import models
from ..extensions import db

from .hours_admin import MuseumHoursMixin
from .tickets_admin import MuseumTicketsMixin

WEEKDAY_NAMES = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
                 4: "Friday", 5: "Saturday", 6: "Sunday"}

class AdminAccessMixin:
    def is_accessible(self):
        return current_user.is_active and current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("security.login", next=request.url))
        abort(403)


class SecureIndexView(AdminAccessMixin, AdminIndexView):
    pass


def _format_date(view, context, model, name):
    value = getattr(model, name)
    return value.strftime("%Y-%m-%d") if value else ""


def _format_image(view, context, model, name):
    url = getattr(model, name)
    return Markup('<img src="{}" height="40" alt="">').format(url) if url else ""


class BaseView(AdminAccessMixin, ModelView):
    form_base_class = FlaskForm
    column_display_pk = True
    can_view_details = True
    page_size = 50
    column_formatters = {
        "created_at": _format_date,
        "updated_at": _format_date,
    }


class OpeningHoursView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role("admin")

    @expose("/", methods=["GET", "POST"])
    def index(self):
        museum = db.get_or_404(models.Museum, request.args.get("museum_id", type=int))
        return self.render("museums/hours_edit.html", museum=museum)


class UserView(BaseView):
    column_exclude_list = ("password", "fs_uniquifier")
    form_excluded_columns = (
        "password", "fs_uniquifier", "created_at",
        "museum_visits", "museum_wishlist", "museum_reviews",
        "exhibition_visits", "exhibition_wishlist", "exhibition_reviews",
    )
    form_extra_fields = {"new_password": PasswordField("New password")}

    def on_model_change(self, form, model, is_created):
        if form.new_password.data:
            model.password = hash_password(form.new_password.data)
        elif is_created:
            raise ValueError("A password is required for new users.")


class MuseumView(MuseumTicketsMixin, MuseumHoursMixin, BaseView):
    edit_template = "admin/museum/edit.html"
    column_list = ("name", "city", "country", "image_url", "website")
    column_searchable_list = ("name", "city")
    column_filters = ("country", "city")
    column_formatters = {**BaseView.column_formatters, "image_url": _format_image}
    form_excluded_columns = (
        "created_at", "updated_at",
        "tickets", "exhibitions", "opening_hours", "audioguides", "guided_visits",
        "museum_visits", "museum_wishlist", "museum_reviews",
    )
    column_extra_row_actions = [
        EndpointLinkRowAction(
            "fa fa-eye", "museums.museum", id_arg="museum_id", title="View on site"
        ),
    ]

class ExhibitionForm(FlaskForm):
    """Same rules as the CheckConstraints in models.py, so the admin gets a
    message next to the field instead of an IntegrityError."""

    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators)
        permanent = self.is_permanent.data
        start, end = self.start_date.data, self.end_date.data

        if permanent and end:
            self.end_date.errors = [*self.end_date.errors,
                                    "A permanent exhibition can't have an end date."]
            ok = False
        if start and end and start > end:
            self.end_date.errors = [*self.end_date.errors,
                                    "The end date can't be before the start date."]
            ok = False
        return ok


def _format_exhibition_status(view, context, model, name):
    if model.is_permanent:
        return "Permanent"
    return "Ended" if is_archived(model, date.today()) else "Current"


class ExhibitionView(BaseView):
    form_base_class = ExhibitionForm

    column_list = ("name", "museum", "status", "start_date", "end_date", "image_url")
    column_searchable_list = ("name", "museum.name")
    column_filters = ("museum.name", "museum.city", "is_permanent", "start_date", "end_date")
    column_default_sort = ("start_date", True)
    column_formatters = {
        **BaseView.column_formatters,
        "status": _format_exhibition_status,
        "start_date": _format_date,
        "end_date": _format_date,
        "image_url": _format_image,
    }
    column_labels = {"typical_duration_minutes": "Visit time (min)"}

    form_columns = (
        "museum", "name", "is_permanent", "start_date", "end_date",
        "typical_duration_minutes", "short_description", "long_description",
        "website", "image_url",
    )
    form_args = {
        "is_permanent": {"description": "Permanent exhibitions have no end date."},
        "typical_duration_minutes": {
            "description": "Visit time recommended by the museum.",
            "validators": [NumberRange(min=1)],
        },
    }

    column_extra_row_actions = [
        EndpointLinkRowAction(
            "fa fa-eye", "museums.exhibition", id_arg="exhibition_id", title="View on site"
        ),
    ]

class RoleView(BaseView):
    column_searchable_list = ("name",)
    form_excluded_columns = ("users",)

def _short(field, length=80):
    def formatter(view, context, model, name):
        text = getattr(model, field) or ""
        return text if len(text) <= length else text[:length] + "…"
    return formatter


class ExhibitionView(BaseView):
    column_list = ("museum", "name", "is_permanent", "start_date", "end_date",
                   "typical_duration_minutes", "image_url")
    column_searchable_list = ("name", "museum.name")
    column_filters = ("museum.name", "is_permanent", "start_date", "end_date")
    column_default_sort = ("end_date", True)
    column_formatters = {**BaseView.column_formatters,
                         "start_date": _format_date, "end_date": _format_date,
                         "image_url": _format_image}
    form_excluded_columns = ("tickets", "exhibition_visits",
                             "exhibition_wishlist", "exhibition_reviews")
    form_extra_fields = {
        "copy_tickets_from": QuerySelectField(
            "Give it the same tickets as",
            query_factory=exhibition_query, get_label=exhibition_label,
            allow_blank=True, blank_text="—",
            description="Adds this exhibition to every ticket that covers the chosen one "
                        "(same museum). Fine-tune afterwards in Tickets.",
        ),
    }
    column_extra_row_actions = [
        EndpointLinkRowAction("fa fa-eye", "museums.exhibition",
                              id_arg="exhibition_id", title="View on site"),
    ]
    can_export = True

    def on_model_change(self, form, model, is_created):
        source = form.copy_tickets_from.data
        if source is not None and source is not model:
            if source.museum != model.museum:
                raise ValueError("Copy tickets from an exhibition of the same museum")
            for ticket in list(source.tickets):
                if model not in ticket.exhibitions:
                    ticket.exhibitions.append(model)


class TicketView(ScheduleValidationMixin, BaseView):
    column_list = ("museum", "label", "price", "currency", "museum_pass",
                   "min_age", "max_age", "is_student", "resident_municipality",
                   "resident_country", "entry_policy", "validity")
    column_searchable_list = ("label", "museum.name")
    column_filters = ("museum.name", "museum_pass.name", "is_student",
                      "price", "month_from", "month_to")
    column_default_sort = "museum_id"
    can_export = True

    form_overrides = SCHEDULE_OVERRIDES
    form_args = {**SCHEDULE_ARGS, "exhibitions": EXHIBITION_ARGS}
    form_rules = [
        rules.FieldSet(["museum", "label", "price", "currency", "notes"], "Basics"),
        rules.FieldSet(["exhibitions"], "Covers these exhibitions"),
        rules.FieldSet(["museum_pass", "is_student", "min_age", "max_age",
                        "resident_country", "resident_municipality"], "Who it is for"),
        rules.FieldSet(["entry_policy", "validity", "validity_value", "validity_unit"],
                       "Booking and validity"),
        rules.FieldSet(["month_from", "day_from", "month_to", "day_to"],
                       "Season (leave empty for all year)"),
        rules.FieldSet(["weekday", "week_of_month", "start_time", "end_time",
                        "month", "day", "holidays"],
                       "Special access rule (e.g. free first Monday, free on holidays)"),
    ]

    def on_model_change(self, form, model, is_created):
        validity = getattr(model.validity, "value", model.validity)
        if validity != "period":
            model.validity_value = None       # only periods have a length
            model.validity_unit = None
        elif model.validity_value is None or model.validity_unit is None:
            raise ValueError("A ticket valid for a period needs a length and a unit (e.g. 1 years)")
        super().on_model_change(form, model, is_created)

    @action("duplicate", "Duplicate", "Duplicate the selected tickets?")
    def action_duplicate(self, ids):
        try:
            for t in self.session.scalars(db.select(models.Ticket).where(models.Ticket.id.in_(ids))):
                values = {a.key: getattr(t, a.key) for a in inspect(models.Ticket).column_attrs
                          if a.key not in ("id", "label")}
                copy = models.Ticket(label=f"{t.label} (copy)", **values)
                copy.exhibitions = list(t.exhibitions)
                self.session.add(copy)
            self.session.commit()
            flash(f"Duplicated {len(ids)} tickets. Edit the copies to change their label or season.")
        except Exception as ex:
            self.session.rollback()
            flash(f"Could not duplicate: {ex}", "error")


class MuseumPassView(PassPricesMixin, BaseView):
    edit_template = "admin/museum_pass/edit.html"
    column_list = ("name", "includes_transport", "website")
    column_searchable_list = ("name",)
    # Prices are edited in the panel on the edit page (see pass_prices_admin.py).
    form_excluded_columns = ("tickets", "prices")


class AudioguideView(BaseView):
    column_list = ("museum", "audioguide_type", "price", "currency",
                   "requires_own_headphones", "deposit_required", "languages")
    column_filters = ("museum.name", "audioguide_type")
    column_searchable_list = ("museum.name",)


class GuidedVisitView(ScheduleValidationMixin, BaseView):
    column_list = ("museum", "exhibition", "name", "weekday", "start_time",
                   "duration_minutes", "price", "requires_reservation", "languages")
    column_searchable_list = ("name", "museum.name")
    column_filters = ("museum.name", "requires_reservation")
    column_formatters = {
        **BaseView.column_formatters,
        "weekday": lambda v, c, m, n: WEEKDAY_NAMES.get(m.weekday, ""),
    }

    form_overrides = SCHEDULE_OVERRIDES
    form_args = {**SCHEDULE_ARGS, "exhibition": EXHIBITION_ARGS}
    form_rules = [
        rules.FieldSet(["museum", "exhibition", "name", "description", "languages"], "Basics"),
        rules.FieldSet(["duration_minutes", "max_participants", "price", "currency",
                        "requires_reservation", "notes"], "Practical details"),
        rules.FieldSet(["weekday", "week_of_month", "start_time", "end_time",
                        "month", "day", "holidays"], "When"),
        rules.FieldSet(["month_from", "day_from", "month_to", "day_to"],
                       "Season (leave empty for all year)"),
    ]

    def on_model_change(self, form, model, is_created):
        if model.start_time is None:
            raise ValueError("A guided visit needs a start time")
        if model.weekday is None and model.month is None and not model.holidays:
            raise ValueError("Pick when it runs: a weekday, an annual date, or public holidays")
        if model.month_from is not None and (model.day_from is None or model.day_to is None):
            raise ValueError("A season needs first and last days as well as months")
        super().on_model_change(form, model, is_created)


class LanguageView(BaseView):
    column_searchable_list = ("code", "name")
    form_excluded_columns = ("guided_visits",)

class PaymentMethodView(BaseView):
    column_searchable_list = ("code", "name")
    form_excluded_columns = ("museums",)


# --- Community data: mostly read-only, for moderation ---------------------

class ReadOnlyActivityView(BaseView):
    can_create = False
    can_edit = False
    can_export = True


class MuseumReviewView(ReadOnlyActivityView):
    column_list = ("user", "museum", "rating", "review", "created_at")
    column_formatters = {**BaseView.column_formatters, "review": _short("review")}
    column_searchable_list = ("user.username", "museum.name", "review")
    column_filters = ("museum.name", "rating", "created_at")


class ExhibitionReviewView(ReadOnlyActivityView):
    column_list = ("user", "exhibition", "rating", "review", "created_at")
    column_formatters = {**BaseView.column_formatters, "review": _short("review")}
    column_searchable_list = ("user.username", "exhibition.name", "review")
    column_filters = ("exhibition.name", "rating", "created_at")


class MuseumVisitView(ReadOnlyActivityView):
    column_list = ("user", "museum", "visit_date")
    column_searchable_list = ("user.username", "museum.name")
    column_filters = ("museum.name", "visit_date")


class ExhibitionVisitView(ReadOnlyActivityView):
    column_list = ("user", "exhibition", "visit_date", "duration_minutes")
    column_searchable_list = ("user.username", "exhibition.name")
    column_filters = ("exhibition.name", "visit_date")


class MuseumWishlistView(ReadOnlyActivityView):
    column_list = ("user", "museum")
    column_searchable_list = ("user.username", "museum.name")


class ExhibitionWishlistView(ReadOnlyActivityView):
    column_list = ("user", "exhibition")
    column_searchable_list = ("user.username", "exhibition.name")

admin = Admin(
    name="Administration",
    theme=Bootstrap4Theme(swatch="lux"),
    index_view=SecureIndexView(),
)

admin.add_view(UserView(models.User, db.session, category="Accounts"))
admin.add_view(RoleView(models.Role, db.session, category="Accounts"))

admin.add_view(MuseumView(models.Museum, db.session, category="Catalogue"))
admin.add_view(ExhibitionView(models.Exhibition, db.session, category="Catalogue"))
admin.add_view(TicketView(models.Ticket, db.session, category="Catalogue"))
admin.add_view(MuseumPassView(models.MuseumPass, db.session, name="Passes", category="Catalogue"))
admin.add_view(AudioguideView(models.Audioguide, db.session, category="Catalogue"))
admin.add_view(GuidedVisitView(models.GuidedVisit, db.session, name="Guided visits", category="Catalogue"))
admin.add_view(LanguageView(models.Language, db.session, category="Catalogue"))
admin.add_view(PaymentMethodView(models.PaymentMethod, db.session, name="Payment methods", category="Catalogue"))

admin.add_view(MuseumReviewView(models.MuseumReview, db.session, name="Museum reviews", category="Community"))
admin.add_view(ExhibitionReviewView(models.ExhibitionReview, db.session, name="Exhibition reviews", category="Community"))
admin.add_view(MuseumVisitView(models.MuseumVisit, db.session, name="Museum visits", category="Community"))
admin.add_view(ExhibitionVisitView(models.ExhibitionVisit, db.session, name="Exhibition visits", category="Community"))
admin.add_view(MuseumWishlistView(models.MuseumWishlist, db.session, name="Museum wishlists", category="Community"))
admin.add_view(ExhibitionWishlistView(models.ExhibitionWishlist, db.session, name="Exhibition wishlists", category="Community"))