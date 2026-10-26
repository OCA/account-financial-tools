/*
  Copyright 2025 Akretion France (https://www.akretion.com/)
  @author: Alexis de Lattre <alexis.delattre@akretion.com>
  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

import {DashboardKanbanRecord} from "@account/views/account_dashboard_kanban/account_dashboard_kanban_record";
import {browser} from "@web/core/browser/browser";
import {DashboardKanbanRenderer} from "@account/views/account_dashboard_kanban/account_dashboard_kanban_renderer";
import {kanbanView} from "@web/views/kanban/kanban_view";
import {onWillStart} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

// Currency of the totals when several companies are selected, kept by the browser
const CURRENCY_KEY = "account_dashboard_banner.currency_id";

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
            const currencies = await this.orm.call("account.dashboard.banner.cell", "get_banner_currencies");
            const storedId = parseInt(browser.localStorage.getItem(CURRENCY_KEY));
            const currency = currencies.find((cur) => cur.id === storedId) || currencies[0];
            this.state.bannerCurrencies = currencies;
            this.state.bannerCurrencyId = currency ? currency.id : false;
            await this.loadBanner();
        });
    }

    async loadBanner() {
        this.state.banner = await this.orm.call("account.dashboard.banner.cell", "get_banner_data", [], {
            currency_id: this.state.bannerCurrencyId,
        });
    }

    async onBannerCurrencyChange(ev) {
        this.state.bannerCurrencyId = parseInt(ev.target.value);
        browser.localStorage.setItem(CURRENCY_KEY, this.state.bannerCurrencyId);
        await this.loadBanner();
    }
}

export const accountDashboardKanbanBanner = {
    ...kanbanView,
    Renderer: DashboardKanbanRendererBanner,
};

registry.category("views").add("account_dashboard_kanban_banner", accountDashboardKanbanBanner);
