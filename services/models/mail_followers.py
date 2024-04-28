    # -*- coding: utf-8 -*-
from odoo import _, api, fields, models, modules, tools, Command


class MailFollowers(models.Model):
    _inherit = 'mail.followers'

    def _get_recipient_data(self, records, message_type, subtype_id, pids=None):
        """ Private method allowing to fetch recipients data based on a subtype.
        Purpose of this method is to fetch all data necessary to notify recipients
        in a single query. It fetches data from

         * followers (partners and channels) of records that follow the given
           subtype if records and subtype are set;
         * partners if pids is given;

        :param records: fetch data from followers of ``records`` that follow
          ``subtype_id``;
        :param str message_type: mail.message.message_type in order to allow custom
          behavior depending on it (SMS for example);
        :param int subtype_id: mail.message.subtype to check against followers;
        :param pids: additional set of partner IDs from which to fetch recipient
          data independently from following status;

        :return dict: recipients data based on record.ids if given, else a generic
          '0' key to keep a dict-like return format. Each item is a dict based on
          recipients partner ids formatted like
          {'active': whether partner is active;
           'id': res.partner ID;
           'is_follower': True if linked to a record and if partner is a follower;
           'lang': lang of the partner;
           'groups': groups of the partner's user. If several users exist preference
                is given to internal user, then share users. In case of multiples
                users of same kind groups are unioned;
            'notif': notification type ('inbox' or 'email'). Overrides may change
                this value (e.g. 'sms' in sms module);
            'share': if partner is a customer (no user or share user);
            'ushare': if partner has users, whether all are shared (public or portal);
            'type': summary of partner 'usage' (portal, customer, internal user);
          }
        """
        self.env['mail.followers'].flush_model(['partner_id', 'subtype_ids'])
        self.env['mail.message.subtype'].flush_model(['internal'])
        self.env['res.users'].flush_model(['notification_type', 'active', 'partner_id', 'groups_id'])
        self.env['res.partner'].flush_model(['active', 'partner_share'])
        self.env['res.groups'].flush_model(['users'])
        # if we have records and a subtype: we have to fetch followers, unless being
        # in user notification mode (contact only pids)
        invoice_records = records.filtered(lambda mv: mv._name == "account.move")
        records -= invoice_records

        if message_type != 'user_notification' and records and subtype_id and pids and invoice_records:
            query = """
    WITH sub_followers AS (
        SELECT fol.partner_id AS pid,
               fol.id AS fid,
               fol.res_id AS res_id,
               TRUE as is_follower,
               COALESCE(subrel.follow, FALSE) AS subtype_follower,
               COALESCE(subrel.internal, FALSE) AS internal
          FROM mail_followers fol
     LEFT JOIN LATERAL (
            SELECT TRUE AS follow,
                   subtype.internal AS internal
              FROM mail_followers_mail_message_subtype_rel m
         LEFT JOIN mail_message_subtype subtype ON subtype.id = m.mail_message_subtype_id
             WHERE m.mail_followers_id = fol.id AND m.mail_message_subtype_id = %s
            ) subrel ON TRUE
         WHERE fol.res_model = %s
               AND fol.res_id IN %s
               AND fol.partner_id IN %s

     UNION ALL

        SELECT res_partner.id AS pid,
               0 AS fid,
               0 AS res_id,
               FALSE as is_follower,
               FALSE as subtype_follower,
               FALSE as internal
          FROM res_partner
         WHERE res_partner.id = ANY(%s)
    )
    SELECT partner.id as pid,
           partner.active as active,
           partner.lang as lang,
           partner.partner_share as pshare,
           sub_user.uid as uid,
           COALESCE(sub_user.share, FALSE) as ushare,
           COALESCE(sub_user.notification_type, 'email') as notif,
           sub_user.groups as groups,
           sub_followers.res_id as res_id,
           sub_followers.is_follower as _insert_followerslower
      FROM res_partner partner
      JOIN sub_followers ON sub_followers.pid = partner.id
                        AND (sub_followers.internal IS NOT TRUE OR partner.partner_share IS NOT TRUE)
 LEFT JOIN LATERAL (
        SELECT users.id AS uid,
               users.share AS share,
               users.notification_type AS notification_type,
               ARRAY_AGG(groups_rel.gid) FILTER (WHERE groups_rel.gid IS NOT NULL) AS groups
          FROM res_users users
     LEFT JOIN res_groups_users_rel groups_rel ON groups_rel.uid = users.id
         WHERE users.partner_id = partner.id AND users.active
      GROUP BY users.id,
               users.share,
               users.notification_type
      ORDER BY users.share ASC NULLS FIRST, users.id ASC
         FETCH FIRST ROW ONLY
         ) sub_user ON TRUE

     WHERE sub_followers.subtype_follower OR partner.id = ANY(%s)
"""
            params = [subtype_id, invoice_records._name, tuple(invoice_records.ids), tuple(pids or []), list(pids or []), list(pids or [])]
            self.env.cr.execute(query, tuple(params))
            res = self.env.cr.fetchall()
        elif message_type != 'user_notification' and records and subtype_id and not pids:
            query = """
    WITH sub_followers AS (
        SELECT fol.partner_id AS pid,
               fol.id AS fid,
               fol.res_id AS res_id,
               TRUE as is_follower,
               COALESCE(subrel.follow, FALSE) AS subtype_follower,
               COALESCE(subrel.internal, FALSE) AS internal
          FROM mail_followers fol
     LEFT JOIN LATERAL (
            SELECT TRUE AS follow,
                   subtype.internal AS internal
              FROM mail_followers_mail_message_subtype_rel m
         LEFT JOIN mail_message_subtype subtype ON subtype.id = m.mail_message_subtype_id
             WHERE m.mail_followers_id = fol.id AND m.mail_message_subtype_id = %s
            ) subrel ON TRUE
         WHERE fol.res_model = %s
               AND fol.res_id IN %s

     UNION ALL

        SELECT res_partner.id AS pid,
               0 AS fid,
               0 AS res_id,
               FALSE as is_follower,
               FALSE as subtype_follower,
               FALSE as internal
          FROM res_partner
         WHERE res_partner.id = ANY(%s)
    )
    SELECT partner.id as pid,
           partner.active as active,
           partner.lang as lang,
           partner.partner_share as pshare,
           sub_user.uid as uid,
           COALESCE(sub_user.share, FALSE) as ushare,
           COALESCE(sub_user.notification_type, 'email') as notif,
           sub_user.groups as groups,
           sub_followers.res_id as res_id,
           sub_followers.is_follower as _insert_followerslower
      FROM res_partner partner
      JOIN sub_followers ON sub_followers.pid = partner.id
                        AND (sub_followers.internal IS NOT TRUE OR partner.partner_share IS NOT TRUE)
 LEFT JOIN LATERAL (
        SELECT users.id AS uid,
               users.share AS share,
               users.notification_type AS notification_type,
               ARRAY_AGG(groups_rel.gid) FILTER (WHERE groups_rel.gid IS NOT NULL) AS groups
          FROM res_users users
     LEFT JOIN res_groups_users_rel groups_rel ON groups_rel.uid = users.id
         WHERE users.partner_id = partner.id AND users.active
      GROUP BY users.id,
               users.share,
               users.notification_type
      ORDER BY users.share ASC NULLS FIRST, users.id ASC
         FETCH FIRST ROW ONLY
         ) sub_user ON TRUE

     WHERE sub_followers.subtype_follower OR partner.id = ANY(%s)
"""
            params = [subtype_id, records._name, tuple(records.ids), list(pids or []), list(pids or [])]
            self.env.cr.execute(query, tuple(params))
            res = self.env.cr.fetchall()
        # partner_ids and records: no sub query for followers but check for follower status
        elif pids and records:
            params = []
            query = """
    SELECT partner.id as pid,
           partner.active as active,
           partner.lang as lang,
           partner.partner_share as pshare,
           sub_user.uid as uid,
           COALESCE(sub_user.share, FALSE) as ushare,
           COALESCE(sub_user.notification_type, 'email') as notif,
           sub_user.groups as groups,
           ARRAY_AGG(fol.res_id) FILTER (WHERE fol.res_id IS NOT NULL) AS res_ids
      FROM res_partner partner
 LEFT JOIN mail_followers fol ON fol.partner_id = partner.id
                              AND fol.res_model = %s
                              AND fol.res_id IN %s
 LEFT JOIN LATERAL (
        SELECT users.id AS uid,
               users.share AS share,
               users.notification_type AS notification_type,
               ARRAY_AGG(groups_rel.gid) FILTER (WHERE groups_rel.gid IS NOT NULL) AS groups
          FROM res_users users
     LEFT JOIN res_groups_users_rel groups_rel ON groups_rel.uid = users.id
         WHERE users.partner_id = partner.id AND users.active
      GROUP BY users.id,
               users.share,
               users.notification_type
      ORDER BY users.share ASC NULLS FIRST, users.id ASC
         FETCH FIRST ROW ONLY
         ) sub_user ON TRUE

     WHERE partner.id IN %s
  GROUP BY partner.id,
           sub_user.uid,
           sub_user.share,
           sub_user.notification_type,
           sub_user.groups
"""
            params = [records._name, tuple(records.ids), tuple(pids)]
            self.env.cr.execute(query, tuple(params))
            simplified_res = self.env.cr.fetchall()
            # simplified query contains res_ids -> flatten it by making it a list
            # with res_id and add follower status
            res = []
            for item in simplified_res:
                res_ids = item[-1]
                if not res_ids:  # keep res_ids Falsy (global), set as not follower
                    flattened = [list(item) + [False]]
                else:  # generate an entry for each res_id with partner being follower
                    flattened = [list(item[:-1]) + [res_id, True]
                                 for res_id in res_ids]
                res += flattened
        # only partner ids: no follower status involved, fetch only direct recipients information
        elif pids:
            query = """
    SELECT partner.id as pid,
           partner.active as active,
           partner.lang as lang,
           partner.partner_share as pshare,
           sub_user.uid as uid,
           COALESCE(sub_user.share, FALSE) as ushare,
           COALESCE(sub_user.notification_type, 'email') as notif,
           sub_user.groups as groups,
           0 as res_id,
           FALSE as is_follower
      FROM res_partner partner
 LEFT JOIN LATERAL (
        SELECT users.id AS uid,
               users.share AS share,
               users.notification_type AS notification_type,
               ARRAY_AGG(groups_rel.gid) FILTER (WHERE groups_rel.gid IS NOT NULL) AS groups
          FROM res_users users
     LEFT JOIN res_groups_users_rel groups_rel ON groups_rel.uid = users.id
         WHERE users.partner_id = partner.id AND users.active
      GROUP BY users.id,
               users.share,
               users.notification_type
      ORDER BY users.share ASC NULLS FIRST, users.id ASC
         FETCH FIRST ROW ONLY
         ) sub_user ON TRUE

     WHERE partner.id IN %s
  GROUP BY partner.id,
           sub_user.uid,
           sub_user.share,
           sub_user.notification_type,
           sub_user.groups
"""
            params = [tuple(pids)]
            self.env.cr.execute(query, tuple(params))
            res = self.env.cr.fetchall()
        else:
            res = []

        res_ids = records.ids if records else [0]
        doc_infos = dict((res_id, {}) for res_id in res_ids)
        for (partner_id, is_active, lang, pshare, uid, ushare, notif, groups, res_id, is_follower) in res:
            to_update = [res_id] if res_id else res_ids
            for res_id_to_update in to_update:
                # avoid updating already existing information, unnecessary dict update
                if not res_id and partner_id in doc_infos[res_id_to_update]:
                    continue
                follower_data = {
                    'active': is_active,
                    'id': partner_id,
                    'is_follower': is_follower,
                    'lang': lang,
                    'groups': set(groups or []),
                    'notif': notif,
                    'share': pshare,
                    'uid': uid,
                    'ushare': ushare,
                }
                # additional information
                if follower_data['ushare']:  # any type of share user
                    follower_data['type'] = 'portal'
                elif follower_data['share']:  # no user, is share -> customer (partner only)
                    follower_data['type'] = 'customer'
                else:  # has a user not share -> internal user
                    follower_data['type'] = 'user'
                doc_infos[res_id_to_update][partner_id] = follower_data

        return doc_infos