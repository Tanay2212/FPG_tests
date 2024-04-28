# -*- coding: utf-8 -*-

from odoo import _, models, fields, api
from odoo.tools import format_date


class ProductTemplate(models.Model):
    _inherit = "product.template"

    service_invoice_policy = fields.Selection(
        selection=[
            ('order', "Ordered quantities"),
            ('delivery', "Delivered quantities"),
        ],
        string="Invoicing Policy",
        compute='_compute_service_invoice_policy', store=True, readonly=False, precompute=True,
        help="Ordered Quantity: Invoice quantities ordered by the customer.\n"
             "Delivered Quantity: Invoice quantities delivered to the customer.")

    expense_policy = fields.Selection(
        selection=[
            ('no', "No"),
            ('cost', "At cost"),
            ('sales_price', "Sales price"),
        ],
        string="Re-Invoice Expenses", default='no',
        compute='_compute_expense_policy', store=True, readonly=False,
        help="Validated expenses and vendor bills can be re-invoiced to a customer at its cost or sales price.")
    
    @api.depends('type')
    def _compute_service_invoice_policy(self):
        self.filtered(lambda t: t.type == 'consu' or not t.service_invoice_policy).service_invoice_policy = 'order'

    @api.depends('sale_ok')
    def _compute_expense_policy(self):
        self.filtered(lambda t: not t.sale_ok).expense_policy = 'no'

class ProductAttributeCustomValue(models.Model):
    _inherit = "product.attribute.custom.value"

    service_order_line_id = fields.Many2one("service.order.line")