# -*- coding: utf-8 -*-

from odoo import _, models, fields, api
from odoo.tools import format_date


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    service_order_line = fields.Many2one("service.order.line")
    service_order_line = fields.Many2one('service.order.line', string='Service Order Item', domain=[('qty_delivered_method', '=', 'analytic')])
