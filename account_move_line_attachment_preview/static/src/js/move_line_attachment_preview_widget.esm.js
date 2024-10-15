/** @odoo-module **/
import {registry} from "@web/core/registry";
import {query} from "web.rpc";
import {canPreview, getUrl, showPreview} from "@attachment_preview/js/utils.esm";
import {sprintf} from "@web/core/utils/strings";
import {useService} from "@web/core/utils/hooks";
import {SIZES} from "@web/core/ui/ui_service";

const {Component} = owl;

class MoveLineAttachmentWidget extends Component {
    setup() {
        super.setup();
        const ui = useService("ui");
        // Preview on new tab instead of widget in case the monitor is not big enough
        this.split_screen = ui.size >= SIZES.XXL;
    }

    async openAttachment() {
        var attachment_id = this.props.record.data.preview_attachment_id[0];
        const filename = this.props.record.data.preview_attachment_id[1];
        const split_screen = this.split_screen;

        query({
            model: "ir.attachment",
            method: "get_attachment_extension",
            args: [attachment_id],
        }).then(function (extension) {
            // In case extension not supported, emulate attachment like it's undefined
            if (!canPreview(extension)) {
                attachment_id = undefined;
            }

            // Invoke showPreview() from module attachment_preview
            showPreview(attachment_id, "", extension, filename, split_screen, [
                {
                    id: attachment_id,
                    url: sprintf("/web/content/%s", attachment_id),
                    extension: extension,
                    title: filename,
                    previewUrl: getUrl(
                        attachment_id,
                        sprintf("/web/content/%s#pagemode=none", attachment_id),
                        extension,
                        filename
                    ),
                },
            ]);
        });
    }
}

MoveLineAttachmentWidget.template =
    "account_move_line_attachment_preview.MoveLineAttachmentWidget";
registry
    .category("fields")
    .add("move_line_attachment_preview_widget", MoveLineAttachmentWidget);
