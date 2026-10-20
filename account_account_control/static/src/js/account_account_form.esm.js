import {FormController} from "@web/views/form/form_controller";
import {addModificationReason} from "./modification_reason_dialog.esm";
import {formView} from "@web/views/form/form_view";
import {registry} from "@web/core/registry";

export class AccountAccountFormController extends FormController {
    async onWillSaveRecord(record, changes) {
        const canProceed = await super.onWillSaveRecord(...arguments);
        if (canProceed === false) {
            return false;
        }
        return addModificationReason(this.dialogService, [record], changes);
    }
}

registry.category("views").add("account_account_control_form", {
    ...formView,
    Controller: AccountAccountFormController,
});
