{
    'name': 'CRnD Web Diagram Plus',
    'category': 'Technical Settings',
    'summary': """
        Odoo Web Diagram view by CRnD.
    """,
    'author': 'Center of Research and Development',
    'support': 'info@crnd.pro',
    'website': 'https://crnd.pro',
    'license': 'LGPL-3',
    'version': '17.0.0.14.0',
    'depends': [
        'web',
    ],
    'assets': {
        'web.assets_backend': [
            'crnd_web_diagram_plus/static/src/scss/diagram_view.scss',
            'crnd_web_diagram_plus/static/lib/js/underscore-umd.js',
            'crnd_web_diagram_plus/static/lib/js/jquery.mousewheel.js',
            'crnd_web_diagram_plus/static/lib/js/raphael-2.0.2/raphael.js',
            'crnd_web_diagram_plus/static/lib/js/vec2.js',
            'crnd_web_diagram_plus/static/lib/js/graph.js',
            'crnd_web_diagram_plus/static/src/js/diagram_arch_parser.js',
            'crnd_web_diagram_plus/static/src/js/diagram_model.js',
            'crnd_web_diagram_plus/static/src/js/diagram_controller.js',
            'crnd_web_diagram_plus/static/src/js/diagram_renderer.js',
            'crnd_web_diagram_plus/static/src/js/diagram_view.js',
            'crnd_web_diagram_plus/static/src/xml/base_diagram.xml',
        ],
        'web.tests_assets': [
            # Add Raphael liberary directly to test suite, because it is not
            # loaded by default.
            'crnd_web_diagram_plus/static/lib/js/jquery.mousewheel.js',
            # Also, use non-minified, patched version of library,
            # because original library will try to use different import
            # mechanics when see 'define' that is defined.
            'crnd_web_diagram_plus/static/lib/js/raphael-2.0.2/raphael.js',
        ],
        'web.qunit_suite_tests': [
            'crnd_web_diagram_plus/static/tests/diagram_tests.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
}
