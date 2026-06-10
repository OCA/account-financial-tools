/** @odoo-module **/
import {registry} from "@web/core/registry";
import {
    AccountDropZone,
    DashboardKanbanRecord,
    DashboardKanbanRenderer,
} from "@account/components/bills_upload/bills_upload";
import {kanbanView} from "@web/views/kanban/kanban_view";
import {onWillStart} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export class DashboardKanbanRendererBanner extends DashboardKanbanRenderer {
    static template = "account_dashboard_banner.AccountDashboardBannerRenderer";
    static components = {
        ...DashboardKanbanRenderer.components,
        AccountDropZone,
        KanbanRecord: DashboardKanbanRecord,
    };

    setup() {
        super.setup();
        this.state.dropzoneVisible = false;
        this.orm = useService("orm");

        onWillStart(async () => {
            this.state.banner = await this.orm.call(
                "account.dashboard.banner.cell",
                "get_banner_data"
            );
        });
    }
}

export const accountDashboardKanbanBanner = {
    ...kanbanView,
    Renderer: DashboardKanbanRendererBanner,
    components: {
        ...kanbanView.components,
        AccountDropZone,
    },
};

registry
    .category("views")
    .add("account_dashboard_kanban_banner", accountDashboardKanbanBanner);
