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

from .. import models
from ..extensions import db

from .hours_admin import MuseumHoursMixin
from .tickets_admin import MuseumTicketsMixin


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


class RoleView(BaseView):
    column_searchable_list = ("name",)
    form_excluded_columns = ("users",)


admin = Admin(
    name="Administration",
    theme=Bootstrap4Theme(swatch="lux"),
    index_view=SecureIndexView(),
)

admin.add_view(UserView(models.User, db.session))
admin.add_view(MuseumView(models.Museum, db.session))
admin.add_view(RoleView(models.Role, db.session))
