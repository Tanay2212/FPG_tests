# -*- coding: utf-8 -*-
from odoo import _, models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    service_down_payment_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Deposit Product",
        domain=[
            ("type", "=", "service"),
            ("service_invoice_policy", "=", "order"),
        ],
        help="Default product used for down payments",
        check_company=True,
    )
    service_validity_days = fields.Integer(
        string="Default Quotation Validity",
        default=30,
        help="Days between quotation proposal and expiration."
        " 0 days means automatic expiration is disabled",
    )

    service_order_template_id = fields.Many2one(
        "service.order.template",
        string="Default Service Template",
        domain="['|', ('company_id', '=', False), ('company_id', '=', id)]",
        check_company=True,
    )

    service_discount_product_id = fields.Many2one(
        comodel_name='product.product',
        string="Discount Product",
        domain=[
            ('type', '=', 'service'),
            ('invoice_policy', '=', 'order'),
        ],
        help="Default product used for discounts",
        check_company=True,
    )
