/** @odoo-module **/

// import DiagramPlusView from './../src/js/diagram_view';
// import {
//     createView,
//     dom,
//     fields,
//     nextTick,
// } from 'web.test_utils';
// import {
//     GraphNode as CuteNodePlus,
//     GraphEdge as CuteEdgePlus,
// } from './../src/js/graph';
//
// QUnit.module('DiagramPlus', {
//     beforeEach: function () {
//         this.data = {
//             workflow: {
//                 fields: {
//                     name: {string: 'Name', type: "char"},
//                 },
//                 records: [
//                     {id: 1, name: "a workflow"},
//                 ],
//             },
//             node_model: {
//                 fields: {
//                     name: {string: 'Name', type: 'char'},
//                     workflow_id: {
//                         string: 'Workflow ID',
//                         type: 'many2one',
//                         relation: 'workflow',
//                     },
//                 },
//                 records: [
//                     {id: 1, name: "A first node", workflow_id: 1},
//                     {id: 2, name: "A second node", workflow_id: 1},
//                     {id: 3, name: "A third node", workflow_id: 1},
//                 ],
//             },
//             transition_model: {
//                 fields: {
//                     name: {string: 'Name', type: 'char'},
//                     source_id: {
//                         string: 'Source ID',
//                         type: 'many2one',
//                         relation: 'node_model',
//                     },
//                     dest_id: {
//                         string: 'Destination ID',
//                         type: 'many2one',
//                         relation: 'node_model',
//                     },
//                 },
//                 records: [
//                     {
//                         id: 1,
//                         name: 'a transition from 1 to 2',
//                         source_id: 1,
//                         dest_id: 2,
//                     },
//                     {
//                         id: 2,
//                         name: 'a transition from 2 to 3',
//                         source_id: 2,
//                         dest_id: 3,
//                     },
//                     {
//                         id: 3,
//                         name: 'a transition from 2 to 1',
//                         source_id: 2,
//                         dest_id: 1,
//                     },
//                 ],
//             },
//         };
//         this.arch = '<diagram_plus>' +
//                         '<node object="node_model"/>' +
//                         '<arrow ' +
//                             'object="transition_model" ' +
//                             'source="source_id" ' +
//                             'destination="dest_id" ' +
//                             'label="[\'name\']"' +
//                         '/>' +
//                         '<label string="A first label"/>' +
//                         '<label string="A second label"/>' +
//                     '</diagram_plus>';
//         this.archs = {
//             'node_model,false,form': '<form string="Create a new node">' +
//                                          '<field name="name"/>' +
//                                          '<field name="workflow_id"/>' +
//                                      '</form>',
//             'transition_model,false,form':
//                                       '<form string="Create an edge">' +
//                                       '<field name="name"/>' +
//                                       '<field name="source_id"/>' +
//                                       '<field name="dest_id"/>' +
//                                   '</form>',
//         };
//         this.mockRPC = function (route, args) {
//             if (route !== '/web_diagram_plus/diagram/get_diagram_info') {
//                 return this._super.apply(this, arguments);
//             }
//             var data = this.data;
//             var node_records = _.filter(
//                 data.node_model.records,
//                 {workflow_id: args.id}
//             );
//             var transition_records = _.filter(
//                 data.transition_model.records,
//                 function (record) {
//                     return _.findWhere(
//                         node_records,
//                         {id: record.source_id}
//                     );
//                 }
//             );
//             return Promise.resolve({
//                 parent_field: 'workflow_id',
//                 display_name: _.findWhere(
//                     data.workflow.records,
//                     {id: args.id}
//                 ).name,
//                 nodes: _.map(node_records, function (record) {
//                     return {
//                         id: record.id,
//                         name: record.name,
//                         color: 'gray',
//                         shape: record.id === 1 ? 'rectangle' : undefined,
//                     };
//                 }),
//                 conn: _.map(
//                     transition_records,
//                     function (record) {
//                         var source_node = _.findWhere(
//                             data.node_model.records,
//                             {id: record.source_id}
//                         );
//                         var dest_node = _.findWhere(
//                             data.node_model.records,
//                             {id: record.dest_id}
//                         );
//                         return {
//                             source: source_node ? source_node.name: '',
//                             destination: dest_node ? dest_node.name: '',
//                             s_id: record.source_id,
//                             d_id: record.dest_id,
//                             signal: record.name,
//                         };
//                     }
//                 ),
//             });
//         };
//     },
//     afterEach: function () {
//         $("body > i[title='Raphaël Colour Picker']").remove();
//     }
// }, function () {
//
//     QUnit.module('DiagramPlusView');
//
//     QUnit.test('simple diagram plus rendering', async function (assert) {
//         assert.expect(6);
//
//         var diagram = await createView({
//             View: DiagramPlusView,
//             model: 'workflow',
//             data: this.data,
//             arch: this.arch,
//             res_id: 1,
//             mockRPC: this.mockRPC,
//         });
//         assert.containsOnce(diagram, '.o_diagram_plus svg',
//             "draw the diagram inside the .o_diagram_plus div");
//         assert.strictEqual(
//             diagram.$(
//                 '.o_diagram_plus path:not(#raphael-marker-block)'
//             ).length, 3,
//             "diagram should contain 3 transitions");
//         assert.containsN(diagram, '.o_diagram_plus ellipse', 2,
//             "diagram should contain 2 'ellipse' nodes (nodes 2 and 3)");
//         // -1 because the lib always generates a rect tag that isn't a node
//         assert.strictEqual(diagram.$('.o_diagram_plus rect').length - 1, 1,
//             "diagram should contain 1 'rectangle' node (node 1)");
//         assert.containsN(diagram, '.o_diagram_plus_header span', 2,
//             "diagram should contain 2 header rows");
//         assert.strictEqual(
//             diagram.$('.o_diagram_plus_header span:eq(0)').text(),
//             'A first label',
//             "diagram label is correctly inserted");
//         diagram.destroy();
//     });
//
//     QUnit.test('node plus creation', async function (assert) {
//         assert.expect(4);
//
//         var diagram = await createView({
//             View: DiagramPlusView,
//             model: 'workflow',
//             data: this.data,
//             arch: this.arch,
//             archs: this.archs,
//             res_id: 1,
//             mockRPC: this.mockRPC,
//         });
//
//         assert.containsN(diagram, '.o_diagram_plus ellipse', 2,
//             "diagram should contain 2 'ellipse' nodes (nodes 2 and 3)");
//         assert.strictEqual(
//             diagram.$('text:contains(a new node)').length, 0,
//             "diagram should only have the default nodes at start");
//
//         await dom.click(
//             diagram.$buttons.find('.o_diagram_plus_new_button'));
//         await fields.editInput(
//             $('.modal-body input:first'), 'a new node');
//         await fields.editInput(
//             $('.modal-body input:last'), 1);
//         await dom.click(
//             $('.modal-footer button.btn-primary'));
//
//         assert.containsN(
//             diagram, '.o_diagram_plus ellipse', 3,
//             "diagram should contain 3 'ellipse' nodes now " +
//             "(nodes 2, 3 and the new one)");
//         assert.strictEqual(
//             diagram.$('text:contains(a new node)').length, 1,
//             "diagram should only have the default nodes at start");
//         diagram.destroy();
//     });
//
//     QUnit.test('node plus edition', async function (assert) {
//         assert.expect(2);
//
//         var diagram = await createView({
//             View: DiagramPlusView,
//             model: 'workflow',
//             data: this.data,
//             arch: this.arch,
//             archs: this.archs,
//             res_id: 1,
//             mockRPC: this.mockRPC,
//         });
//
//         assert.strictEqual(diagram.$('.o_diagram_plus text').first().text(),
//             'A first node',
//             "diagram first node should have default name at first");
//
//         CuteNodePlus.double_click_callback({id: 1});
//         await nextTick();
//         await fields.editInput(
//             $('.modal-body input:first'), 'An edited node');
//         await dom.click(
//             $('.modal-footer button.btn-primary'));
//
//         assert.strictEqual(
//             diagram.$('text').first().text(), 'An edited node',
//             "diagram first node should now have new name");
//
//         diagram.destroy();
//     });
//
//     QUnit.test('node plus deletion', async function (assert) {
//         assert.expect(2);
//
//         var diagram = await createView({
//             View: DiagramPlusView,
//             model: 'workflow',
//             data: this.data,
//             arch: this.arch,
//             res_id: 1,
//             mockRPC: this.mockRPC,
//         });
//
//         assert.containsN(diagram, '.o_diagram_plus ellipse', 2,
//             "diagram should contain 2 'ellipse' nodes (nodes 2 and 3)");
//
//         CuteNodePlus.destruction_callback({id: 2});
//         await nextTick();
//         await dom.click($('.modal-footer button.btn-primary'));
//
//         assert.containsOnce(diagram, '.o_diagram_plus ellipse',
//             "diagram should contain 1 'ellipse' nodes (node 2)");
//
//         diagram.destroy();
//     });
//
//     QUnit.test('edge plus creation', async function (assert) {
//         assert.expect(4);
//
//         var diagram = await createView({
//             View: DiagramPlusView,
//             model: 'workflow',
//             data: this.data,
//             arch: this.arch,
//             archs: this.archs,
//             res_id: 1,
//             mockRPC: this.mockRPC,
//         });
//
//         assert.containsN(diagram, '.o_diagram_plus path', 4,
//             "diagram should contain 4 'path' nodes " +
//             "(#raphael-marker-block, and transitions 1, 2 and 3)");
//         assert.strictEqual(
//             diagram.$('text:contains(a transition from 1 to 3)').length, 0,
//             "diagram should not have a transition from 1 to 3 at start");
//
//         CuteEdgePlus.new_edge_callback({
//             get_start: function () {return {id: 1};},
//             get_end: function () {return {id: 3};},
//         });
//         await nextTick();
//         await fields.editInput(
//             $('.modal-body input:first'), 'a transition from 1 to 3');
//         await dom.click(
//             $('.modal-footer button.btn-primary'));
//
//         assert.containsN(diagram, '.o_diagram_plus path', 5,
//             "diagram should contain 4 'path' nodes " +
//             "(#raphael-marker-block, transitions 1, 2, 3, and the new one)"
//         );
//         assert.strictEqual(
//             diagram.$('text:contains(a transition from 1 to 3)').length, 1,
//             "diagram should now have a transition from 1 to 3");
//
//         diagram.destroy();
//     });
//
//     QUnit.test('edge plus edition', async function (assert) {
//         assert.expect(4);
//
//         var diagram = await createView({
//             View: DiagramPlusView,
//             model: 'workflow',
//             data: this.data,
//             arch: this.arch,
//             archs: this.archs,
//             res_id: 1,
//             mockRPC: this.mockRPC,
//         });
//
//         assert.strictEqual(
//             diagram.$('text:contains(a transition from 1 to 2)').length, 1,
//             "diagram edge should have default name at start");
//         assert.strictEqual(
//             diagram.$('text:contains(An edited edge)').length, 0,
//             "diagram should only have the default edges at start");
//
//         CuteEdgePlus.double_click_callback({id: 1});
//         await nextTick();
//         await fields.editInput(
//             $('.modal-body input:first'), 'An edited edge');
//         await dom.click(
//             $('.modal-footer button.btn-primary'));
//
//         assert.strictEqual(
//             diagram.$('text:contains(a transition from 1 to 2)').length, 0,
//             "diagram edge should not have default name anymore");
//         assert.strictEqual(
//             diagram.$('text:contains(An edited edge)').length, 1,
//             "diagram should now have the new edge");
//
//         diagram.destroy();
//     });
//
//     QUnit.test('edge plus deletion', async function (assert) {
//         assert.expect(4);
//
//         var diagram = await createView({
//             View: DiagramPlusView,
//             model: 'workflow',
//             data: this.data,
//             arch: this.arch,
//             res_id: 1,
//             mockRPC: this.mockRPC,
//         });
//
//         assert.containsN(diagram, '.o_diagram_plus path', 4,
//             "diagram should contain 4 'path' nodes " +
//             "(#raphael-marker-block, and transitions 1, 2 and 3)");
//         assert.strictEqual(
//             diagram.$('text:contains(a transition from 2 to 1)').length, 1,
//             "diagram edge should have default name at start");
//
//         CuteEdgePlus.destruction_callback({id: 3});
//         await nextTick();
//         await dom.click($('.modal-footer button.btn-primary'));
//
//         assert.containsN(diagram, '.o_diagram_plus path', 3,
//             "diagram should contain 3 'path' nodes " +
//             "(#raphael-marker-block, and transitions 1 and 2)");
//         assert.strictEqual(
//             diagram.$('text:contains(a transition from 2 to 1)').length, 0,
//             "diagram edge label should have been deleted");
//
//         diagram.destroy();
//     });
// });
