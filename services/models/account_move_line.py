from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    service_line_ids = fields.Many2many(
        'service.order.line',
        'service_order_line_invoice_rel',
        'invoice_line_id', 'order_line_id',
        string='Service Order Lines', readonly=True, copy=False)

    is_downpayment = fields.Boolean()