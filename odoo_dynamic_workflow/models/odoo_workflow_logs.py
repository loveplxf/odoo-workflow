# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID, Command
from datetime import datetime
import logging
from collections import defaultdict

_logger = logging.getLogger(__name__)


class OdooWorkflowLogs(models.Model):
    _name = 'odoo.workflow.logs'
    _description = 'Logs'

    name = fields.Char('Resource Name', compute='_compute_res_name')
    current_state = fields.Selection(string='Current State', compute='_compute_current_state',
                                     selection=[('draft', 'Draft'), ('processing', 'Processing'), ('done', 'Done')])

    node_from = fields.Many2one('odoo.workflow.node', string='Source Node', ondelete='cascade', store=True)
    node_to = fields.Many2one('odoo.workflow.node', string='Destination Node', ondelete='cascade', store=True)
    flow_start = fields.Boolean(string='Flow Start', related="node_from.flow_start")
    flow_end = fields.Boolean(string='Flow End', related="node_to.flow_end")
    workflow_id = fields.Many2one('odoo.workflow', string='Workflow Ref', ondelete='cascade')
    res_model = fields.Char('Resource Model')
    res_id = fields.Integer('Resource ID')
    approve_user_ids = fields.Many2many('res.users', 'log_users_rel', 'log_id', 'users_id', string='Approve Users')
    notice_user_ids = fields.Many2many('res.users', 'log_notice_users_rel', 'log_id', 'users_id', string='Notice Users')
    current = fields.Boolean('Active', default=True)
    note = fields.Text('Note', help="If you want record something for this link, write here")

    start_datetime = fields.Datetime('Start Time')
    end_datetime = fields.Datetime('End Time')
    process_user = fields.Many2one('res.users', string='Process User')
    process_datetime = fields.Datetime('Process Time')
    process = fields.Char('Process')
    duration = fields.Float('Duration', compute='_compute_duration')
    timeout_id = fields.Many2one('odoo.workflow.timeout', string='Timeout')

    is_read = fields.Boolean('已读', compute='_compute_is_read')
    read_user_ids = fields.Many2many('res.users', 'log_read_users_rel', 'log_id', 'users_id', string='Read Users')

    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for rec in self:
            rec.update_end_datetime()
            if rec.start_datetime and rec.end_datetime:
                seconds = (rec.end_datetime - rec.start_datetime).total_seconds()
                if 0 < seconds < 60:
                    seconds = 60
                seconds = seconds - seconds % 60
                rec.duration = round(seconds / 3600, 2)
            else:
                rec.duration = 0

    @api.model
    def create_all_timeout_notice(self):
        self.update_all_end_datetime()
        logs = self.env['odoo.workflow.logs'].search([('current', '=', True)])
        logs.create_timeout_notice()

    def create_timeout_notice(self):
        for rec in self:
            timeouts = self.env['odoo.workflow.timeout'].search([('workflow_id', '=', rec.workflow_id.id)])
            for timeout in timeouts:
                has_timeout = self.env['odoo.workflow.logs'].search_count(
                    [('workflow_id', '=', rec.workflow_id.id),
                     ('res_model', '=', rec.res_model),
                     ('res_id', '=', rec.res_id),
                     ('timeout_id', '=', timeout.id)])
                if has_timeout:
                    continue

                logs = self.env['odoo.workflow.logs'].search(
                    [('workflow_id', '=', rec.workflow_id.id),
                     ('res_model', '=', rec.res_model),
                     ('res_id', '=', rec.res_id),
                     ('node_to', 'in', timeout.node_ids.ids)])

                sum_duration = sum([log.duration for log in logs])
                if sum_duration > timeout.timeout_duration:
                    self.env['odoo.workflow.logs'].create({
                        'res_model': rec.res_model,
                        'res_id': rec.res_id,
                        'workflow_id': rec.workflow_id.id,
                        'process': timeout.name,
                        'process_user': SUPERUSER_ID,
                        'process_datetime': datetime.now(),
                        'notice_user_ids': timeout.notice_user_ids,
                        'current': False,
                        'timeout_id': timeout.id
                    })

    @api.model
    def update_all_end_datetime(self):
        logs = self.env['odoo.workflow.logs'].search([('current', '=', True)])
        logs.update_end_datetime()

    def update_end_datetime(self):
        for rec in self:
            if rec.current:
                rec.end_datetime = datetime.now()

    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for rec in self:
            if rec.res_model and rec.res_id:
                rec.name = self.env[rec.res_model].browse(rec.res_id).display_name

    @api.depends('res_model', 'res_id')
    def _compute_current_state(self):
        for rec in self:
            rec.current_state = 'processing'
            if rec.res_model and rec.res_id:
                if self.env[rec.res_model].browse(rec.res_id).x_stage_id.flow_start:
                    rec.current_state = 'draft'
                if self.env[rec.res_model].browse(rec.res_id).x_stage_id.flow_end:
                    rec.current_state = 'done'

    def action_open_record(self):
        self.ensure_one()
        self.set_message_done()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': self.res_id,
            'res_model': self.res_model,
        }

    @api.depends('read_user_ids')
    def _compute_is_read(self):
        for log in self:
            if self.env.user in log.read_user_ids:
                log.is_read = True
            else:
                log.is_read = False

    def set_message_done(self):
        # 设置已读
        if not self.is_read:
            self.env[self.res_model].browse(self.res_id).message_post(body='已读', message_type='notification')
            self.read_user_ids = [Command.link(self.env.user.id)]

    @api.model
    def get_duration_tracking(self, res_model, res_id):
        if not res_id:
            return {}
        logs = self.env['odoo.workflow.logs'].search([('res_model', '=', res_model), ('res_id', '=', res_id)],
                                                     order='start_datetime')
        logs.update_end_datetime()
        default_dict = defaultdict(lambda: 0)
        for log in logs:
            if log.start_datetime and log.end_datetime:
                seconds = (log.end_datetime - log.start_datetime).total_seconds()
                if 0 < seconds < 60:
                    seconds = 60
                seconds = seconds - seconds % 60
                default_dict[log.node_to.id] += seconds
        return default_dict
