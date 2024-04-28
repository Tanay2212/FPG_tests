# -*- coding: utf-8 -*-

from odoo import _, models, fields, api
from odoo.tools import format_date


class Equipment(models.Model):
    _name = "equipment.equipment"

    name = fields.Char(compute="_compute_name", string="Name")
    serial = fields.Char(string="Serial")
    year = fields.Integer(string="Year")
    manufacturer = fields.Char(string="Manufacturer")
    model = fields.Char(string="Model")
    sub_model = fields.Char(string="Sub-Model")

    @api.depends("serial", "year", "manufacturer", "model")
    def _compute_name(self):
        for eq in self:
            eq.name = str(eq.id) + ": " + str(eq.serial or "") + " " + str(eq.year or "") + " " + str(eq.manufacturer or "") + " " + str(eq.model or "")
