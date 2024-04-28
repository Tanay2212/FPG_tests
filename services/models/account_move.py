from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = "account.move"

    equipment_id = fields.Many2one("equipment.equipment", string="Equipment", store=True)
    equipment_name = fields.Char(store=True)
    equipment_serial = fields.Char(store=True)
    customer_complaint = fields.Text(store=True)
    date_damage = fields.Datetime("Date of Damage", store=True)
    complaint_number = fields.Char("Complaint No.", store=True)
    warranty_number = fields.Char("Warranty No.", store=True)
    pre_payment = fields.Monetary(currency_field="currency_id", store=True)
    billing_customer = fields.Many2one(
        comodel_name='res.partner', string="Bill to Customer", store=True
    )
    service_order_count = fields.Integer(compute="_compute_origin_service_count", string='Service Order Count')

    @api.depends('line_ids.service_line_ids')
    def _compute_origin_service_count(self):
        for move in self:
            move.service_order_count = len(move.line_ids.service_line_ids.order_id)

    def _get_mail_template(self):
        if self.invoice_line_ids and self.invoice_line_ids.service_line_ids:
            return "services.services_email_template_edi_invoice"
        return super(AccountMove, self)._get_mail_template()
    
    def open_attachments(self):
        self.ensure_one()
        attachments = self.line_ids.service_line_ids[:1].order_id.service_attachment_ids
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "base.action_attachment"
        )
        action['domain'] = [('id', 'in', attachments.ids)]
        if len(attachments) == 1:
            action['res_id'] = attachments.id
        elif len(attachments) < 1:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_view_source_service_orders(self):
        self.ensure_one()
        source_orders = self.line_ids.service_line_ids.order_id
        result = self.env['ir.actions.act_window']._for_xml_id('services.action_service_orders')
        if len(source_orders) > 1:
            result['domain'] = [('id', 'in', source_orders.ids)]
        elif len(source_orders) == 1:
            result['views'] = [(self.env.ref('services.view_service_order_form', False).id, 'form')]
            result['res_id'] = source_orders.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
        
