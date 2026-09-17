import * as topic_title_improver from "./topic_title_improver.ts";
import * as transmit from "./transmit.ts";
export function send_message_success(
    sent_message: SentMessageData | LocalMessage,
    data: PostMessageAPIData,
): void {
    if (sent_message.type === "stream") {
        topic_title_improver.check_after_send({
            stream_id: sent_message.stream_id,
            topic: sent_message.topic,
            message_id: data.id,
        });
    }
