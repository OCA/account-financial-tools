/*
  Copyright 2025 Akretion France (https://www.akretion.com/)
  @author: Alexis de Lattre <alexis.delattre@akretion.com>
  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

import {DashboardKanbanRecord} from "@account/views/account_dashboard_kanban/account_dashboard_kanban_record";
import {DashboardKanbanRenderer} from "@account/views/account_dashboard_kanban/account_dashboard_kanban_renderer";
import {kanbanView} from "@web/views/kanban/kanban_view";
import {onWillStart} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class DashboardKanbanRendererBanner extends DashboardKanbanRenderer {
    static template = "account_dashboard_banner.AccountDashboardBannerRenderer";
    static components = {
        ...DashboardKanbanRenderer.components,
        KanbanRecord: DashboardKanbanRecord,
    };

    setup() {
        super.setup();
        this.orm = useService("orm");

        onWillStart(async () => {
            this.state.banner = await this.orm.call("account.dashboard.banner.cell", "get_banner_data");
        });
    }
}

export const accountDashboardKanbanBanner = {
    ...kanbanView,
    Renderer: DashboardKanbanRendererBanner,
};

registry.category("views").add("account_dashboard_kanban_banner", accountDashboardKanbanBanner);
