# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, Command, _
from datetime import datetime, date, time, timedelta


class WorkflowOptional(models.TransientModel):
    _name = 'odoo.workflow.optional'
    _description = "Workflow Optional"

    is_approve = fields.Boolean('Is Approve')
    approve_user_ids = fields.Many2many('res.users', 'odoo_workflow_optional_approve_users_rel', 'optional_id',
                                        'approve_users_id', string='Approve Users')
    is_notice = fields.Boolean('Is Notice')
    notice_user_ids = fields.Many2many('res.users', 'odoo_workflow_optional_notice_users_rel', 'optional_id',
                                       'notice_users_id', string='Notice Users')

    def action_optional_confirm(self):
        record = self.env[self.env.context['active_model']].browse(self.env.context['active_id'])
        if self.is_approve:
            record.x_approve_user_ids = [Command.set(self.approve_user_ids.ids)] if self.approve_user_ids.ids else [Command.clear()]
        if self.is_notice:
            record.x_notice_user_ids = [Command.set(self.notice_user_ids.ids)] if self.notice_user_ids.ids else [Command.clear()]

        if self.env.context['is_forward']:
            self._add_workflow_logs(record)

    def _add_workflow_logs(self, record):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        log = self.env['odoo.workflow.logs'].search([('res_model', '=', active_model), ('res_id', '=', active_id)],
                                                    order='id DESC', limit=1)
        datetime_now = datetime.now()

        log.write({
            'process': _('Forward'),
            'process_user': self.env.uid,
            'process_datetime': datetime_now,
            'end_datetime': datetime_now,
            'current': False,
        })
        self.env['odoo.workflow.logs'].create({
            'workflow_id': log.node_to.workflow_id.id,
            'node_to': log.node_to.id,
            'res_model': log.res_model,
            'res_id': log.res_id,
            'start_datetime': datetime.now(),
            'approve_user_ids': record.x_approve_user_ids,
            'notice_user_ids': record.x_notice_user_ids,
            'current': False if log.node_to.flow_end else True
        })
