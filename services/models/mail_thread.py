
from odoo import _, models, tools
import itertools


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_get_recipients(self, message, msg_vals, **kwargs):
        """ Compute recipients to notify based on subtype and followers. This
        method returns data structured as expected for ``_notify_recipients``.

        :param record message: <mail.message> record being notified. May be
          void as 'msg_vals' superseeds it;
        :param dict msg_vals: values dict used to create the message, allows to
          skip message usage and spare some queries;

        Kwargs allow to pass various parameters that are used by sub notification
        methods. See those methods for more details about supported parameters.
        Specific kwargs used in this method:

          * ``notify_author``: allows to notify the author, which is False by
            default as we don't want people to receive their own content. It is
            used notably when impersonating partners or having automated
            notifications send by current user, targeting current user;
          * ``skip_existing``: check existing notifications and skip them in order
            to avoid having several notifications / partner as it would make
            constraints crash. This is disabled by default to optimize speed;

        TDE/XDO TODO: flag rdata directly, for example r['notif'] = 'ocn_client'
        and r['needaction']=False and correctly override _notify_get_recipients

        :return list recipients_data: list of recipients information (see
          ``MailFollowers._get_recipient_data()`` for more details) formatted
          like [
          {
            'active': partner.active;
            'id': id of the res.partner being recipient to notify;
            'is_follower': follows the message related document;
            'lang': its lang;
            'groups': res.group IDs if linked to a user;
            'notif': 'inbox', 'email', 'sms' (SMS App);
            'share': is partner a customer (partner.partner_share);
            'type': partner usage ('customer', 'portal', 'user');
            'ushare': are users shared (if users, all users are shared);
          }, {...}]
        """
        msg_sudo = message.sudo()
        # get values from msg_vals or from message if msg_vals doen't exists
        pids = msg_vals.get('partner_ids', []) if msg_vals else msg_sudo.partner_ids.ids
        message_type = msg_vals.get('message_type') if msg_vals else msg_sudo.message_type
        subtype_id = msg_vals.get('subtype_id') if msg_vals else msg_sudo.subtype_id.id
        # is it possible to have record but no subtype_id ?
        recipients_data = []
        res = self.env['mail.followers']._get_recipient_data(self, message_type, subtype_id, pids).get(self.id if self else 0)
        if not res:
            res = self.env['mail.followers']._get_recipient_data(self, message_type, subtype_id, pids).get(0)
        if not res:
            return recipients_data

        # notify author of its own messages, False by default
        notify_author = kwargs.get('notify_author') or self.env.context.get('mail_notify_author')
        real_author_id = False
        if not notify_author:
            if self.env.user.active:
                real_author_id = self.env.user.partner_id.id
            elif msg_vals.get('author_id'):
                real_author_id = msg_vals['author_id']
            else:
                real_author_id = message.author_id.id

        for pid, pdata in res.items():
            if pid and pid == real_author_id:
                continue
            if pdata['active'] is False:
                continue
            recipients_data.append(pdata)

        # avoid double notification (on demand due to additional queries)
        if kwargs.pop('skip_existing', False):
            pids = [r['id'] for r in recipients_data]
            if pids:
                existing_notifications = self.env['mail.notification'].sudo().search([
                    ('res_partner_id', 'in', pids),
                    ('mail_message_id', 'in', message.ids)
                ])
                recipients_data = [
                    r for r in recipients_data
                    if r['id'] not in existing_notifications.res_partner_id.ids
                ]

        return recipients_data
