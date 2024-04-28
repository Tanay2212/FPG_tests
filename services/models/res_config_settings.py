# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    service_validity_days = fields.Integer(
        related='company_id.service_validity_days',
        readonly=False)
 
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
