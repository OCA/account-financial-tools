/** @odoo-module **/
import {onMounted} from "@odoo/owl";
import {AttachmentPreviewWidget} from "@attachment_preview/js/attachmentPreviewWidget.esm";
import {ListRenderer} from "@web/views/list/list_renderer";
import {bus} from "web.core";
import {patch} from "@web/core/utils/patch";

patch(ListRenderer.prototype, "account_move_line_attachment_preview.ListRenderer", {
    attachmentPreviewWidget: null,

    setup() {
        var res = this._super(...arguments);
        // Only enable preview widget if model is "account.move.line"
        this.is_move_line = this.props.list.resModel === "account.move.line";
        if (!this.is_move_line) return res;

        this.attachmentPreviewWidget = new AttachmentPreviewWidget(this);
        this.attachmentPreviewWidget.on(
            "hidden",
            this,
            this._attachmentPreviewWidgetHidden
        );
        onMounted(() => {
            // If form container is defined, it's likely that the list renderer
            // is invoked inside an "account.move" form. In this case we do
            // not initiate the widget.
            var form_view_container = $(".o_form_view_container");
            if (form_view_container.length > 0) return;
            // Preview widget added just after the move line list.
            this.attachmentPreviewWidget.insertAfter($(".o_list_renderer"));
            bus.on("open_attachment_preview", this, this._onAttachmentPreview);
        });
        return res;
    },

    _attachmentPreviewWidgetHidden() {
        // Hide the preview widget.
        if (!this.is_move_line) return;
        $(".o_list_renderer").removeClass("attachment_preview_list");
    },

    _onAttachmentPreview(attachment_id, attachment_info_list) {
        // Only preview if model is "account.move.line"
        if (!this.is_move_line) return;
        // Only preview if form container is defined, otherwise it's likely
        // that the list renderer is invoked inside an "account.move" form.
        var form_view_container = $(".o_form_view_container");
        if (form_view_container.length > 0) return;
        // Show the preview widget.
        $(".o_list_renderer").addClass("attachment_preview_list");
        if (attachment_id === undefined) {
            // Case attachment undefined: display empty widget
            this.attachmentPreviewWidget.$iframe.attr("src", "about:blank");
            $("button.attachment_preview_popout").addClass("d-none");
        } else {
            // Case attachment defined: display attachment
            this.attachmentPreviewWidget.setAttachments(
                attachment_info_list,
                attachment_id
            );
            $("button.attachment_preview_popout").removeClass("d-none");
            this.attachmentPreviewWidget.show();
            window.dispatchEvent(new Event("resize"));
        }
    },
});
