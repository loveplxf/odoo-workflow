# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date, time, timedelta
import random
import string
import logging

_logger = logging.getLogger(__name__)

CONDITION_CODE_TEMP = """# Available locals:
#  - time, date, datetime, timedelta: Python libraries.
#  - env: Odoo Environement.
#  - model: Model of the record on which the action is triggered.
#  - obj: Record on which the action is triggered if there is one, otherwise None.
#  - user, Current user object.
#  - workflow: Workflow engine.
# if result is False, you can return an action, assign: action = {...}

result = True"""

PYTHON_CODE_TEMP = """# Available locals:
#  - time, date, datetime, timedelta: Python libraries.
#  - env: Odoo Environement.
#  - model: Model of the record on which the action is triggered.
#  - obj: Record on which the action is triggered if there is one, otherwise None.
#  - user, Current user object.
#  - workflow: Workflow engine.
# To return an action, assign: action = {...}

action={
    "name": '转发',
    "type": 'ir.actions.act_window',
    "res_model": 'odoo.workflow.optional',
    "view_mode": 'form',
    "view_id": env.ref('odoo_dynamic_workflow.odoo_workflow_optional_view_form').id,
    "target": 'new',
    "context": {
        **env.context,
        'is_forward': True,
        'active_id': obj.id,
        'active_model': obj._name,
        'default_is_approve': True,
        'default_is_notice': False,
    },
}
"""


class OdooWorkflowNodeButton(models.Model):
    _name = 'odoo.workflow.node.button'
    _description = 'Odoo Workflow Node Buttons'
    _order = 'sequence'

    def _generate_key(self):
        return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))

    name = fields.Char(string='Button String', translate=True,
                       help="Enter button string name that will appear in the view.")
    sequence = fields.Integer(string='Sequence', help="Arrange buttons by defining sequence.")
    is_forward = fields.Boolean(string='Is Forward')
    is_highlight = fields.Boolean(string='Is Highlighted', default=True,
                                  help="Control highlighting of the button if needs user attention..")
    has_icon = fields.Boolean(string='Has Icon', help="Enable it to add icon to the button.")
    icon = fields.Char(string='Icon', help="Enter icon name like: fa-print, it's recommended to use FontAwesome Icons.")
    btn_key = fields.Char(string='Button Key', default=_generate_key)
    condition_code = fields.Text(string='Condition Code', default=CONDITION_CODE_TEMP,
                                 help="Enter condition to execute button action.")
    action_type = fields.Selection([
        ('link', 'Trigger Link'),
        ('code', 'Python Code'),
        ('action', 'Server Action'),
        ('win_act', 'Window Action'),
    ], string='Action Type', default='link', help="Choose type of action to be trigger by the button.")
    link_id = fields.Many2one('odoo.workflow.link', string='Link')
    code = fields.Text(string='Python Code', default=PYTHON_CODE_TEMP)
    server_action_id = fields.Many2one('ir.actions.server', string='Server Action')
    win_act_id = fields.Many2one('ir.actions.act_window', string='Window Action')
    node_id = fields.Many2one('odoo.workflow.node', string='Workflow Node Ref', ondelete='cascade', required=True)
    workflow_id = fields.Many2one('odoo.workflow', string='Workflow Ref', ondelete='cascade', required=True,
                                  related='node_id.workflow_id')
    group_ids = fields.Many2many('res.groups', string='Groups')
    user_ids = fields.Many2many('res.users', string='Users')
    expression = fields.Text(string='Expression', help="Enter expression to display button.")

    @api.constrains('btn_key')
    def validation(self):
        for rec in self:
            # Check if there is no duplicate button key
            res = self.search_count([
                ('id', '!=', rec.id),
                ('btn_key', '=', rec.btn_key),
            ])
            if res:
                rec.btn_key = self._generate_key()

    def run(self):
        for rec in self:
            # Check Condition Before Executing Action
            result = False
            cx = self.env.context.copy() or {}
            locals_dict = {
                'env': self.env,
                'model': self.env[cx.get('active_model', False)],
                'obj': self.env[cx.get('active_model', False)].browse(cx.get('active_id', 0)),
                'user': self.env.user,
                'datetime': datetime,
                'time': time,
                'date': date,
                'timedelta': timedelta,
                'workflow': self.env['odoo.workflow']
            }
            try:
                safe_eval(rec.condition_code, locals_dict=locals_dict, mode='exec', nocopy=True)
                result = 'result' in locals_dict and locals_dict['result'] or False
            except ValidationError as ex:
                raise ex
            except SyntaxError as ex:
                raise UserError(_("Wrong python code defined.\n\nError: %s\nLine: %s, Column: %s\n\n%s" % (
                    ex.args[0], ex.args[1][1], ex.args[1][2], ex.args[1][3])))
            if result:
                # Run Proper Action
                func = getattr(self, "_run_%s" % rec.action_type)
                return func()
            else:
                action = 'action' in locals_dict and locals_dict['action'] or False
                return action

    def _run_win_act(self):
        # Variables
        cx = self.env.context.copy() or {}
        win_act_obj = self.env['ir.actions.act_window']
        # Run Window Action
        for rec in self:
            action = win_act_obj.with_context(cx).browse(rec.win_act_id.id).read()[0]
            action['context'] = cx
            return action
        return False

    def _run_action(self):
        # Variables
        srv_act_obj = self.env['ir.actions.server']
        # Run Server Action
        for rec in self:
            srv_act_rec = srv_act_obj.browse(rec.server_action_id.id)
            return srv_act_rec.run()

    def _run_code(self):
        # Variables
        cx = self.env.context.copy() or {}
        locals_dict = {
            'env': self.env,
            'model': self.env[cx.get('active_model', False)],
            'obj': self.env[cx.get('active_model', False)].browse(cx.get('active_id', 0)),
            'user': self.env.user,
            'datetime': datetime,
            'time': time,
            'date': date,
            'timedelta': timedelta,
            'workflow': self.env['odoo.workflow']
        }
        # Run Code
        for rec in self:
            try:
                safe_eval(rec.code, locals_dict=locals_dict, mode='exec', nocopy=True)
                action = 'action' in locals_dict and locals_dict['action'] or False
                if action:
                    return action
            except Warning as ex:
                raise ex
            except SyntaxError as ex:
                raise UserError(_("Wrong python code defined.\n\nError: %s\nLine: %s, Column: %s\n\n%s" % (
                ex.args[0], ex.args[1][1], ex.args[1][2], ex.args[1][3])))
        return True

    def _run_link(self):
        for rec in self:
            # Check Condition Before Executing Action
            result = False
            cx = self.env.context.copy() or {}
            locals_dict = {
                'env': self.env,
                'model': self.env[cx.get('active_model', False)],
                'obj': self.env[cx.get('active_model', False)].browse(cx.get('active_id', 0)),
                'user': self.env.user,
                'datetime': datetime,
                'time': time,
                'date': date,
                'timedelta': timedelta,
                'workflow': self.env['odoo.workflow']
            }
            try:
                safe_eval(rec.link_id.condition_code, locals_dict=locals_dict, mode='exec', nocopy=True)
                result = 'result' in locals_dict and locals_dict['result'] or False
            except ValidationError as ex:
                raise ex
            except SyntaxError as ex:
                raise UserError(_("Wrong python code defined.\n\nError: %s\nLine: %s, Column: %s\n\n%s" % (
                    ex.args[0], ex.args[1][1], ex.args[1][2], ex.args[1][3])))
            if result:
                # Trigger link function
                return rec.link_id.trigger_link()
