"""Flask-Admin glue: puts the pass-price editor inside the Pass edit page.

Use it as a mixin before ModelView, like MuseumHoursMixin.
"""

from flask import flash, jsonify, redirect, render_template, request
from flask_admin import expose
from werkzeug.exceptions import abort

from ..models import MuseumPass
from .pass_prices_edit import bulk_update, expand_rows, parse_form, prices_context


class PassPricesMixin:
    def render(self, template, **kwargs):
        if template == self.edit_template and kwargs.get("model") is not None:
            kwargs.update(prices_context(kwargs["model"]))
        return super().render(template, **kwargs)

    @expose("/<int:pass_id>/prices/", methods=["POST"])
    def prices_view(self, pass_id):
        if not self.can_edit:
            abort(403)
        museum_pass = self.session.get(MuseumPass, pass_id) or abort(404)
        back = self.get_url(".edit_view", id=museum_pass.id,
                            url=request.form.get("return_url") or None)
        action = request.form.get("action")

        if action in ("preview", "save"):
            durations, currency, rows = parse_form(request.form)
            expansion = expand_rows(durations, currency, rows, museum_pass.id, museum_pass.prices)
            saved = False
            if action == "save":
                if expansion.can_save:
                    self.session.add_all(expansion.to_add)
                    self.session.commit()
                    flash(f"Added {len(expansion.to_add)} prices.")
                    saved = True
                elif not expansion.errors:
                    expansion.errors.append("Nothing to add: those prices already exist.")
            html = render_template("admin/museum_pass/_prices_preview.html", expansion=expansion)
            return jsonify(saved=saved, html=html)

        ids = request.form.getlist("selected", type=int)
        selected = [p for p in museum_pass.prices if p.id in ids]   # only this pass's rows
        if not selected:
            flash("Select at least one row first.")
        elif action == "delete":
            for p in selected:
                self.session.delete(p)
            self.session.commit()
            flash(f"Deleted {len(selected)} prices.")
        elif action == "bulk_update":
            count, errors = bulk_update(selected, request.form)
            if errors:
                for e in errors:
                    flash(e)
            else:
                self.session.commit()
                flash(f"Updated {count} prices.")
        return redirect(back)