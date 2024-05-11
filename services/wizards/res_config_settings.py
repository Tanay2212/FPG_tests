# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    service_deposit_default_product_id = fields.Many2one(
        related="company_id.service_down_payment_product_id",
        readonly=False,
    )
