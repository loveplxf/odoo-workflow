# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class OdooWorkflowTimeout(models.Model):
    _name = 'odoo.workflow.timeout'
    _description = 'Odoo Workflow Timeout'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', help="Arrange node by defining sequence.")
    name = fields.Char(string='Name', required=True)
    workflow_id = fields.Many2one('odoo.workflow', string='Workflow Ref', ondelete='cascade')
    node_ids = fields.Many2many('odoo.workflow.node', 'timeout_node_rel', 'timeout_id', 'node_id',
                                string='Timeout Nodes', required=True)
    timeout_duration = fields.Float('Timeout Duration', required=True)
    notice_user_ids = fields.Many2many('res.users', 'timeout_notice_users_rel', 'timeout_id', 'users_id',
                                       string='Notice Users', required=True)
