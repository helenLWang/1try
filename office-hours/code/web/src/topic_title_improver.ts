import $ from "jquery";
import * as z from "zod/mini";

import render_topic_title_suggestion from "../templates/compose_banner/topic_title_suggestion.hbs";

import * as channel from "./channel.ts";
import * as compose_banner from "./compose_banner.ts";
import {$t} from "./i18n.ts";
import * as message_edit from "./message_edit.ts";

const suggestion_schema = z.object({
    drifted: z.boolean(),
    suggested_title: z.string(),
    reason: z.string(),
    skipped_llm: z.boolean(),
    latest_message_id: z.nullish(z.number()),
});

export function check_after_send(opts: {
    stream_id: number;
    topic: string;
    message_id: number;
}): void {
    void channel.post({
        url: "/json/messages/topic_title_suggest",
        data: {
            stream_id: JSON.stringify(opts.stream_id),
            topic: opts.topic,
        },
        success(raw_data) {
            const data = suggestion_schema.parse(raw_data);
            if (!data.drifted) {
                return;
            }
            show_suggestion_banner({
                stream_id: opts.stream_id,
                topic: opts.topic,
                message_id: data.latest_message_id ?? opts.message_id,
                suggested_title: data.suggested_title,
                reason: data.reason,
            });
        },
        error() {
            // Title suggestions are best-effort; never block sending.
        },
    });
}

function show_suggestion_banner(opts: {
    stream_id: number;
    topic: string;
    message_id: number;
    suggested_title: string;
    reason: string;
}): void {
    const $container = $("#compose_banners");
    $container.find(`.${compose_banner.CLASSNAMES.topic_title_suggestion}`).remove();
    const html = render_topic_title_suggestion({
        classname: compose_banner.CLASSNAMES.topic_title_suggestion,
        stream_id: opts.stream_id,
        topic_name: opts.topic,
        message_id: opts.message_id,
        suggested_title: opts.suggested_title,
        reason: opts.reason,
        button_text: $t({defaultMessage: "Rename topic"}),
    });
    compose_banner.append_compose_banner_to_banner_list($(html), $container);
}

export function initialize(): void {
    $("body").on(
        "click",
        `.${compose_banner.CLASSNAMES.topic_title_suggestion} .topic-title-apply-button`,
        function (this: HTMLElement) {
            const $banner = $(this).closest(
                `.${compose_banner.CLASSNAMES.topic_title_suggestion}`,
            );
            const stream_id = Number($banner.attr("data-stream-id"));
            const suggested_title = $banner.attr("data-suggested-title");
            const message_id = Number($banner.attr("data-message-id"));
            if (!suggested_title || Number.isNaN(stream_id) || Number.isNaN(message_id)) {
                return;
            }
            message_edit.move_topic_containing_message_to_stream(
                message_id,
                stream_id,
                suggested_title,
                false,
                false,
                "change_all",
            );
            $banner.remove();
        },
    );
}
