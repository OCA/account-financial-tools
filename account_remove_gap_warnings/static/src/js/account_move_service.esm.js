/** @odoo-module **/
/* Copyright 2024 Miika Nissi (https://miikanissi.com)
/* License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {accountMove} from "@account/components/account_move_service/account_move_service";
import {registry} from "@web/core/registry";

registry.category("services").remove("account_move");

const patchedAccountMove = {
    ...accountMove,
    start(env, {dialog, orm}) {
        const originalStart = accountMove.start(env, {dialog, orm});
        return {
            ...originalStart,
            async addDeletionDialog() {
                return false;
            },
        };
    },
};

registry.category("services").add("account_move", patchedAccountMove);
