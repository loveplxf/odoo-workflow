# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class OdooWorkflowNodeField(models.Model):
    _name = 'odoo.workflow.node.field'
    _description = 'Odoo Workflow Node Fields'

    field_id = fields.Many2one('ir.model.fields', string='Field')
    model_id = fields.Many2one('ir.model', string='Model')
    readonly = fields.Boolean(string='Readonly')
    required = fields.Boolean(string='Required')
    invisible = fields.Boolean(string='Invisible')
    node_id = fields.Many2one('odoo.workflow.node', string='Node Ref', ondelete='cascade', required=True)


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    @api.depends('field_description', 'name')
    def _compute_display_name(self):
        for field in self:
            field.display_name = f'[{field.name}] {field.field_description}'
