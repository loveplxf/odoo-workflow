# -*- coding: utf-8 -*-
{
    'name': "Odoo Dynamic Workflow",

    'summary': """
        Odoo Dynamic Workflow""",

    'description': """
        Odoo Dynamic Workflow
    """,

    'author': "Hubin",
    'website': "https://www.faway.vip",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Productivity',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crnd_web_diagram_plus', 'hr'],
    'sequence': 1,

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/odoo_workflow_view.xml',
        'views/odoo_workflow_link_view.xml',
        'views/odoo_workflow_timeout_view.xml',
        'views/odoo_workflow_logs_view.xml',
        'views/odoo_workflow_node_view.xml',
        'views/odoo_workflow_node_button_view.xml',
        'views/odoo_workflow_node_field_view.xml',
        'views/menu.xml',
        'wizard/odoo_workflow_optional.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_dynamic_workflow/static/src/**/*',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
}
