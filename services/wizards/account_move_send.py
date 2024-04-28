# -*- coding: utf-8 -*-
from markupsafe import Markup
from werkzeug.urls import url_encode

from odoo import _, api, fields, models, modules, tools, Command
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang


class AccountMoveSend(models.TransientModel):
    _inherit = 'account.move.send'

    def action_send_and_print(self, force_synchronous=False, allow_fallback_pdf=False, **kwargs):
        return super(AccountMoveSend, self.with_context(send_and_print=True)).action_send_and_print(force_synchronous=force_synchronous, allow_fallback_pdf=allow_fallback_pdf, **kwargs)
        # return super().action_send_and_print(force_synchronous=force_synchronous, allow_fallback_pdf=allow_fallback_pdf, **kwargs)

    def _get_default_mail_attachments_widget(self, move, mail_template):
        res = super()._get_default_mail_attachments_widget(move=move, mail_template=mail_template)
        attachments = []
        if not self._context.get("send_and_print"):
            active_id = self.env.context.get("active_id", False)
            account_move = self.env["account.move"].browse(active_id)
            service_order = account_move.line_ids.service_line_ids[:1].order_id
            attachments = service_order.service_attachment_ids.read(["id", "name", "mimetype"])
        return res + attachments
    
    def _get_default_mail_partner_ids(self, move, mail_template, mail_lang):
        service_order = move.line_ids.service_line_ids[:1].order_id
        return service_order.billing_customer

   