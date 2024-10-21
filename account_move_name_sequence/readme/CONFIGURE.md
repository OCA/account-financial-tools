On the form view of an account journal, in the first tab, there is a
many2one link to the sequence. When you create a new journal, you can
keep this field empty and a new sequence will be automatically created
when you save the journal.

On sale and purchase journals, you have an additional option to have
another sequence dedicated to refunds.

Upon module installation, all existing journals will be updated with a
journal entry sequence (and also a credit note sequence for sale and
purchase journals). You should update the configuration of the sequences
to fit your needs. You can uncheck the option *Dedicated Credit Note
Sequence* on existing sale and purchase journals if you don't want it.
For the journals which already have journal entries, you should update
the sequence configuration to avoid a discontinuity in the numbering for
the next journal entry.
