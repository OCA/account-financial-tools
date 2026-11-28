import {defineModels, fields, models, mountView} from "@web/../tests/web_test_helpers";
import {expect, test} from "@odoo/hoot";
import {animationFrame} from "@odoo/hoot-mock";
import {defineAccountModels} from "@account/../tests/account_test_helpers";
import {maskedValues} from "@web_widget_masked_value/masked_value.esm";
import {queryAllTexts} from "@odoo/hoot-dom";

class AccountJournal extends models.Model {
    _name = "account.journal";
    name = fields.Char();
    kanban_dashboard = fields.Text();
    _records = [
        {id: 1, name: "Bank", kanban_dashboard: '{"account_balance": "$ 1,000.00"}'},
        {id: 2, name: "Cash", kanban_dashboard: '{"account_balance": "$ 20.00"}'},
    ];
}

defineAccountModels();
defineModels([AccountJournal]);

test("journal balances stay hidden until revealed", async () => {
    maskedValues.visible = false;
    await mountView({
        resModel: "account.journal",
        type: "kanban",
        arch: `
            <kanban>
                <templates>
                    <t t-name="card">
                        <field name="name"/>
                        <widget name="journal_balance_amount" dashboard_key="account_balance"/>
                    </t>
                </templates>
            </kanban>`,
    });
    expect(queryAllTexts(".o_masked_value")).toEqual(["*****", "*****"]);
    maskedValues.visible = true;
    await animationFrame();
    expect(queryAllTexts(".o_masked_value")).toEqual(["$ 1,000.00", "$ 20.00"]);
    maskedValues.visible = false;
});
