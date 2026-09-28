import {ListController} from "@web/views/list/list_controller";
import {addModificationReason} from "./modification_reason_dialog.esm";
import {listView} from "@web/views/list/list_view";
import {registry} from "@web/core/registry";

export class AccountAccountListController extends ListController {
    async onWillSaveRecord(record, changes) {
        const canProceed = await super.onWillSaveRecord(...arguments);
        if (canProceed === false) {
            return false;
        }
        return addModificationReason(this.dialogService, [record], changes);
    }

    async onWillSaveMulti(editedRecord, changes, validSelectedRecords) {
        const canProceed = await super.onWillSaveMulti(...arguments);
        if (canProceed === false) {
            return false;
        }
        return addModificationReason(this.dialogService, validSelectedRecords, changes);
    }
}

registry.category("views").add("account_account_control_list", {
    ...listView,
    Controller: AccountAccountListController,
});
