import {FormViewDialog} from "@web/views/view_dialogs/form_view_dialog";
import {_t} from "@web/core/l10n/translation";

/**
 * Open the modification reason wizard.
 *
 * @param {Object} dialogService
 * @returns {Promise<Number|false>} the id of the selected reason, false if
 * the dialog has been discarded
 */
export function askModificationReason(dialogService) {
    return new Promise((resolve) => {
        let reasonId = false;
        dialogService.add(
            FormViewDialog,
            {
                resModel: "account.account.modification.reason.wizard",
                title: _t("Reason for account modification"),
                onRecordSaved: (record) => {
                    reasonId = record.data.reason_id && record.data.reason_id[0];
                },
            },
            {onClose: () => resolve(reasonId)}
        );
    });
}

/**
 * Ask the modification reason if it is required for one of the existing
 * records, and add it to the changes sent to the server.
 *
 * @returns {Promise<Boolean>} false if the save must be cancelled
 */
export async function addModificationReason(dialogService, records, changes) {
    if (!records.some((record) => !record.isNew && record.data.is_modification_reason_required)) {
        return true;
    }
    const reasonId = await askModificationReason(dialogService);
    if (!reasonId) {
        return false;
    }
    changes.modification_reason_id = reasonId;
    return true;
}
