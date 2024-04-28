# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ServiceOrderTemplate(models.Model):
    _name = "service.order.template"
    _description = "Service Template"

    active = fields.Boolean(
        default=True,
        help="If unchecked, it will allow you to hide the order template without removing it.")
    
    company_id = fields.Many2one(comodel_name='res.company')

    name = fields.Char(string="Order Template", required=True)
    note = fields.Html(string="Terms and conditions", translate=True)

    mail_template_id = fields.Many2one(
        comodel_name='mail.template',
        string="Confirmation Mail",
        domain=[('model', '=', 'service.order')],
        help="This e-mail template will be sent on confirmation. Leave empty to send nothing.")
    number_of_days = fields.Integer(
        string="Order Duration",
        help="Number of days for the validity date computation of the order")

    require_signature = fields.Boolean(
        string="Online Signature",
        compute='_compute_require_signature',
        store=True, readonly=False,
        help="Request a online signature to the customer in order to confirm orders automatically.")
    require_payment = fields.Boolean(
        string="Online Payment",
        compute='_compute_require_payment',
        store=True, readonly=False,
        help="Request an online payment to the customer in order to confirm orders automatically.")
    prepayment_percent = fields.Float(
        string="Prepayment percentage",
        compute="_compute_prepayment_percent",
        store=True, readonly=False,
        help="The percentage of the amount needed to be paid to confirm orders.")

    service_order_template_line_ids = fields.One2many(
        comodel_name='service.order.template.line', inverse_name='service_order_template_id',
        string="Lines",
        copy=True)
    service_order_template_option_ids = fields.One2many(
        comodel_name='service.order.template.option', inverse_name='service_order_template_id',
        string="Optional Products",
        copy=True)
    journal_id = fields.Many2one(
        'account.journal', string="Invoicing Journal",
        domain=[('type', '=', 'service')], company_dependent=True, check_company=True,
        help="If set, SO with this template will invoice in this journal; "
             "otherwise the service journal with the lowest sequence is used.")

    #=== COMPUTE METHODS ===#

    @api.depends('company_id')
    def _compute_require_signature(self):
        for order in self:
            order.require_signature = True
            # order.require_signature = (order.company_id or order.env.company).portal_confirmation_sign

    @api.depends('company_id')
    def _compute_require_payment(self):
        for order in self:
            order.require_payment = False
            # order.require_payment = (order.company_id or order.env.company).portal_confirmation_pay

    @api.depends('company_id', 'require_payment')
    def _compute_prepayment_percent(self):
        for template in self:
            template.prepayment_percent = (
                template.company_id or template.env.company
            ).prepayment_percent

    #=== ONCHANGE METHODS ===#

    @api.onchange('prepayment_percent')
    def _onchange_prepayment_percent(self):
        for template in self:
            if not template.prepayment_percent:
                template.require_payment = False

    #=== CONSTRAINT METHODS ===#

    @api.constrains('company_id', 'service_order_template_line_ids', 'service_order_template_option_ids')
    def _check_company_id(self):
        for template in self:
            companies = template.mapped('service_order_template_line_ids.product_id.company_id') | template.mapped('service_order_template_option_ids.product_id.company_id')
            if len(companies) > 1:
                raise ValidationError(_("Your template cannot contain products from multiple companies."))
            elif companies and companies != template.company_id:
                raise ValidationError(_(
                    "Your template contains products from company %(product_company)s whereas your template belongs to company %(template_company)s. \n Please change the company of your template or remove the products from other companies.",
                    product_company=', '.join(companies.mapped('display_name')),
                    template_company=template.company_id.display_name,
                ))

    @api.constrains('prepayment_percent')
    def _check_prepayment_percent(self):
        for template in self:
            if template.require_payment and not (0 < template.prepayment_percent <= 1.0):
                raise ValidationError(_("Prepayment percentage must be a valid percentage."))

    #=== CRUD METHODS ===#

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._update_product_translations()
        return records

    def write(self, vals):
        if 'active' in vals and not vals.get('active'):
            companies = self.env['res.company'].sudo().search([('service_order_template_id', 'in', self.ids)])
            companies.service_order_template_id = None
        result = super().write(vals)
        self._update_product_translations()
        return result

    def _update_product_translations(self):
        languages = self.env['res.lang'].search([('active', '=', 'true')])
        for lang in languages:
            for line in self.service_order_template_line_ids:
                if line.name == line.product_id.get_product_multiline_description_sale():
                    line.with_context(lang=lang.code).name = line.product_id.with_context(lang=lang.code).get_product_multiline_description_sale()
            for option in self.service_order_template_option_ids:
                if option.name == option.product_id.get_product_multiline_description_sale():
                    option.with_context(lang=lang.code).name = option.product_id.with_context(lang=lang.code).get_product_multiline_description_sale()

class ServiceOrderTemplateLine(models.Model):
    _name = "service.order.template.line"
    _description = "Order Template Line"
    _order = 'service_order_template_id, sequence, id'

    _sql_constraints = [
        ('accountable_product_id_required',
            "CHECK(display_type IS NOT NULL OR (product_id IS NOT NULL AND product_uom_id IS NOT NULL))",
            "Missing required product and UoM on accountable sale quote line."),

        ('non_accountable_fields_null',
            "CHECK(display_type IS NULL OR (product_id IS NULL AND product_uom_qty = 0 AND product_uom_id IS NULL))",
            "Forbidden product, quantity and UoM on non-accountable sale quote line"),
    ]

    service_order_template_id = fields.Many2one(
        comodel_name='service.order.template',
        string='Order Template Reference',
        index=True, required=True,
        ondelete='cascade')
    sequence = fields.Integer(
        string="Sequence",
        help="Gives the sequence order when displaying a list of service quote lines.",
        default=10)

    company_id = fields.Many2one(
        related='service_order_template_id.company_id', store=True, index=True)

    product_id = fields.Many2one(
        comodel_name='product.product',
        check_company=True,
        domain=lambda self: self._product_id_domain())

    name = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False, precompute=True,
        required=True,
        translate=True)

    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_product_uom_id',
        store=True, readonly=False, precompute=True,
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_uom_qty = fields.Float(
        string='Quantity',
        required=True,
        digits='Product Unit of Measure',
        default=1)

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False)

    #=== COMPUTE METHODS ===#

    @api.depends('product_id')
    def _compute_name(self):
        for option in self:
            if not option.product_id:
                continue
            option.name = option.product_id.get_product_multiline_description_sale()

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for option in self:
            option.product_uom_id = option.product_id.uom_id

    #=== CRUD METHODS ===#

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('display_type', self.default_get(['display_type'])['display_type']):
                vals.update(product_id=False, product_uom_qty=0, product_uom_id=False)
        return super().create(vals_list)

    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_("You cannot change the type of a sale quote line. Instead you should delete the current line and create a new line of the proper type."))
        return super().write(values)

    #=== BUSINESS METHODS ===#

    @api.model
    def _product_id_domain(self):
        """ Returns the domain of the products that can be added to the template. """
        return [('sale_ok', '=', True)]

    def _prepare_order_line_values(self):
        """ Give the values to create the corresponding order line.

        :return: `service.order.line` create values
        :rtype: dict
        """
        self.ensure_one()
        return {
            'display_type': self.display_type,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_uom_qty,
            'product_uom': self.product_uom_id.id,
            'sequence': self.sequence,
        }

class ServiceOrderTemplateOption(models.Model):
    _name = "service.order.template.option"
    _description = "Order Template Option"
    _check_company_auto = True

    service_order_template_id = fields.Many2one(
        comodel_name='service.order.template',
        string="Order Template Reference",
        index=True, required=True,
        ondelete='cascade')

    company_id = fields.Many2one(
        related='service_order_template_id.company_id', store=True, index=True)

    product_id = fields.Many2one(
        comodel_name='product.product',
        required=True, check_company=True,
        domain=lambda self: self._product_id_domain())

    name = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False, precompute=True,
        required=True, translate=True)

    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_uom_id',
        store=True, readonly=False,
        required=True, precompute=True,
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    quantity = fields.Float(
        string="Quantity",
        required=True,
        digits='Product Unit of Measure',
        default=1)

    #=== COMPUTE METHODS ===#

    @api.depends('product_id')
    def _compute_name(self):
        for option in self:
            if not option.product_id:
                continue
            option.name = option.product_id.get_product_multiline_description_sale()

    @api.depends('product_id')
    def _compute_uom_id(self):
        for option in self:
            option.uom_id = option.product_id.uom_id

    #=== BUSINESS METHODS ===#

    @api.model
    def _product_id_domain(self):
        """Returns the domain of the products that can be added as a template option."""
        return [('sale_ok', '=', True)]

    def _prepare_option_line_values(self):
        """ Give the values to create the corresponding option line.

        :return: `service.order.option` create values
        :rtype: dict
        """
        self.ensure_one()
        return {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': self.quantity,
            'uom_id': self.uom_id.id,
        }

