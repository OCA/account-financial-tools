# Copyright 2021 Akretion France (http://www.akretion.com/)
# Copyright 2022 Vauxoo (https://www.vauxoo.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Moisés López <moylop260@vauxoo.com>
# @author: Francisco Luna <fluna@vauxoo.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    create_journal_sequences(env)


def create_journal_sequences(env):
    journals = (
        env["account.journal"]
        .with_context(active_test=False)
        .search([("sequence_id", "=", False)])
    )
    for journal in journals:
        journal_vals = {
            "code": journal.code,
            "name": journal.name,
            "company_id": journal.company_id.id,
        }
        seq_vals = journal._prepare_sequence(journal_vals)
        seq_vals.update(journal._prepare_sequence_current_moves())
        vals = {"sequence_id": env["ir.sequence"].create(seq_vals).id}
        if journal.type in ("sale", "purchase") and journal.refund_sequence:
            rseq_vals = journal._prepare_sequence(journal_vals, refund=True)
            rseq_vals.update(journal._prepare_sequence_current_moves(refund=True))
            vals["refund_sequence_id"] = env["ir.sequence"].create(rseq_vals).id
        journal.write(vals)
    return
