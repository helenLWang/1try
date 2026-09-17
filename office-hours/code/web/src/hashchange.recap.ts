import * as message_recap from "./message_recap.ts";
import * as message_view from "./message_view.ts";
        case "#scheduled":
        case "#reminders":
        case "#recap":
            blueslip.error("overlay logic skipped for: " + hash[0]);
            break;
    }

    if (base === "recap") {
        message_recap.launch();
        return;
    }
