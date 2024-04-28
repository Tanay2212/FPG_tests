from odoo import fields, models

class ServiceOrderAttachment(models.Model):
    _name = "service.order.attachment"
    _description = "Service Order Attachments"  

    service_order_id = fields.Many2one("service.order")
    attachment_ids = fields.One2many("ir.attachment", inverse_name="service_order_attachment_id")