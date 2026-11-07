from flask import abort, redirect, request, url_for
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.template import EndpointLinkRowAction
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user
from flask_wtf import FlaskForm
from markupsafe import Markup
from werkzeug.security import generate_password_hash
from wtforms import PasswordField

from .. import models
from ..extensions import db


class AdminAccessMixin:
    """Only logged-in admins may see anything under the admin."""

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.url))
        abort(403)


class SecureIndexView(AdminAccessMixin, AdminIndexView):
    pass


def _format_date(view, context, model, name):
    value = getattr(model, name)
    return value.strftime("%Y-%m-%d") if value else ""


def _format_image(view, context, model, name):
    url = getattr(model, name)
    # Markup(...).format() escapes the URL; Markup("...".format(url)) does not.
    return Markup('<img src="{}" height="40" alt="">').format(url) if url else ""


class BaseView(AdminAccessMixin, ModelView):
    form_base_class = FlaskForm        # adds the CSRF token (you use CSRFProtect)
    column_display_pk = True
    can_view_details = True
    page_size = 50
    column_formatters = {
        "created_at": _format_date,
        "updated_at": _format_date,
    }


class UserView(BaseView):
    column_exclude_list = ("password_hash",)
    column_searchable_list = ("username", "email")
    # Visits/wishlists/reviews are the users' own data, not edited from here.
    form_excluded_columns = (
        "password_hash", "created_at",
        "museum_visits", "museum_wishlist", "museum_reviews",
        "exhibition_visits", "exhibition_wishlist", "exhibition_reviews",
    )
    form_extra_fields = {"password": PasswordField("New password")}

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password_hash = generate_password_hash(form.password.data)
        elif is_created:
            raise ValueError("A password is required for new users.")


class MuseumView(BaseView):
    column_list = ("name", "city", "country", "image_url", "website")
    column_searchable_list = ("name", "city")
    column_filters = ("country", "city")
    column_formatters = {**BaseView.column_formatters, "image_url": _format_image}
    # Children get their own views; loading them all into multi-selects here
    # would be slow and lets you reassign rows by accident.
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


admin = Admin(
    name="Administration",
    theme=Bootstrap4Theme(swatch="lux"),
    index_view=SecureIndexView(),
)

admin.add_view(UserView(models.User, db.session))
admin.add_view(MuseumView(models.Museum, db.session))