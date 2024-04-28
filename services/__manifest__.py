# -*- coding: utf-8 -*-
{
    'name': "Services Orders",
    'description': """
    Service Orders
    """,
    'author': "Tanay Goyal",
    'website': "",
    'category': 'Customizations',
    'sequence': 1,
    'version': '17.0.1.0.0',
    'depends': ["mail", "portal", "web", "product", "analytic", "account", "sales_team"],
    'data': [
        'security/ir.model.access.csv',
        'wizards/service_make_invoice_advance.xml',
        'data/ir_sequence.xml',
        'reports/ir_action_report_template.xml',
        'reports/ir_action_report.xml',
        'reports/account_invoice.xml',
        'views/service_orders_views.xml',
        'views/mail_template_views.xml',
        'views/service_portal_template.xml',
        'views/equipments_views.xml',
        'wizards/account_move_send_views.xml',
        'views/account_move_views.xml',
        'views/product_views.xml',
        'views/service_menus.xml',
        'data/mail_template_data.xml',
        'data/ir_config_parameter.xml',
    ],
    "assets": {
        "web.assets_frontend": [
            "services/static/src/core/**/*",
            "services/static/src/js/service_name_and_signature.js",
        ],

        "web._assets_core": [
            "services/static/src/core/**/*",
        ],
    },
    'application': True,
    'installable': True,
}

