# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
from lxml import etree

_logger = logging.getLogger(__name__)

MODEL_DOMAIN = """[
        ('state', '=', 'base'),
        ('transient', '=', False),
        '!',
        '|',
        '|',
        '|',
        '|',
        '|',
        '|',
        '|',
        ('model', '=ilike', 'res.%'),
        ('model', '=ilike', 'ir.%'),
        ('model', '=ilike', 'odoo.workflow%'),
        ('model', '=ilike', 'bus.%'),
        ('model', '=ilike', 'base.%'),
        ('model', '=ilike', 'base_%'),
        ('model', '=', 'base'),
        ('model', '=', '_unknown'),
    ]"""

template_data = """
<data>
    %(arch_header)s
    %(arch_fields)s
</data> """

template_header = """
    <xpath expr="//header" position="inside">
        %(arch_links)s
        %(arch_buttons)s
        %(arch_logs)s
        %(arch_statusbar)s
    </xpath> """

template_no_header = """
    <xpath expr="//form/*" position="before">
        <header>
            %(arch_links)s
            %(arch_buttons)s
            %(arch_logs)s
            %(arch_statusbar)s
        </header>
    </xpath> """

template_link = """
        <button name="btn_trigger_link" string="%(btn_name)s"
              context="{'link_id':%(link_id)d, 'active_model':'%(active_model)s'}"
              class="%(btn_class)s" icon="%(btn_icon)s" groups="%(btn_groups)s"
              invisible="%(btn_invisible)s"
              type="object"/> """

template_button = """
        <button name="btn_exec_action" string="%(btn_name)s"
              context="{'btn_key':'%(btn_key)s', 'active_model':'%(active_model)s'}"
              class="%(btn_class)s" icon="%(btn_icon)s" groups="%(btn_groups)s"
              invisible="%(btn_invisible)s"
              type="object"/> """

template_logs = """
        <button name="btn_exec_logs_action" string="" icon="fa-code-fork" type="object"/> """

template_statusbar = """
        <field name="x_approve_user_ids" widget="many2many_tags" invisible="1"/>
        <field name="x_notice_user_ids" widget="many2many_tags" invisible="1"/>
        <field name="x_stage_id" widget="statusbar_duration_workflow" options="{'fold_field': 'is_fold'}"/> """

template_field = """
    <xpath expr="//field[@name='%(field_name)s']" position="attributes">
        <attribute name="invisible">%(domain_invisible)s</attribute>
        <attribute name="readonly">%(domain_readonly)s</attribute>
        <attribute name="required">%(domain_required)s</attribute>
    </xpath> """


class OdooWorkflow(models.Model):
    _name = 'odoo.workflow'
    _description = 'Workflow'

    name = fields.Char(string='Name', help="Give workflow a name.")
    model_id = fields.Many2one('ir.model', string='Model', domain=MODEL_DOMAIN, ondelete="cascade",
                               help="Enter business model you would like to modify its workflow.")
    res_model = fields.Char(related='model_id.model', readonly=True, string='Model')
    view_id = fields.Many2one('ir.ui.view', string='View')
    inherit_view_id = fields.Many2one('ir.ui.view', string='Inherit View', readonly=True)
    stage_field_id = fields.Many2one('ir.model.fields', string='Stage Field')
    duration_tracking_field_id = fields.Many2one('ir.model.fields', string='Duration Tracking Field')
    approve_users_field_id = fields.Many2one('ir.model.fields', string='Approve Users Field')
    notice_users_field_id = fields.Many2one('ir.model.fields', string='Notice Users Field')
    node_ids = fields.One2many('odoo.workflow.node', 'workflow_id', string='Nodes')
    link_ids = fields.One2many('odoo.workflow.link', 'workflow_id', string='Links')
    timeout_ids = fields.One2many('odoo.workflow.timeout', 'workflow_id', string='Timeout')

    _sql_constraints = [
        ('uniq_name', 'unique(name)', _("Workflow name must be unique.")),
        ('uniq_model', 'unique(model_id)', _("Model must be unique.")),
    ]

    @api.constrains('node_ids')
    def validate_nodes(self):
        for rec in self:
            # Must have one flow start node
            res = rec.node_ids.search_count([
                ('workflow_id', '=', rec.id),
                ('flow_start', '=', True),
            ])
            if res > 1:
                raise ValidationError(_("Workflow must have only one start node."))

    def unlink(self):
        for rec in self:
            if rec.inherit_view_id:
                raise ValidationError(_("Unable to delete records. Please first cancel the workflow deployment."))
        return super(OdooWorkflow, self).unlink()

    def action_odoo_workflow_diagram(self):
        self.ensure_one()
        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'view_mode': 'diagram_plus',
            'res_model': 'odoo.workflow',
            'res_id': self.id,
            'context': self.env.context
        }

    def btn_reload_workflow(self):
        self._remove_inherit_view()
        # self._remove_x_field()

        self._add_x_field()
        self._create_inherit_view()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _add_x_field(self):
        self._add_stage_field()
        self._add_duration_tracking_field()
        self._add_approve_users_field()
        self._add_notice_users_field()

    def _add_approve_users_field(self):
        field_id = self.env['ir.model.fields'].search([('name', '=', 'x_approve_user_ids'),
                                                       ('model_id', '=', self.model_id.id)])
        field_data = {
            'name': 'x_approve_user_ids',
            'field_description': 'Approve Users',
            'model': self.res_model,
            'model_id': self.model_id.id,
            'relation': 'res.users',
            'relation_table': 'odoo_workflow_' + self.res_model.replace('.', '_') + '_approve_users_rel',
            'column1': 'approve_id',
            'column2': 'res_users_id',
            'ttype': 'many2many',
            'tracking': True
        }
        if field_id:
            field_id.write(field_data)
        else:
            field_id = self.env['ir.model.fields'].create(field_data)
        self.approve_users_field_id = field_id

    def _add_notice_users_field(self):
        field_id = self.env['ir.model.fields'].search([('name', '=', 'x_notice_user_ids'),
                                                       ('model_id', '=', self.model_id.id)])
        field_data = {
            'name': 'x_notice_user_ids',
            'field_description': 'Notice Users',
            'model': self.res_model,
            'model_id': self.model_id.id,
            'relation': 'res.users',
            'relation_table': 'odoo_workflow_' + self.res_model.replace('.', '_') + '_notice_users_rel',
            'column1': 'notice_id',
            'column2': 'res_users_id',
            'ttype': 'many2many',
            'tracking': True
        }
        if field_id:
            field_id.write(field_data)
        else:
            field_id = self.env['ir.model.fields'].create(field_data)
        self.notice_users_field_id = field_id

    def _add_stage_field(self):
        field_id = self.env['ir.model.fields'].search([('name', '=', 'x_stage_id'),
                                                       ('model_id', '=', self.model_id.id)])
        field_data = {
            'name': 'x_stage_id',
            'field_description': 'Stage',
            'model': self.res_model,
            'model_id': self.model_id.id,
            'relation': 'odoo.workflow.node',
            'ttype': 'many2one',
            'tracking': True,
            'domain': '[("model_id", "=", %d)]' % self.model_id.id
        }
        if field_id:
            field_id.write(field_data)
        else:
            field_id = self.env['ir.model.fields'].create(field_data)
        self.stage_field_id = field_id

    def _add_duration_tracking_field(self):
        field_id = self.env['ir.model.fields'].search([('name', '=', 'x_duration_tracking'),
                                                       ('model_id', '=', self.model_id.id)])
        field_data = {
            'name': 'x_duration_tracking',
            'field_description': 'Duration Tracking',
            'model': self.res_model,
            'model_id': self.model_id.id,
            'ttype': 'json',
            'store': False,
            'compute': "for r in self: " +
                       "r['x_duration_tracking'] = self.env['odoo.workflow.logs'].get_duration_tracking(r._name, r.id)"
        }
        if field_id:
            field_id.write(field_data)
        else:
            field_id = self.env['ir.model.fields'].create(field_data)
        self.duration_tracking_field_id = field_id

    def _get_arch_links(self):
        links = self.env['odoo.workflow.link'].search([('workflow_id', '=', self.id)])

        def _get_groups_string(node):
            if node.approve_type == 'groups' and node.approve_group_ids:
                external_ids = node.approve_group_ids._get_external_ids()
                groups = [external_ids[external][0] for external in external_ids]
                return ','.join(groups)
            else:
                return ''

        def _get_invisible_string(link):
            invisible_string = "x_stage_id != " + str(link.node_from.id)
            invisible_string = invisible_string + " or not (not x_approve_user_ids or uid in x_approve_user_ids)"

            if link.expression:
                invisible_string = invisible_string + " or not (" + str(link.expression) + ")"
            return invisible_string

        arch_links = ''
        for link in links:
            # Add Button to View
            arch_link = template_link % {
                'btn_name': link.name,
                'link_id': link.id,
                'active_model': self.res_model,
                'btn_class': 'oe_highlight',
                'btn_icon': '',
                'btn_invisible': _get_invisible_string(link),
                'btn_groups': '',
            }
            arch_links = arch_links + arch_link
        return arch_links

    def _get_arch_buttons(self):
        buttons = self.env['odoo.workflow.node.button'].search([('workflow_id', '=', self.id)])

        def _get_groups_string(group_ids):
            if group_ids:
                external_ids = group_ids._get_external_ids()
                groups = [external_ids[external][0] for external in external_ids]
                return ','.join(groups)
            else:
                return ''

        def _get_invisible_string(button):
            invisible_string = "x_stage_id != " + str(button.node_id.id)
            invisible_string = invisible_string + " or not (not x_approve_user_ids or uid in x_approve_user_ids)"
            if button.user_ids:
                invisible_string = invisible_string + " or uid not in " + str([user.id for user in button.user_ids])
            if button.expression:
                invisible_string = invisible_string + " or not (" + str(button.expression) + ")"
            return invisible_string

        arch_buttons = ''
        for button in buttons:
            # Add Button to View
            arch_button = template_button % {
                'btn_name': button.name,
                'btn_key': button.btn_key,
                'active_model': self.res_model,
                'btn_class': 'oe_highlight' if button.is_highlight else '',
                'btn_icon': button.icon if button.has_icon else '',
                'btn_invisible': _get_invisible_string(button),
                'btn_groups': _get_groups_string(button.group_ids),
            }

            arch_buttons = arch_buttons + arch_button
        return arch_buttons

    def _get_arch_statusbar(self):
        return template_statusbar

    def _get_arch_fields(self, arch):
        arch_fields = ''
        for xpath_field in etree.fromstring(arch).xpath("//field"):
            xpath_field = xpath_field.attrib.get('name')
            arr_readonly = []
            arr_required = []
            arr_invisible = []
            for node in self.node_ids:
                for field in node.field_ids:
                    if field.field_id.name == xpath_field:
                        if field.readonly:
                            arr_readonly.append(node.id)
                        if field.required:
                            arr_required.append(node.id)
                        if field.invisible:
                            arr_invisible.append(node.id)
            if not (arr_readonly or arr_required or arr_invisible):
                continue
            arch_field = template_field % {
                'field_name': xpath_field,
                'domain_readonly': 'x_stage_id in ' + str(arr_readonly) if arr_readonly else '',
                'domain_required': 'x_stage_id in ' + str(arr_required) if arr_required else '',
                'domain_invisible': 'x_stage_id in ' + str(arr_invisible) if arr_invisible else ''
            }
            arch_fields = arch_fields + arch_field

        return arch_fields

    def _create_inherit_view(self):
        if not self.inherit_view_id:
            arch_links = self._get_arch_links()
            arch_buttons = self._get_arch_buttons()
            arch_logs = template_logs
            arch_statusbar = self._get_arch_statusbar()
            arch_fields = self._get_arch_fields(self.view_id.arch)

            if '<header>' in self.view_id.arch:
                arch_header = template_header % {'arch_buttons': arch_buttons,
                                                 'arch_links': arch_links,
                                                 'arch_logs': arch_logs,
                                                 'arch_statusbar': arch_statusbar}
            else:
                arch_header = template_no_header % {'arch_buttons': arch_buttons,
                                                    'arch_links': arch_links,
                                                    'arch_logs': arch_logs,
                                                    'arch_statusbar': arch_statusbar}

            arch = template_data % {
                'arch_header': arch_header,
                'arch_fields': arch_fields,
            }

            priority = max(self.view_id.inherit_children_ids.mapped("priority"), default=0) + 10
            self.inherit_view_id = self.env['ir.ui.view'].create({
                'type': self.view_id.type,
                'model': self.view_id.model,
                'inherit_id': self.view_id.id,
                'mode': 'extension',
                'priority': priority,
                'arch': arch,
                'name': self.view_id.name + '_workflow_inherit',
            })

    def btn_cancel_workflow(self):
        self._remove_inherit_view()
        self._remove_x_field()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _remove_x_field(self):
        self._remove_stage_field()
        self._remove_duration_tracking_field()
        self._remove_approve_users_field()
        self._remove_notice_users_field()

    def _remove_stage_field(self):
        self.stage_field_id.unlink()

    def _remove_duration_tracking_field(self):
        self.duration_tracking_field_id.unlink()

    def _remove_approve_users_field(self):
        self.approve_users_field_id.unlink()

    def _remove_notice_users_field(self):
        self.notice_users_field_id.unlink()

    def _remove_inherit_view(self):
        self.inherit_view_id.unlink()

    @api.model
    def get_default_stage_id(self, model_name):
        default_value = ''
        model = self.sudo().search([('res_model', '=', model_name)], limit=1)
        for node in model.node_ids:
            if node.flow_start:
                default_value = node
        return default_value
