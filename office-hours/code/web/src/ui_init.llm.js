import * as message_recap from "./message_recap.ts";
import * as message_reminder from "./message_reminder.ts";
import * as topic_title_improver from "./topic_title_improver.ts";
import * as transmit from "./transmit.ts";
    message_recap.initialize();
    topic_title_improver.initialize();
    // This needs to happen after activity_ui.initialize, so that user_filter
