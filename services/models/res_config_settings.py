# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    service_validity_days = fields.Integer(
        related='company_id.service_validity_days',
        readonly=False)

    service_deposit_default_product_id = fields.Many2one(
        related="company_id.service_down_payment_product_id",
        readonly=False,
    )

    company_service_template_id = fields.Many2one(
        related="company_id.service_order_template_id", string="Default Template", readonly=False,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    group_service_order_template = fields.Boolean(
        "Order Templates", implied_group='services.group_service_order_template')
    
    group_discount_per_service_line = fields.Boolean("Discounts", implied_group='services.group_discount_per_service_line')

    group_service_pricelist = fields.Boolean("Advanced Pricelists",
        implied_group='services.group_service_pricelist',
        help="""Allows to manage different prices based on rules per category of customers.
                Example: 10% for retailers, promotion of 5 EUR on this product, etc.""")
    
    group_uom_service = fields.Boolean("Units of Measure", implied_group='services.group_uom')

    group_stock_packaging_service = fields.Boolean('Product Packagings',
        implied_group='services.group_stock_packaging')
    
    default_invoice_policy_service = fields.Selection(
        selection=[
            ('order', "Invoice what is ordered"),
            ('delivery', "Invoice what is delivered")
        ],
        string="Invoicing Policy",
        default='order',
        default_model='product.template')
    
    automatic_invoice_service = fields.Boolean(
        string="Automatic Invoice",
        help="The invoice is generated automatically and available in the customer portal when the "
             "transaction is confirmed by the payment provider.\nThe invoice is marked as paid and "
             "the payment is registered in the payment journal defined in the configuration of the "
             "payment provider.\nThis mode is advised if you issue the final invoice at the order "
             "and not after the delivery.",
        config_parameter='services.automatic_invoice',
    )
    
    @api.onchange('service_validity_days')
    def _onchange_service_validity_days(self):
        if self.service_validity_days < 0:
            self.service_validity_days = self.env['res.company'].default_get(
                ['service_validity_days']
            )['service_validity_days']
            return {
                'warning': {
                    'title': _("Warning"),
                    'message': _("Service Validity is required and must be greater or equal to 0."),
                },
            }

    def set_values(self):
        if self.company_service_template_id:
            self.company_service_template_id = False
        companies = self.env['res.company'].sudo().search([
            ('service_order_template_id', '!=', False)
        ])
        if companies:
            companies.service_order_template_id = False
        super().set_values()
        if self.default_invoice_policy_service != 'order':
            self.env['ir.config_parameter'].set_param('services.automatic_invoice', False)

        send_invoice_cron = self.env.ref('sale.send_invoice_cron', raise_if_not_found=False)
        if send_invoice_cron and send_invoice_cron.active != self.automatic_invoice_service:
            send_invoice_cron.active = self.automatic_invoice_service
    
    
        

