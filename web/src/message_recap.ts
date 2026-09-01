import $ from "jquery";
import * as z from "zod/mini";

import render_message_recap_body from "../templates/message_recap_body.hbs";
import render_message_recap_overlay from "../templates/message_recap_overlay.hbs";

import * as browser_history from "./browser_history.ts";
import * as channel from "./channel.ts";
import {$t} from "./i18n.ts";
import * as overlays from "./overlays.ts";

const recap_schema = z.object({
    overview: z.string(),
    unread_count: z.number(),
    truncated: z.boolean(),
    sections: z.array(
        z.object({
            title: z.string(),
            summary: z.string(),
            references: z.array(
                z.object({
                    message_id: z.number(),
                    sender: z.string(),
                    permalink: z.string(),
                }),
            ),
        }),
    ),
});

function render_status(message: string, is_error = false): void {
    const html = render_message_recap_body({
        error: is_error ? message : "",
        unread_count: is_error ? 1 : 0,
        overview: "",
        truncated: false,
        sections: [],
    });
    $("#message_recap_overlay .recap-body").html(html);
}

export function launch(): void {
    $("#recap_overlay_container").html(render_message_recap_overlay());
    overlays.open_overlay({
        name: "recap",
        $overlay: $("#message_recap_overlay"),
        on_close() {
            browser_history.exit_overlay();
        },
    });

    void channel.get({
        url: "/json/messages/recap",
        success(raw_data) {
            const data = recap_schema.parse(raw_data);
            $("#message_recap_overlay .recap-body").html(render_message_recap_body(data));
        },
        error(xhr) {
            let message = $t({defaultMessage: "Could not generate a recap."});
            try {
                const parsed = z.object({msg: z.string()}).parse(xhr.responseJSON);
                message = parsed.msg;
            } catch {
                // Keep the generic error.
            }
            render_status(message, true);
        },
    });
}

export function initialize(): void {
    // Permalink clicks leave #recap; hashchange closes the overlay.
}
