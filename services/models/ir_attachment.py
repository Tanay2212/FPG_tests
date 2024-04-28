from odoo import fields, models

class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    service_order_id = fields.Many2one("service.order")