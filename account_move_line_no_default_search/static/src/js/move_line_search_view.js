/*

   Copyright (C) 2013 Therp BV
   License: GNU AFFERO GENERAL PUBLIC LICENSE
            Version 3 or any later version

  Disable default search on the default journal and period
  in the javascript search extension on move lines in
  openobject-addons/account/static/src/js/account_move_line_quickadd.js
*/     
openerp.account_move_line_no_default_search = function (instance) {
    instance.web.account.QuickAddListView.include({
        start: function() {
            /*
              Set a hook to be honoured in our override of do_search()
              so as to prevent a default search on account move lines
              on the default period and journal.
            */
            this.block_default_search = true;
            return this._super.apply(this, arguments);
        },

        do_search: function(domain, context, group_by) {
            /*
              Check for a flag to block default search
              and reset default values when it has been found,
              then reset the blocking flag.
            */
            if (this.block_default_search === true) {
                this.current_journal = null;
                this.current_period = null;
                this.block_default_search = false;
            }
            return this._super.apply(this, arguments);
        },
    });
};
                          