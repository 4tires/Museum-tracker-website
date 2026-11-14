"""Flask-Admin glue: the tickets editor on the Museum edit page.

Mixed into MuseumView (before BaseView). It adds the ticket data to the edit
page and one POST endpoint that the panel talks to with fetch(). Every answer is
JSON: {"saved": bool, "html": "<preview or error markup>"}. The panel shows the
html when nothing was saved, and reloads the page when something was, so the
museum form above is never reloaded under your hands and typed values are never
lost to a validation error.

What the endpoint does is chosen by the "action" field:

    preview / save        the add/edit form (ticket_id present = edit one row)
    bulk_price_preview    show old -> new prices for the selected tickets
    bulk_price            apply them
    bulk_exhibitions      add / remove / replace exhibitions on the selected tickets
    delete                delete the selected tickets
"""

from datetime import date

from flask import flash, jsonify, render_template, request
from flask_admin import expose
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import abort

from .. import models
from .tickets_edit import (
    EXHIBITION_MODES, change_exhibitions, plan_price_change, plan_ticket,
    plan_ticket_batch, tickets_context,
)


class MuseumTicketsMixin:
    def render(self, template, **kwargs):
        # edit_view passes the museum as `model`; the panel needs its tickets.
        if template == self.edit_template and kwargs.get("model") is not None:
            kwargs.update(tickets_context(kwargs["model"], self._passes(), date.today()))
        return super().render(template, **kwargs)

    def _passes(self):
        return self.session.query(models.MuseumPass).order_by(models.MuseumPass.name).all()

    @staticmethod
    def _reply(saved=False, **context):
        context.setdefault("errors", [])
        return jsonify(saved=saved, html=render_template("admin/museum/_tickets_preview.html", **context))

    @expose("/<int:museum_id>/tickets/", methods=["POST"])
    def tickets_view(self, museum_id):
        if not self.can_edit:
            abort(403)
        museum = self.session.get(models.Museum, museum_id) or abort(404)

        action = request.form.get("action")
        if action in ("preview", "save"):
            return self._save_ticket(museum, commit=(action == "save"))
        if action in ("batch_preview", "batch_save"):
            return self._save_ticket_batch(museum, commit=(action == "batch_save"))

        # The other actions work on the ticked rows. Only this museum's tickets can be picked.
        wanted = set(request.form.getlist("selected", type=int))
        selected = [t for t in museum.tickets if t.id in wanted]
        if not selected:
            return self._reply(errors=["Select at least one ticket first."])

        if action in ("bulk_price_preview", "bulk_price"):
            return self._change_prices(selected, commit=(action == "bulk_price"))
        if action == "bulk_exhibitions":
            return self._change_exhibitions(museum, selected)
        if action == "delete":
            for ticket in selected:
                self.session.delete(ticket)
            self.session.commit()
            flash(f"Deleted {len(selected)} ticket{'s' if len(selected) != 1 else ''}.")
            return self._reply(saved=True)
        abort(400)

    # --- add / edit one ticket -----------------------------------------------

    def _save_ticket(self, museum, commit: bool):
        plan = plan_ticket(
            request.form, museum_id=museum.id, tickets=museum.tickets,
            exhibitions=museum.exhibitions, passes=self._passes(), today=date.today(),
            editing_id=request.form.get("ticket_id", type=int),
        )
        if commit and plan.can_save:
            for row in plan.rows:
                if row.target is not None:
                    ticket = row.target
                    for key, value in row.values.items():
                        setattr(ticket, key, value)
                else:
                    ticket = models.Ticket(museum_id=museum.id, **row.values)
                    self.session.add(ticket)
                ticket.exhibitions = list(plan.exhibitions)
            try:
                self.session.commit()
            except IntegrityError as error:
                # plan_ticket checks the same rules, so this means a rule it doesn't know about.
                self.session.rollback()
                plan.errors.append(f"The database rejected the ticket: {error.orig}")
            else:
                label = plan.rows[0].values["label"]
                flash(f'Saved "{label}".' if len(plan.rows) == 1 else
                      f'Saved "{label}" with {len(plan.rows)} prices.')
                return self._reply(saved=True)
        return self._reply(plan_rows=plan.rows, errors=plan.errors, warnings=plan.warnings)


    def _save_ticket_batch(self, museum, commit: bool):
        plan = plan_ticket_batch(
            request.form, museum_id=museum.id, tickets=museum.tickets,
            exhibitions=museum.exhibitions, passes=self._passes(), today=date.today(),
        )
        # Count submitted ticket definitions, rather than the expanded seasonal DB rows.
        import json
        try:
            ticket_count = len(json.loads(request.form.get("ticket_rows", "[]")))
        except (TypeError, ValueError):
            ticket_count = 0

        if commit and plan.can_save:
            for row in plan.rows:
                ticket = models.Ticket(museum_id=museum.id, **row.values)
                self.session.add(ticket)
                ticket.exhibitions = list(plan.exhibitions)
            try:
                self.session.commit()
            except IntegrityError as error:
                self.session.rollback()
                plan.errors.append(f"The database rejected the ticket batch: {error.orig}")
            else:
                flash(
                    f"Created {ticket_count} ticket{'s' if ticket_count != 1 else ''} "
                    f"({len(plan.rows)} seasonal price{'s' if len(plan.rows) != 1 else ''})."
                )
                return self._reply(saved=True)
        return self._reply(
            plan_rows=plan.rows, errors=plan.errors, warnings=plan.warnings,
            ticket_count=ticket_count,
        )

    # --- several tickets at once -----------------------------------------------

    def _change_prices(self, selected, commit: bool):
        changes, errors = plan_price_change(
            selected, request.form.get("price_mode", ""), request.form.get("price_amount", "")
        )
        if commit and not errors:
            for change in changes:
                change.ticket.price = change.new
            self.session.commit()
            flash(f"Changed the price of {len(changes)} ticket{'s' if len(changes) != 1 else ''}.")
            return self._reply(saved=True)
        return self._reply(price_changes=changes, errors=errors)

    def _change_exhibitions(self, museum, selected):
        mode = request.form.get("exhibition_mode", "")
        wanted = set(request.form.getlist("bulk_exhibition_ids", type=int))
        chosen = [e for e in museum.exhibitions if e.id in wanted]
        if mode not in EXHIBITION_MODES:
            return self._reply(errors=["Choose what to do with the exhibitions."])
        if not chosen or len(chosen) != len(wanted):
            return self._reply(errors=["Pick at least one exhibition of this museum."])
        changed = change_exhibitions(selected, mode, chosen)
        self.session.commit()
        flash(f"Updated the exhibitions of {changed} ticket{'s' if changed != 1 else ''}.")
        return self._reply(saved=True)
