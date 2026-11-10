"""Flask-Admin glue: puts the opening-hours editor inside the Museum edit page.

Use it as a mixin *before* ModelView:

    class MuseumAdmin(MuseumHoursMixin, ModelView):
        edit_template = "admin/museum/edit.html"
"""

from flask import flash, jsonify, redirect, render_template, request
from flask_admin import expose
from werkzeug.exceptions import abort

from ..models import Museum
from .hours_edit import (
    RuleInput, bulk_update, expand_rules, hours_context, parse_rules,
)


class MuseumHoursMixin:
    def render(self, template, **kwargs):
        # edit_view passes the museum as `model`; the hours panel needs its rows.
        if template == self.edit_template and kwargs.get("model") is not None:
            kwargs.update(hours_context(kwargs["model"]))
        return super().render(template, **kwargs)

    @expose("/<int:museum_id>/hours/", methods=["POST"])
    def hours_view(self, museum_id):
        if not self.can_edit:
            abort(403)
        museum = self.session.get(Museum, museum_id) or abort(404)
        back = self.get_url(".edit_view", id=museum.id, url=request.form.get("return_url") or None)
        action = request.form.get("action")

        # Preview / save of new rules: called with fetch(), answers with JSON.
        if action in ("preview", "save"):
            rules = parse_rules(request.form)
            expansion = expand_rules(rules, museum.id, museum.opening_hours)
            saved = False
            if action == "save":
                if expansion.can_save:
                    self.session.add_all(expansion.to_add)
                    self.session.commit()
                    flash(f"Added {len(expansion.to_add)} opening-hours rows.")
                    saved = True
                elif not expansion.errors:
                    expansion.errors.append("Nothing to add: those rows already exist.")
            html = render_template("admin/museum/_hours_preview.html", expansion=expansion)
            return jsonify(saved=saved, html=html)

        # Delete / change several existing rows: ordinary form post, then back to the edit page.
        ids = request.form.getlist("selected", type=int)
        selected = [h for h in museum.opening_hours if h.id in ids]   # only this museum's rows
        if not selected:
            flash("Select at least one row first.")
        elif action == "delete":
            for h in selected:
                self.session.delete(h)
            self.session.commit()
            flash(f"Deleted {len(selected)} rows.")
        elif action == "bulk_update":
            count, errors = bulk_update(selected, request.form)
            if errors:
                for e in errors:
                    flash(e)
            else:
                self.session.commit()
                flash(f"Updated {count} rows.")
        return redirect(back)
