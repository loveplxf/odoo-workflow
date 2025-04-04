# -*- coding: utf-8 -*-
##############################################################################
from odoo.models import BaseModel
from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)

# Get BaseModel super method
default_get_old = BaseModel.default_get


def btn_exec_action(self):
    """
        Got invoked when a workflow button is called.
        :return: button action return value.
    """
    # Variables
    cx = self.env.context.copy() or {}
    cx.update({'active_id': self.id, 'active_ids': self.ids})
    wkf_btn_obj = self.env['odoo.workflow.node.button']
    btn_rec = wkf_btn_obj.search([('btn_key', '=', cx.get('btn_key', False))])
    if btn_rec:
        return btn_rec.with_context(cx).run()


def btn_trigger_link(self):
    """
        Got invoked when a workflow button is called.
        :return: button action return value.
    """
    # Variables
    cx = self.env.context.copy() or {}
    cx.update({'active_id': self.id, 'active_ids': self.ids})
    wkf_link_obj = self.env['odoo.workflow.link']
    link_rec = wkf_link_obj.browse(cx.get('link_id', False))
    if link_rec:
        return link_rec.with_context(cx).trigger_link()


def btn_exec_logs_action(self):
    """
        Got invoked when a workflow button is called.
        :return: button action return value.
    """
    self.ensure_one()
    return {
        'name': _('Workflow Logs'),
        'view_mode': 'tree',
        'view_id': self.env.ref('odoo_dynamic_workflow.view_tree_odoo_workflow_logs_no_open').id,
        'search_view_id': [self.env.ref('odoo_dynamic_workflow.view_odoo_workflow_logs_search_no_panel').id, 'search'],
        'res_model': 'odoo.workflow.logs',
        'type': 'ir.actions.act_window',
        'target': 'target',
        'domain': [('res_model', '=', self._name),
                   ('res_id', '=', self.id)]
    }


@api.model
def default_get_new(self, fields_list):
    res = default_get_old(self, fields_list)
    if 'x_stage_id' in fields_list:
        x_stage_id = self.env['odoo.workflow'].get_default_stage_id(self._name)
        res.update({'x_stage_id': x_stage_id.id})
    return res


BaseModel.default_get = default_get_new
BaseModel.btn_exec_action = btn_exec_action
BaseModel.btn_trigger_link = btn_trigger_link
BaseModel.btn_exec_logs_action = btn_exec_logs_action
