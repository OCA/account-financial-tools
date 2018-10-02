# -*- coding: utf-8 -*-
# Copyright 2014 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, models, _
from openerp.exceptions import ValidationError


FY_SLOT = '%(fy)s'
YEAR_SLOT = '%(year)s'


class Sequence(models.Model):
    _inherit = 'ir.sequence'

    def _create_fy_sequence(self, seq, fiscalyear):
        """ Create a FY sequence by cloning a sequence
            which has %(fy)s in prefix or suffix """
        fy_seq_id = self.sudo().create({
            'name': seq.name + ' - ' + fiscalyear.code,
            'implementation': seq.implementation,
            'prefix': (seq.prefix and
                       seq.prefix.replace(FY_SLOT, fiscalyear.code)),
            'suffix': (seq.suffix and
                       seq.suffix.replace(FY_SLOT, fiscalyear.code)),
            'number_next': 1,
            'number_increment': seq.number_increment,
            'padding': seq.padding,
            'company_id': seq.company_id.id,
            'code': False,
            # the Sequence Type is set to False, because the
            # the fiscal-year-specific sequence must not be catched
            # by next_by_code(), see
            # https://github.com/OCA/account-financial-tools/issues/115
            })
        self.env['account.sequence.fiscalyear']\
            .sudo().create({
                'sequence_id': fy_seq_id,
                'sequence_main_id': seq.id,
                'fiscalyear_id': fiscalyear.id,
            })
        return fy_seq_id

    # We NEED to have @api.cr_uid_ids_context even if this file still uses
    # the old API, to avoid breaking the POS, see this bug:
    # https://github.com/OCA/account-financial-tools/issues/119
    # Don't ask me why it fixes the bug, I have no idea  -- Alexis de Lattre
    # I "copied" this solution from odoo-80/addons/account/ir_sequence.py
    @api.cr_uid_ids_context
    def _next(self):
        for seq in self:
            if (seq.prefix and FY_SLOT in seq.prefix) or \
                    (seq.suffix and FY_SLOT in seq.suffix):
                fiscalyear_id = self.env.context.get('fiscalyear_id')
                if not fiscalyear_id:
                    raise ValidationError(
                        _('The system tried to access '
                          'a fiscal year sequence '
                          'without specifying the actual '
                          'fiscal year.'))
                # search for existing fiscal year sequence
                # here we behave exactly like addons/account/ir_sequence.py
                for line in seq.fiscal_ids:
                    if line.fiscalyear_id.id == fiscalyear_id:
                        return super(Sequence, self)._next()
                # no fiscal year sequence found, auto create it
                if len(self.ids) != 1:
                    # Where fiscal year sequences are used, we
                    # should always have one and only one sequence
                    # (which is the one associated to the journal).
                    # If this is not the case we'll need to investigate
                    # why, but we prefer to abort here instead of
                    # doing something potentially harmful.
                    raise ValidationError(
                        _('The system tried to access '
                          'a fiscal year sequence '
                          'but there is more than one '
                          'sequence to choose from.'))
                fiscalyear = self.env['account.fiscalyear'].browse(
                    fiscalyear_id)
                fy_seq_id = self._create_fy_sequence(fiscalyear)
                return super(Sequence, fy_seq_id)._next()
        return super(Sequence, self)._next()

    @api.multi
    def write(self, vals):
        new_prefix = vals.get('prefix')
        new_suffix = vals.get('suffix')
        if (new_prefix and FY_SLOT in new_prefix) or \
                (new_suffix and FY_SLOT in new_suffix):
            for seq in self:
                if (seq.prefix and
                    YEAR_SLOT in seq.prefix and
                    new_prefix and
                    FY_SLOT in new_prefix) or \
                        (seq.suffix and
                         YEAR_SLOT in seq.suffix and
                         new_suffix and
                         FY_SLOT in new_suffix):
                    if seq.number_next > 1 or vals.get('number_next', 1) > 1:
                        # we are converting from %(year)s to %(fy)s
                        # and the next number is > 1; this means the
                        # sequence has already been used.
                        raise ValidationError(
                            _('You cannot change from '
                              '%s to %s '
                              'for a sequence with '
                              'next number > 1' % (YEAR_SLOT, FY_SLOT)))
        return super(Sequence, self).write(vals)
