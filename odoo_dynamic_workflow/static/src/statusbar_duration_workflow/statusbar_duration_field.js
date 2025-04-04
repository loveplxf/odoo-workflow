/** @odoo-module **/

import { formatDuration } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { statusBarDurationField, StatusBarDurationField } from "@mail/views/fields/statusbar_duration/statusbar_duration_field";

export class StatusBarDurationWorkflowField extends StatusBarDurationField {

    getAllItems() {
        const items = super.getAllItems();
        const durationTracking = this.props.record.data.x_duration_tracking || {};
        if (Object.keys(durationTracking).length) {
            for (const item of items) {
                const duration = durationTracking[item.value];
                if (duration > 0) {
                    item.shortTimeInStage = formatDuration(duration, false);
                    item.fullTimeInStage = formatDuration(duration, true);
                } else {
                    item.shortTimeInStage = 0;
                }
            }
        }
        return items;
    }
}

export const statusBarDurationWorkflowField = {
    ...statusBarDurationField,
    component: StatusBarDurationWorkflowField,
    displayName: _t("Duration Tracking Field"),
    supportedTypes: ["many2one"],
    fieldDependencies: [{ name: "x_duration_tracking", type: "JSON" }],
};

registry.category("fields").add("statusbar_duration_workflow", statusBarDurationWorkflowField);
