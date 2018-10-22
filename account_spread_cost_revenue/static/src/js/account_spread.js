odoo.define('account_spread_cost_revenue.widget', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var registry = require('web.field_registry');

    var _t = core._t;

    var AccountSpreadWidget = AbstractField.extend({
        events: _.extend({}, AbstractField.prototype.events, {
            'click': '_onClick',
        }),
        description: "",

        /**
         * @override
         */
        isSet: function () {
            return this.value !== 'unavailable';
        },

        /**
         * @override
         * @private
         */
        _render: function () {
            var className = '';
            var style = 'btn fa fa-arrow-circle-right o_spread_line ';
            var title = '';
            if (this.recordData.spread_check === 'linked') {
                className = 'o_is_linked';
                title = _t('Linked to spread');
            } else {
                title = _t('Not linked to spread');
            }
            var $button = $('<button/>', {
                type: 'button',
                title: title,
            }).addClass(style + className);
            this.$el.html($button);
        },

        /**
         * @private
         * @param {MouseEvent} event
         */
        _onClick: function (event) {
            event.stopPropagation();
            this.trigger_up('button_clicked', {
                attrs: {
                    name: 'spread_details',
                    type: 'object',
                },
                record: this.record,
            });
        },
    });

    registry.add("spread_line_widget", AccountSpreadWidget);

});
