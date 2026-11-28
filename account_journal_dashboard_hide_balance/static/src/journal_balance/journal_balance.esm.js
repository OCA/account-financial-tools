/* Copyright 2026 KMEE
   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). */

import {Component} from "@odoo/owl";
import {MaskedValue} from "@web_widget_masked_value/masked_value.esm";
import {registry} from "@web/core/registry";
import {standardWidgetProps} from "@web/views/widgets/standard_widget_props";

export class JournalBalanceAmount extends Component {
    static template = "account_journal_dashboard_hide_balance.JournalBalanceAmount";
    static components = {MaskedValue};
    static props = {...standardWidgetProps, dashboardKey: String};

    get amount() {
        return JSON.parse(this.props.record.data.kanban_dashboard)[this.props.dashboardKey];
    }
}

registry.category("view_widgets").add("journal_balance_amount", {
    component: JournalBalanceAmount,
    extractProps: ({attrs}) => ({dashboardKey: attrs.dashboard_key}),
    fieldDependencies: [{name: "kanban_dashboard", type: "text"}],
});
