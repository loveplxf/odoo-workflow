# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval, test_python_expr
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date, time, timedelta
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
#    action type: danger/warning/success/info
# eg:
# if True:
#     result = True
# else:
#     result = False
#     action = {
#         'type': 'ir.actions.client',
#         'tag': 'display_notification',
#         'params': {
#             'title': 'Message Title',
#             'message': 'Message Description',
#             'type': 'danger',
#             'sticky': False
#         },
#     }

result = True"""


class OdooWorkflowLink(models.Model):
    _name = 'odoo.workflow.link'
    _description = 'Link'

    name = fields.Char(string='Name', help="Enter friendly link name that describe the process.", required=True)
    workflow_id = fields.Many2one('odoo.workflow', string='Workflow Ref', ondelete='cascade', store=True,
                                  related='node_from.workflow_id')
    node_from = fields.Many2one('odoo.workflow.node', 'Source Node', ondelete='cascade', required=True)
    node_to = fields.Many2one('odoo.workflow.node', 'Destination Node', ondelete='cascade', required=True)

    expression = fields.Text(string='Expression', help="Enter expression to display button. eg: status == 'EQ'")

    link_before = fields.Text(string='Link Before Code', default=CONDITION_CODE_TEMP,
                              help="Enter condition to pass thru this link.")
    link_after = fields.Text(string='Link After Code', default=CONDITION_CODE_TEMP,
                             help="Enter condition to pass thru this link.")

    @api.constrains('link_before')
    def _check_python_code(self):
        for action in self.sudo().filtered('link_before'):
            msg = test_python_expr(expr=action.link_before.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    @api.constrains('link_after')
    def _check_python_code(self):
        for action in self.sudo().filtered('link_after'):
            msg = test_python_expr(expr=action.link_after.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    @api.constrains('node_from', 'node_to')
    def check_nodes(self):
        for rec in self:
            if rec.node_from == rec.node_to:
                raise ValidationError(_("Sorry, source & destination nodes can't be the same."))

    def trigger_link(self):
        # Variables
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        record = self.env[active_model].sudo().browse(active_id)

        if record.x_stage_id == self.node_from:
            # Link Before
            result_link_before = self._run_link_before()
            if type(result_link_before) is not bool:
                return result_link_before
            elif type(result_link_before) is bool and not result_link_before:
                return

            # Link
            record.x_stage_id = self.node_to
            result = record.x_stage_id.set_approve_notice_users(record)
            self._add_workflow_logs(record)

            # Link After
            result_link_after = self._run_link_after()
            if type(result_link_after) is not bool:
                return result_link_after
            elif type(result_link_after) is bool and not result_link_after:
                return

            return result

    def _run_link_before(self):
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
                'workflow': self.env['odoo.workflow'],
            }
            try:
                safe_eval(rec.link_before, locals_dict=locals_dict, mode='exec', nocopy=True)
                result = 'result' in locals_dict and locals_dict['result'] or False
            except ValidationError as ex:
                raise ex
            except SyntaxError as ex:
                raise UserError(_("Wrong python code defined.\n\nError: %s\nLine: %s, Column: %s\n\n%s" % (
                    ex.args[0], ex.args[1][1], ex.args[1][2], ex.args[1][3])))
            if result:
                return True
            else:
                action = 'action' in locals_dict and locals_dict['action'] or False
                return action

    def _run_link_after(self):
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
                'workflow': self.env['odoo.workflow'],
            }
            try:
                safe_eval(rec.link_after, locals_dict=locals_dict, mode='exec', nocopy=True)
                result = 'result' in locals_dict and locals_dict['result'] or False
            except ValidationError as ex:
                raise ex
            except SyntaxError as ex:
                raise UserError(_("Wrong python code defined.\n\nError: %s\nLine: %s, Column: %s\n\n%s" % (
                    ex.args[0], ex.args[1][1], ex.args[1][2], ex.args[1][3])))
            if result:
                return result
            else:
                action = 'action' in locals_dict and locals_dict['action'] or False
                return action

    def _add_workflow_logs(self, record):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        log = self.env['odoo.workflow.logs'].search([('res_model', '=', active_model), ('res_id', '=', active_id)],
                                                    order='id DESC', limit=1)
        datetime_now = datetime.now()
        if not log:
            log = self.env['odoo.workflow.logs'].create({
                'res_model': record._name,
                'res_id': record.id,
                'workflow_id': self.node_from.workflow_id.id,
                'node_from': self.node_from.id,
                'process': self.name,
                'process_user': self.env.uid,
                'start_datetime': datetime_now,
                'end_datetime': datetime_now,
                'process_datetime': datetime_now,
                'current': False
            })

        log.write({
            'node_from': self.node_from.id,
            'process': self.name,
            'process_user': self.env.uid,
            'end_datetime': datetime_now,
            'process_datetime': datetime_now,
            'current': False,
        })
        self.env['odoo.workflow.logs'].create({
            'res_model': record._name,
            'res_id': record.id,
            'workflow_id': self.node_from.workflow_id.id,
            'node_to': self.node_to.id,
            'start_datetime': datetime.now(),
            'approve_user_ids': record.x_approve_user_ids,
            'notice_user_ids': record.x_notice_user_ids,
            'current': False if self.node_to.flow_end else True
        })
