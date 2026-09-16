# ChildFind hazard analysis — ChildFind Dashcam Search

This report is the output of the LLM-assisted pipeline in `hazard_tool/` after human review of the JSON checkpoints in `workspace/`. It covers the first four analysis steps: stakeholders, values/goals, losses, world-level requirements (REQ), environmental assumptions (ASM), and software specifications (SPEC). Jackson's split: REQ is world-only; ASM is world/shared; SPEC is interface-only.

## Scale

- Stakeholders: **12**
- Losses / requirements: **64**
- Assumptions: **195**
- Specifications: **195**

Trace: stakeholder → goal → loss → REQ → ASM/SPEC.

## Stakeholder index

| ID | Name | Kind | #losses |
| --- | --- | --- | ---: |
| S01 | Dashcam owner / driver | direct | 6 |
| S02 | Missing child (search subject) | indirect | 6 |
| S03 | Parent / guardian of the missing child | indirect | 5 |
| S04 | Law enforcement / coordinating authorities | direct | 6 |
| S05 | Child-safety non-profit | direct | 5 |
| S06 | Automotive OEM | direct | 5 |
| S07 | Person-recognition contractor | direct | 5 |
| S08 | Bystander / other road user | indirect | 6 |
| S09 | Innocent lookalike child and caregiver | indirect | 5 |
| S10 | Privacy regulator / data-protection authority | indirect | 5 |
| S11 | Gas-station / edge-kiosk partner | direct | 5 |
| S12 | Rideshare / fleet driver | direct | 5 |

## S01: Dashcam owner / driver

- **Kind:** direct
- **Who:** Person who bought or was given the dashcam and whose car generates footage.
- **Why included:** They control power, pairing, opt-in, and are the first privacy surface.
- **Power / vulnerability:** medium / medium

**Values:** privacy of their own driving record; affordable operation; undistracted driving; agency over the device

**Goals:**
- `G-S01-1`: Keep the dashcam useful as accident evidence without turning the car into a public search node
- `G-S01-2`: Avoid surprise cost, crash risk, or legal blowback from ChildFind

### L-S01-1 / R-S01-1

- **Goal:** `G-S01-1` — Keep the dashcam useful as accident evidence without turning the car into a public search node
- **Loss:** The owner's everyday driving video and face embeddings are retained or reused after an authorized search ends.
- **REQ:** After an authorized search expires, people and vehicles recorded by the owner's dashcam are not identifiable from anything retained for ChildFind.
- **Harm note:** Primary product promise of the dashcam is private evidence, not a biometric database.

**ASM**
- `R-S01-1-A1`: Owners understand and can refuse enrollment in ChildFind before any search photo is applied to their footage. _(fragile: Dark-pattern opt-in and OEM-installed defaults are common.)_
- `R-S01-1-A2`: When a search ends, every copy of embeddings and crops derived from this car is actually deleted, including contractor caches. _(fragile: Contractor stacks like Rekognition often retain artifacts for debugging.)_
- `R-S01-1-A3`: A paired phone is not silently backing up raw clips to a personal cloud the owner forgot about. _(fragile: Phone OS backups are outside the dashcam company's control.)_

**SPEC**
- `R-S01-1-P1` [dashcam firmware]: On search expiry, delete on-device search photos, embeddings, and queued sighting-reports and emit a deletion-complete status.
- `R-S01-1-P2` [cloud/search coordinator]: On expiry, send a revoke message to every enrolled device and contractor endpoint that previously received that search-id.
- `R-S01-1-P3` [phone companion app]: Do not upload raw video for ChildFind; if a clip is sent, send only the still attached to an explicit sighting-report.

### L-S01-2 / R-S01-2

- **Goal:** `G-S01-2` — Avoid surprise cost, crash risk, or legal blowback from ChildFind
- **Loss:** The owner receives an unexpected cellular bill because ChildFind uploaded video through their phone.
- **REQ:** The owner is not billed for cellular data used by ChildFind beyond a limit they accepted in advance.
- **Harm note:** Data-charge fear is named in the scenario and will drive silent opt-out.

**ASM**
- `R-S01-2-A1`: The phone's cellular path is the only way a queued report leaves the car, so byte volume on that path equals user-visible cost. _(fragile: OEM telematics or Wi-Fi at home may carry traffic the user does not attribute to ChildFind.)_
- `R-S01-2-A2`: The owner notices and can act on an in-app data budget before the carrier bills them. _(fragile: Carrier bills lag; many users never open the companion app.)_
- `R-S01-2-A3`: Wi-Fi hotspots used for upload are free or already paid. _(fragile: Captive-portal Wi-Fi can still meter or fail over to cellular.)_

**SPEC**
- `R-S01-2-P1` [phone companion app]: Count ChildFind uplink bytes and stop cellular uploads when the user-set budget is reached, emitting a budget-exceeded status.
- `R-S01-2-P2` [dashcam firmware]: Prefer Wi-Fi and USB offload; mark reports as cellular-eligible only if the phone app has advertised remaining budget.
- `R-S01-2-P3` [phone companion app]: Show a pre-enrollment estimate of worst-case bytes per search-day given the local search frequency.

### L-S01-3 / R-S01-3

- **Goal:** `G-S01-2` — Avoid surprise cost, crash risk, or legal blowback from ChildFind
- **Loss:** A ChildFind match notification distracts the driver and contributes to a crash.
- **REQ:** While the vehicle is moving, the driver is not prompted to inspect a possible-match image.
- **Harm note:** Driving safety dominates child-search UX; a crash makes the feature indefensible to OEMs.

**ASM**
- `R-S01-3-A1`: The companion app can reliably know whether the vehicle is in motion from the dashcam or car speed signal. _(fragile: Bluetooth dropouts and aftermarket installs may not see speed.)_
- `R-S01-3-A2`: Passengers, not drivers, are the ones holding the phone when a prompt appears. _(fragile: The driver is often the only occupant.)_
- `R-S01-3-A3`: A sound or HUD flash is not enough to take the driver's eyes off the road. _(fragile: Any salient alert can still cause a glance.)_

**SPEC**
- `R-S01-3-P1` [phone companion app]: Suppress match-preview UI and audible alerts whenever the last speed sample is above a parked threshold.
- `R-S01-3-P2` [dashcam firmware]: Do not display match images on any in-vehicle screen; only queue a silent sighting-report.
- `R-S01-3-P3` [cloud/search coordinator]: If a human review is required, route thumbnails to the non-profit reviewer interface, not to the moving driver.

### L-S01-4 / R-S01-4

- **Goal:** `G-S01-2` — Avoid surprise cost, crash risk, or legal blowback from ChildFind
- **Loss:** After a child is found near the owner's route, the owner is blamed or sued for not reporting.
- **REQ:** An owner who had the device powered and enrolled is not treated as having a personal duty to have noticed the child.
- **Harm note:** Legal duty-to-rescue confusion will chill adoption.

**ASM**
- `R-S01-4-A1`: Courts and the public distinguish automated search from a human who saw the child. _(fragile: Headlines will not.)_
- `R-S01-4-A2`: Enrollment terms are presented before first use and retained. _(fragile: OEM-installed units may never show terms to the driver.)_
- `R-S01-4-A3`: Logs exist that show whether a search-alert was even on the device that day. _(fragile: Offline devices cannot prove they never received the alert.)_

**SPEC**
- `R-S01-4-P1` [cloud/search coordinator]: Record per-device whether a search-alert was delivered, acknowledged, and whether any sighting-report was emitted.
- `R-S01-4-P2` [phone companion app]: Display that ChildFind is automated matching, not a request that the driver watch the road for a face.
- `R-S01-4-P3` [dashcam firmware]: Keep a tamper-evident log of search-id active windows and power state.

### L-S01-5 / R-S01-5

- **Goal:** `G-S01-1` — Keep the dashcam useful as accident evidence without turning the car into a public search node
- **Loss:** Always-on matching drains the battery or fills storage so the dashcam is dead when a crash happens.
- **REQ:** The dashcam continues to record a crash loop even when a ChildFind search is active.
- **Harm note:** The product's original job is crash evidence; cannibalizing it is an organizational own-goal.

**ASM**
- `R-S01-5-A1`: The unit is on vehicle power whenever the car is moving. _(fragile: Parking-mode battery packs are common.)_
- `R-S01-5-A2`: Person detection is cheap enough that crash-loop writes still keep up. _(fragile: Low-end models cannot run both.)_
- `R-S01-5-A3`: Owners will plug the camera back in after a low-battery shutdown. _(fragile: Many will not.)_

**SPEC**
- `R-S01-5-P1` [dashcam firmware]: Treat crash-loop recording as a higher-priority write path than person-matching; drop matching when free space or voltage is below a reserved threshold.
- `R-S01-5-P2` [dashcam firmware]: Expose a power-state sample to the phone app when matching is shed.
- `R-S01-5-P3` [phone companion app]: If matching is shed, emit a search-degraded status so coordinators do not assume coverage.

### L-S01-6 / R-S01-6

- **Goal:** `G-S01-1` — Keep the dashcam useful as accident evidence without turning the car into a public search node
- **Loss:** Someone uses a fake 'missing child' enrollment to reconstruct the owner's routine from sighting metadata.
- **REQ:** A person who is not the subject of a bona fide, authority-backed search cannot obtain a trail of where the owner's car has been.
- **Harm note:** The search channel is a location oracle if authorization is weak.

**ASM**
- `R-S01-6-A1`: Only authorities/non-profit can create a search-id, and they vet the requester. _(fragile: Legal details are explicitly unsettled in the scenario.)_
- `R-S01-6-A2`: Sighting-reports are not visible to the requester, only to the coordinating unit. _(fragile: Product pressure will be to give parents a live map.)_
- `R-S01-6-A3`: A search photo of an adult cannot be submitted under a child-search type. _(fragile: Nothing in the current legal process prevents this.)_

**SPEC**
- `R-S01-6-P1` [cloud/search coordinator]: Accept new search-ids only from authenticated authority/non-profit accounts, not from end-user accounts.
- `R-S01-6-P2` [cloud/search coordinator]: Do not return sighting GPS to the original requester account; only to the coordinating-unit inbox.
- `R-S01-6-P3` [cloud/search coordinator]: Reject search packets whose metadata mark the subject as 18+ or whose photo fails a child-age gate.

## S02: Missing child (search subject)

- **Kind:** indirect
- **Who:** The child the authorized search is trying to locate.
- **Why included:** The system's stated beneficiary; harms to them are the point of safety analysis.
- **Power / vulnerability:** low / high

**Values:** physical safety; speed of recovery; dignity after recovery

**Goals:**
- `G-S02-1`: Be found while still in the area where a participating camera saw them
- `G-S02-2`: Not be further harmed by how the search is conducted or publicized

### L-S02-1 / R-S02-1

- **Goal:** `G-S02-1` — Be found while still in the area where a participating camera saw them
- **Loss:** The child remains missing even though they walked through a participating camera's view.
- **REQ:** If a missing child is physically visible in the field of view of a participating dashcam during an authorized search, the coordinating law-enforcement unit learns of that co-location while the child is still in the same local area.
- **Harm note:** This is the core mission requirement; it depends on the ML model and on radios the dashcam does not have.

**ASM**
- `R-S02-1-A1`: The dashcam is powered and the lens is unobstructed whenever the vehicle is on a public road. _(fragile: Parking-mode off, dirty lenses, and winter covers are common.)_
- `R-S02-1-A2`: The child's face or other distinctive appearance is not fully covered for the entire time they are in view. _(fragile: Abductors adapt once the system is known; weather gear hides faces.)_
- `R-S02-1-A3`: Within a short interval after the child is in view, the dashcam or paired phone obtains a network path that can deliver a small report. _(fragile: The product has no native Internet; cars park far from phones.)_
- `R-S02-1-A4`: The search packet contains a photograph that still resembles the child's current appearance. _(fragile: Children change clothes, hair, and even face shape; photos may be years old.)_
- `R-S02-1-A5`: Operators read inbound sighting notices rather than discarding them as noise. _(fragile: False-positive floods train operators to ignore the channel.)_

**SPEC**
- `R-S02-1-P1` [phone companion app]: On receiving a search-alert (photo, search-id, geographic scope, expiry), store it until expiry and forward it to the paired dashcam.
- `R-S02-1-P2` [person-recognition model]: For each in-scope person crop, output a match_score against the search photo.
- `R-S02-1-P3` [dashcam firmware]: When match_score exceeds the configured threshold, emit a sighting-report containing search-id, timestamp, GPS sample, and a cropped still.
- `R-S02-1-P4` [dashcam firmware]: If no radio is up, queue the sighting-report until the next successful Bluetooth/Wi-Fi/USB session or until search expiry.
- `R-S02-1-P5` [cloud/search coordinator]: On ingesting a sighting-report, present it in the coordinating-unit inbox with map pin and still, without requiring a second model pass that can drop it.

### L-S02-2 / R-S02-2

- **Goal:** `G-S02-2` — Not be further harmed by how the search is conducted or publicized
- **Loss:** A public or in-app alert warns an abductor, who relocates the child before officers arrive.
- **REQ:** An abductor traveling with the child does not receive a real-time notice that a nearby camera just matched the child.
- **Harm note:** Faster reports help authorities only if they are not also faster reports to the offender.

**ASM**
- `R-S02-2-A1`: Drivers do not get a push that names the child and shows 'match nearby' on a lock screen. _(fragile: Marketing will want visible 'you helped' moments.)_
- `R-S02-2-A2`: The abductor is not also a enrolled ChildFind user who receives the same search-alert photo. _(fragile: Anyone can buy a dashcam.)_
- `R-S02-2-A3`: Officers can intercept without a public crowd converging. _(fragile: Amber-style publicity is the default mental model.)_

**SPEC**
- `R-S02-2-P1` [phone companion app]: Do not display the search photo or 'match nearby' to the driver; only a generic 'search active in region' state if anything.
- `R-S02-2-P2` [cloud/search coordinator]: Hold sighting-reports in the authority inbox; do not fan them out to all enrolled devices.
- `R-S02-2-P3` [cloud/search coordinator]: Delay any public non-profit bulletin until after the coordinating unit marks the sighting as acted-on or expired.

### L-S02-3 / R-S02-3

- **Goal:** `G-S02-2` — Not be further harmed by how the search is conducted or publicized
- **Loss:** The recovered child is filmed, identified, and the still circulates on social media.
- **REQ:** After recovery, the child's face from ChildFind stills is not available to the general public.
- **Harm note:** Rescue can become a second victimization.

**ASM**
- `R-S02-3-A1`: Officers and reviewers do not screenshot the inbox. _(fragile: They will.)_
- `R-S02-3-A2`: Drivers never see a high-resolution crop they can share. _(fragile: If we prompt drivers to confirm, they see the face.)_
- `R-S02-3-A3`: News media cannot FOIA the stills in identifiable form. _(fragile: Public-records law varies and is unsettled here.)_

**SPEC**
- `R-S02-3-P1` [cloud/search coordinator]: Watermark reviewer stills and disable download by default; store access logs per still.
- `R-S02-3-P2` [cloud/search coordinator]: On case-closed, delete or irreversibly blur face crops in all ChildFind stores.
- `R-S02-3-P3` [phone companion app]: If a driver confirmation UI exists, show a time-limited low-resolution thumbnail that cannot be screenshotted via OS flags where available.

### L-S02-4 / R-S02-4

- **Goal:** `G-S02-1` — Be found while still in the area where a participating camera saw them
- **Loss:** Search resources chase a lookalike while the actual child is moved elsewhere.
- **REQ:** A false sighting does not cause the only available officers in the true vicinity to leave that vicinity.
- **Harm note:** False positives are not a victimless precision metric; they steal time from the child.

**ASM**
- `R-S02-4-A1`: Dispatch has more than one unit and will not redeploy the last local unit on a low-confidence pin. _(fragile: Rural areas have one unit.)_
- `R-S02-4-A2`: Confidence scores correspond to real-world chance it is the child. _(fragile: Face scores are poorly calibrated, especially for children.)_
- `R-S02-4-A3`: Multiple independent pins are required before a full redeploy. _(fragile: Pressure to 'do something' after a ping is high.)_

**SPEC**
- `R-S02-4-P1` [cloud/search coordinator]: Attach match_score, number of supporting frames, and 'unconfirmed' to every sighting-report shown to dispatch.
- `R-S02-4-P2` [cloud/search coordinator]: If only one unit covers the true last-known area, flag a single low-score pin as 'do not abandon last-known'.
- `R-S02-4-P3` [person-recognition model]: Output a calibrated score or an explicit low-confidence band rather than a binary match bit.

### L-S02-5 / R-S02-5

- **Goal:** `G-S02-1` — Be found while still in the area where a participating camera saw them
- **Loss:** The child is in view but disguised or too young for an adult-tuned face model, so no one looks at the frame.
- **REQ:** A missing young child who is visibly present and unoccluded in a participating camera's view is not overlooked solely because they are a small child rather than an adult.
- **Harm note:** Contractor expertise in distorted/low-light adult faces is the wrong domain.

**ASM**
- `R-S02-5-A1`: A face model trained mostly on adults transfers to toddlers and school-age children. _(fragile: It generally does not; faces and identification cues differ.)_
- `R-S02-5-A2`: Clothing, height, and companion adult are stable enough to use as a backup cue. _(fragile: Clothes change; the companion may be the abductor.)_
- `R-S02-5-A3`: The search photo is a recent, frontal, well-lit picture of this child. _(fragile: Amber packets are often old school portraits.)_

**SPEC**
- `R-S02-5-P1` [person-recognition model]: Expose a child-specific operating mode or a separate child embedding head; output match_score for the search photo under that mode.
- `R-S02-5-P2` [dashcam firmware]: When face match_score is below threshold but a person crop is in-scope, emit a top-k candidate still for reviewer UI rather than dropping the frame.
- `R-S02-5-P3` [cloud/search coordinator]: Let reviewers filter by clothing-color tags supplied in the search packet, not only by face score.

### L-S02-6 / R-S02-6

- **Goal:** `G-S02-2` — Not be further harmed by how the search is conducted or publicized
- **Loss:** The child's last known location is published so precisely that a dangerous guardian finds them first.
- **REQ:** A person who is a threat to the child does not obtain a live, meter-accurate location from ChildFind.
- **Harm note:** Custody and domestic-violence cases are common in missing-child reports.

**ASM**
- `R-S02-6-A1`: The coordinating unit has already screened which adult may receive location updates. _(fragile: Intake is rushed.)_
- `R-S02-6-A2`: Parents using the non-profit portal are the safe parents. _(fragile: Sometimes they are not.)_
- `R-S02-6-A3`: Coarse city-level public alerts are enough for the public, so precise GPS can stay inside dispatch. _(fragile: Product demos will show a live map.)_

**SPEC**
- `R-S02-6-P1` [cloud/search coordinator]: Separate the parent-status feed (search active / child recovered) from the GPS-bearing sighting inbox.
- `R-S02-6-P2` [cloud/search coordinator]: Require a two-person authority acknowledgement before any GPS-bearing still is exported.
- `R-S02-6-P3` [cloud/search coordinator]: Redact GPS to a coarse geohash on any non-dispatch role.

## S03: Parent / guardian of the missing child

- **Kind:** indirect
- **Who:** Family coordinating with the non-profit and authorities.
- **Why included:** They live with false hope, delays, and leakage of family information.
- **Power / vulnerability:** medium / high

**Values:** hope grounded in truth; speed; family privacy

**Goals:**
- `G-S03-1`: Get timely, truthful information that helps recover the child
- `G-S03-2`: Not have the family's other children or address exposed by the search

### L-S03-1 / R-S03-1

- **Goal:** `G-S03-1` — Get timely, truthful information that helps recover the child
- **Loss:** Parents are told of 'possible sightings' that are not their child, then crash emotionally and stop trusting later true reports.
- **REQ:** Parents are not notified of a sighting unless the coordinating unit has judged it worth acting on.
- **Harm note:** Unfiltered model output is not a family communication channel.

**ASM**
- `R-S03-1-A1`: Parents want every ping. _(fragile: They say that on day one and regret it by ping ten.)_
- `R-S03-1-A2`: A reviewer is available 24/7 to filter. _(fragile: Volunteer capacity is bursty.)_
- `R-S03-1-A3`: Withholding unconfirmed pings will not be described as 'the company hid sightings'. _(fragile: It will, if a child is later found near an unpublished pin.)_

**SPEC**
- `R-S03-1-P1` [cloud/search coordinator]: Parent-facing events are only those marked released-to-family by the coordinating unit, not raw sighting-reports.
- `R-S03-1-P2` [cloud/search coordinator]: Keep an audit log of withheld pins so a later inquiry can show they were reviewed.
- `R-S03-1-P3` [cloud/search coordinator]: Rate-limit family notifications to a configured maximum per hour.

### L-S03-2 / R-S03-2

- **Goal:** `G-S03-1` — Get timely, truthful information that helps recover the child
- **Loss:** A real nearby sighting sits in a queue while parents are told 'no new information'.
- **REQ:** When a sighting is judged actionable, the parents (or their designated liaison) hear about it before the information is stale.
- **Harm note:** Delay is a different failure from silence after a miss.

**ASM**
- `R-S03-2-A1`: Someone is on duty to make the 'actionable' judgment quickly. _(fragile: Night and weekend gaps.)_
- `R-S03-2-A2`: The liaison phone number in the case file still works. _(fragile: Families in crisis change phones.)_
- `R-S03-2-A3`: Parents are in a position to hear a call (not driving, not in the air). _(fragile: Not always.)_

**SPEC**
- `R-S03-2-P1` [cloud/search coordinator]: SLA-timestamp the gap between sighting ingest and released-to-family; page an on-call reviewer when the gap exceeds a threshold.
- `R-S03-2-P2` [cloud/search coordinator]: Support multiple liaison contacts and a fallback to the coordinating unit if all fail.
- `R-S03-2-P3` [phone companion app]: If the liaison is an enrolled user, deliver the released notice over the same authenticated channel as the case.

### L-S03-3 / R-S03-3

- **Goal:** `G-S03-2` — Not have the family's other children or address exposed by the search
- **Loss:** The search packet includes a home address and photos of siblings that then leak.
- **REQ:** Home address and images of children who are not the missing child do not leave the coordinating unit's custody.
- **Harm note:** Search packets are over-broad because intake copies the whole case file.

**ASM**
- `R-S03-3-A1`: Intake staff will minimize the packet to one recent photo and a last-seen area. _(fragile: They paste the whole flyer.)_
- `R-S03-3-A2`: Enrolled dashcams never display the packet. _(fragile: If drivers confirm matches, they see it.)_
- `R-S03-3-A3`: Contractor training pipelines will not scrape production packets. _(fragile: Unless contracts forbid it and we check.)_

**SPEC**
- `R-S03-3-P1` [cloud/search coordinator]: Search-alert schema allows only: search-id, subject photo(s), age band, clothing tags, geo-fence, expiry — no address field.
- `R-S03-3-P2` [cloud/search coordinator]: Strip EXIF and additional faces from photos before fan-out to devices.
- `R-S03-3-P3` [person-recognition contractor]: Contractual SPEC: production search photos are not written into the fine-tune corpus.

### L-S03-4 / R-S03-4

- **Goal:** `G-S03-2` — Not have the family's other children or address exposed by the search
- **Loss:** A sibling or the searching parent is matched as the 'abductor' or as the child and is detained.
- **REQ:** Family members who are with the missing child's siblings in public are not detained solely because a ChildFind score fired on a related face.
- **Harm note:** Related faces are a known failure mode of face systems.

**ASM**
- `R-S03-4-A1`: The system can tell a sibling from the subject. _(fragile: Often it cannot.)_
- `R-S03-4-A2`: Officers will ask a clarifying question before a stop. _(fragile: Fast-moving missing-child calls produce the opposite.)_
- `R-S03-4-A3`: The family is not simultaneously the suspect in the case. _(fragile: Sometimes they are, which needs a different protocol, not a model.)_

**SPEC**
- `R-S03-4-P1` [cloud/search coordinator]: Allow the coordinating unit to attach do-not-confuse reference photos of siblings that suppress a sighting-report if the best match is a sibling id.
- `R-S03-4-P2` [person-recognition model]: When two enrolled identities are both above threshold, output both ids rather than argmax-only.
- `R-S03-4-P3` [cloud/search coordinator]: Label such reports 'possible related-face' in the dispatch UI.

### L-S03-5 / R-S03-5

- **Goal:** `G-S03-1` — Get timely, truthful information that helps recover the child
- **Loss:** The search is quietly ended because the non-profit is flooded, and parents are not told the network is no longer looking.
- **REQ:** Parents know whether participating cameras are still being asked to search for their child.
- **Harm note:** Operational degradation must be visible to the people who think a net is out there.

**ASM**
- `R-S03-5-A1`: A search-id remaining 'open' in a database means devices still have the alert. _(fragile: Revocation can fail on offline devices.)_
- `R-S03-5-A2`: Parents interpret 'case open' as 'cameras are searching'. _(fragile: Those are different.)_
- `R-S03-5-A3`: Coverage maps shown to families match devices that actually acknowledged the alert. _(fragile: Acks never arrive from offline units.)_

**SPEC**
- `R-S03-5-P1` [cloud/search coordinator]: Expose to the liaison a coverage statistic: count of devices that acknowledged the current search-id in the geo-fence in the last T hours.
- `R-S03-5-P2` [dashcam firmware]: Whenever a radio session starts, send an ack for each still-active search-id.
- `R-S03-5-P3` [cloud/search coordinator]: If ack count in the fence drops below a floor, mark the family status 'limited camera coverage' rather than 'searching'.

## S04: Law enforcement / coordinating authorities

- **Kind:** direct
- **Who:** Officers and dispatchers who issue searches and act on sightings.
- **Why included:** They are the actuator that turns a report into a real-world intervention.
- **Power / vulnerability:** high / medium

**Values:** effective recovery; lawful process; scarce officer time

**Goals:**
- `G-S04-1`: Receive sightings that are timely, located, and worth sending a unit
- `G-S04-2`: Not create an unlawful or indefensible search record

### L-S04-1 / R-S04-1

- **Goal:** `G-S04-1` — Receive sightings that are timely, located, and worth sending a unit
- **Loss:** Dispatch burns a shift on false pins and has no unit left for a later true pin.
- **REQ:** A ChildFind notice does not cause officers to abandon a higher-priority last-known area without a human decision.
- **Harm note:** The model must not be allowed to steer cars by itself.

**ASM**
- `R-S04-1-A1`: A dispatcher always stands between a pin and a unit. _(fragile: Staffing gaps; 'auto-assign nearest unit' will be proposed.)_
- `R-S04-1-A2`: Units will wait for a confidence label they understand. _(fragile: A red map pin is treated as certainty.)_
- `R-S04-1-A3`: The last-known area is still the prior. _(fragile: Anchoring on a new ping is strong.)_

**SPEC**
- `R-S04-1-P1` [cloud/search coordinator]: Do not emit an auto-dispatch command; emit a sighting-notice that requires an acknowledge-to-assign action.
- `R-S04-1-P2` [cloud/search coordinator]: Show last-known area and the new pin on the same map with the unconfirmed label.
- `R-S04-1-P3` [person-recognition model]: Provide match_score on the notice, not a binary 'found'.

### L-S04-2 / R-S04-2

- **Goal:** `G-S04-1` — Receive sightings that are timely, located, and worth sending a unit
- **Loss:** A true sighting arrives hours later, after the child has left the area.
- **REQ:** When a participating camera had the child in view, dispatch has the notice while a search of that area can still succeed.
- **Harm note:** Connectivity, not just accuracy, sets whether 'faster is more useful' is true.

**ASM**
- `R-S04-2-A1`: The paired phone is in the car with Bluetooth up. _(fragile: Phones are in houses, offices, and pockets far from parked cars.)_
- `R-S04-2-A2`: Search-alerts are already on the device before the child is seen, so matching is local. _(fragile: Without Internet, the alert may arrive after the footage is overwritten.)_
- `R-S04-2-A3`: Loop footage is retained long enough for a delayed alert to be applied retroactively. _(fragile: Cheap units keep minutes, not hours.)_

**SPEC**
- `R-S04-2-P1` [cloud/search coordinator]: Fan out search-alerts to devices that last reported a GPS sample inside an expanded fence, not only to devices currently online.
- `R-S04-2-P2` [dashcam firmware]: On receiving a search-alert, run matching over retained loop footage for the alert's time window, not only over future frames.
- `R-S04-2-P3` [phone companion app]: When a radio session starts, drain the sighting-report queue before other telemetry.

### L-S04-3 / R-S04-3

- **Goal:** `G-S04-2` — Not create an unlawful or indefensible search record
- **Loss:** A stop or search based on ChildFind is thrown out, and the case is damaged.
- **REQ:** Officers acting on a ChildFind notice can show a lawful, purpose-limited, time-bounded authorization for that search-id.
- **Harm note:** Legal details are unsettled; the machine must still leave a paper trail.

**ASM**
- `R-S04-3-A1`: An authorized search-id corresponds to a real missing-child case, not a fishing expedition. _(fragile: Mission creep is a stated risk.)_
- `R-S04-3-A2`: The geo-fence and expiry on the alert match the warrant or policy instrument. _(fragile: Copy-paste fences will be statewide 'just in case'.)_
- `R-S04-3-A3`: Device logs are admissible and complete. _(fragile: Offline gaps look like spoliation.)_

**SPEC**
- `R-S04-3-P1` [cloud/search coordinator]: Persist the legal/authorization token, geo-fence, and expiry with the search-id and show them on every sighting-notice.
- `R-S04-3-P2` [dashcam firmware]: Refuse to run matching if the search-alert lacks expiry or authorization-id fields.
- `R-S04-3-P3` [cloud/search coordinator]: Export a chain-of-custody package: alert, device ack, still, GPS, timestamps.

### L-S04-4 / R-S04-4

- **Goal:** `G-S04-2` — Not create an unlawful or indefensible search record
- **Loss:** The same pipeline is reused for shoplifting, immigration, or protest monitoring.
- **REQ:** Person matching on consumer dashcams is not applied to a purpose other than an authorized missing-child search.
- **Harm note:** Once the camera network exists, other agencies will ask.

**ASM**
- `R-S04-4-A1`: Contractual purpose limitation will be respected under political pressure. _(fragile: It often is not.)_
- `R-S04-4-A2`: A 'missing child' label on a packet means the subject is a child in a genuine case. _(fragile: Labels can be lied about.)_
- `R-S04-4-A3`: OEMs and the non-profit will walk away if purpose expands, creating a real brake. _(fragile: Unless revenue replaces them.)_

**SPEC**
- `R-S04-4-P1` [cloud/search coordinator]: Hard-code the search type enum to missing-child and drop any other type at the API boundary.
- `R-S04-4-P2` [dashcam firmware]: Ignore search-alerts whose type field is not missing-child.
- `R-S04-4-P3` [cloud/search coordinator]: Publish an append-only audit of search-ids issued (metadata only) to the non-profit's compliance role.

### L-S04-5 / R-S04-5

- **Goal:** `G-S04-1` — Receive sightings that are timely, located, and worth sending a unit
- **Loss:** Operators ignore the inbox because yesterday it was 400 low-quality stills.
- **REQ:** The coordinating unit's ChildFind inbox remains usable on a typical search day (on the order of the national Amber rate, not a continuous firehose).
- **Harm note:** Human attention is part of the environment the REQ depends on.

**ASM**
- `R-S04-5-A1`: Thresholding will keep volume near the 1-alert/day national rate times a small match rate. _(fragile: If we lower threshold for recall, volume explodes locally.)_
- `R-S04-5-A2`: Reviewers will not rubber-stamp to clear the queue. _(fragile: They will if measured on throughput.)_
- `R-S04-5-A3`: Geographic scoping keeps a rural desk from seeing a coastal city's matches. _(fragile: A national inbox is simpler to build.)_

**SPEC**
- `R-S04-5-P1` [cloud/search coordinator]: Shard the inbox by coordinating-unit geo-fence; do not show out-of-fence stills.
- `R-S04-5-P2` [dashcam firmware]: Cap queued candidate stills per search-id per hour and mark overflow as count-only.
- `R-S04-5-P3` [cloud/search coordinator]: Surface queue depth next to each case so coordinators see overload as a first-class status.

### L-S04-6 / R-S04-6

- **Goal:** `G-S04-1` — Receive sightings that are timely, located, and worth sending a unit
- **Loss:** Traditional canvassing stops because 'the cameras would have seen them'.
- **REQ:** Investigators continue non-camera search activity even while ChildFind is active.
- **Harm note:** Automation complacency is an environmental/organizational failure.

**ASM**
- `R-S04-6-A1`: Command staff treat ChildFind as one sensor among many. _(fragile: Vendors will sell it as coverage.)_
- `R-S04-6-A2`: Coverage maps are not mistaken for 'every street is enrolled'. _(fragile: They will be.)_
- `R-S04-6-A3`: A degraded/offline status is visible in the same UI as pins. _(fragile: Separate dashboards get ignored.)_

**SPEC**
- `R-S04-6-P1` [cloud/search coordinator]: Show enrolled-device density, not just pins, on the dispatch map.
- `R-S04-6-P2` [cloud/search coordinator]: If ack coverage is below a floor, banner 'camera network not a substitute for canvass'.
- `R-S04-6-P3` [phone companion app]: Report last-seen GPS only when the device was actually matching, not when it was powered off.

## S05: Child-safety non-profit

- **Kind:** direct
- **Who:** Partner that coordinates searches and public trust around child recovery.
- **Why included:** They hold the mission and the photo pipeline; a scandal ends the feature.
- **Power / vulnerability:** high / medium

**Values:** mission success; public trust; volunteer sustainability

**Goals:**
- `G-S05-1`: Increase recoveries without becoming a surveillance brand
- `G-S05-2`: Keep volunteers and donors engaged

### L-S05-1 / R-S05-1

- **Goal:** `G-S05-1` — Increase recoveries without becoming a surveillance brand
- **Loss:** A privacy scandal ends the partnership and the search capability with it.
- **REQ:** Bystanders and families do not experience a ChildFind privacy incident that becomes public during the partnership.
- **Harm note:** Trust is the non-profit's actual capital.

**ASM**
- `R-S05-1-A1`: The manufacturer will not ship a 'growth' feature that fans photos to drivers. _(fragile: Marketing alignment is not guaranteed.)_
- `R-S05-1-A2`: Edge partners will not advertise 'we help find kids' with customer CCTV stills. _(fragile: They will want the PR.)_
- `R-S05-1-A3`: A single incident will be contained by contracts. _(fragile: Screenshots travel faster than contracts.)_

**SPEC**
- `R-S05-1-P1` [cloud/search coordinator]: Bind photo display to reviewer and dispatch roles; no public CDN URLs for stills.
- `R-S05-1-P2` [cloud/search coordinator]: Require the non-profit compliance role to sign off on any new output surface (driver UI, kiosk screen, parent map).
- `R-S05-1-P3` [edge kiosk]: Do not show search photos or match stills on a customer-facing screen.

### L-S05-2 / R-S05-2

- **Goal:** `G-S05-2` — Keep volunteers and donors engaged
- **Loss:** Donors leave after a high-profile miss that is blamed on the non-profit 'using AI'.
- **REQ:** The public description of a miss does not claim that cameras covered a place they did not.
- **Harm note:** Overclaiming coverage is how AI partnerships die.

**ASM**
- `R-S05-2-A1`: Press statements will be coordinated with coverage facts. _(fragile: Speed of news vs slowness of logs.)_
- `R-S05-2-A2`: The manufacturer will not claim 'citywide' in ads. _(fragile: They might.)_
- `R-S05-2-A3`: Families will not be used as ad testimonials while a search is open. _(fragile: Growth teams will ask.)_

**SPEC**
- `R-S05-2-P1` [cloud/search coordinator]: Export a coverage-fact sheet per case (ack counts, fences, outages) to the non-profit comms role.
- `R-S05-2-P2` [cloud/search coordinator]: Block in-product prompts that ask families for testimonials until case-closed.
- `R-S05-2-P3` [phone companion app]: Consumer marketing copy in-app must pull the same coverage numbers rather than a static slogan.

### L-S05-3 / R-S05-3

- **Goal:** `G-S05-2` — Keep volunteers and donors engaged
- **Loss:** Volunteer reviewers quit because the queue is mostly not-the-child stills.
- **REQ:** Volunteer review load stays within a published per-search budget the non-profit accepted.
- **Harm note:** Human review is a mitigation for model errors; it can become the new hazard.

**ASM**
- `R-S05-3-A1`: Volunteers are interchangeable and always available. _(fragile: They are not.)_
- `R-S05-3-A2`: Top-k stills are a small number. _(fragile: k grows when recall panic hits.)_
- `R-S05-3-A3`: Reviewing children's faces all day is psychologically tolerable. _(fragile: It may not be.)_

**SPEC**
- `R-S05-3-P1` [cloud/search coordinator]: Enforce a per-search cap on stills sent to volunteers; overflow goes to a paid on-call role.
- `R-S05-3-P2` [cloud/search coordinator]: Show estimated remaining queue time to the volunteer before they accept a shift.
- `R-S05-3-P3` [cloud/search coordinator]: Provide a skip/escalate control so a volunteer can drop a still without it disappearing.

### L-S05-4 / R-S05-4

- **Goal:** `G-S05-1` — Increase recoveries without becoming a surveillance brand
- **Loss:** The company uses the non-profit's name to sell dashcams, then ships a weaker privacy mode than the partnership described.
- **REQ:** Devices advertised under the partnership actually run the same matching and retention rules the non-profit signed.
- **Harm note:** SKU fragmentation is how ethics agreements die.

**ASM**
- `R-S05-4-A1`: One firmware train serves OEM and consumer SKUs. _(fragile: Low-end SKUs will strip 'expensive' deletion and ack features.)_
- `R-S05-4-A2`: The non-profit can audit production configs. _(fragile: Unless the contract is logo-only.)_
- `R-S05-4-A3`: Owners cannot disable deletion while leaving matching on. _(fragile: A 'privacy off / matching on' toggle will be requested.)_

**SPEC**
- `R-S05-4-P1` [dashcam firmware]: Refuse to enable matching unless retention-limit and ack features are compiled in and healthy.
- `R-S05-4-P2` [cloud/search coordinator]: Expose a config-attestation hash per device that the non-profit can sample.
- `R-S05-4-P3` [phone companion app]: Do not offer a matching-on / deletion-off combination.

### L-S05-5 / R-S05-5

- **Goal:** `G-S05-1` — Increase recoveries without becoming a surveillance brand
- **Loss:** Search photos of children circulate in volunteer Slack, press, or the contractor's demo reel.
- **REQ:** A child's search photo is not available to people outside the authorized search roles.
- **Harm note:** Distribution, not collection, is where most leaks happen.

**ASM**
- `R-S05-5-A1`: Reviewer tools block download and external share. _(fragile: People use phones to photograph monitors.)_
- `R-S05-5-A2`: The contractor's sales team cannot pull production examples. _(fragile: They will ask for 'realistic' demos.)_
- `R-S05-5-A3`: Expired searches vanish from every replica, including backups, within a stated window. _(fragile: Backups lag.)_

**SPEC**
- `R-S05-5-P1` [cloud/search coordinator]: Issue short-lived, watermarked, non-downloadable still URLs bound to reviewer identity.
- `R-S05-5-P2` [person-recognition contractor]: Production photos are not readable by the vendor's sales or research roles.
- `R-S05-5-P3` [cloud/search coordinator]: On expiry, delete photos from object storage and enqueue backup-tombstones.

## S06: Automotive OEM

- **Kind:** direct
- **Who:** Car manufacturer that may factory-install the dashcam.
- **Why included:** OEM contracts are the company's growth path and a vehicle-safety liability path.
- **Power / vulnerability:** high / low

**Values:** brand safety; vehicle safety regulation; warranty cost

**Goals:**
- `G-S06-1`: Offer ChildFind as a differentiator without creating a recall
- `G-S06-2`: Not be seen as shipping a mass-surveillance car

### L-S06-1 / R-S06-1

- **Goal:** `G-S06-1` — Offer ChildFind as a differentiator without creating a recall
- **Loss:** A crash is attributed to a ChildFind prompt or to compute starving the vehicle electrical system.
- **REQ:** ChildFind does not present driving-relevant alerts to the driver and does not take the vehicle electrical system below the OEM's reserved budget.
- **Harm note:** NHTSA will not care that the ML model was accurate.

**ASM**
- `R-S06-1-A1`: The dashcam is on an accessory circuit the OEM sized for it. _(fragile: Aftermarket installs share cigarette-lighter circuits with other loads.)_
- `R-S06-1-A2`: Infotainment will not be used as the match UI. _(fragile: It is the tempting place to put a big picture.)_
- `R-S06-1-A3`: Parking-mode current draw stays within the OEM spec. _(fragile: Always-on matching will not.)_

**SPEC**
- `R-S06-1-P1` [dashcam firmware]: Honor an OEM current-budget sample; shed matching before crash-loop recording.
- `R-S06-1-P2` [dashcam firmware]: No video output of match crops onto infotainment while gear is not Park.
- `R-S06-1-P3` [phone companion app]: No driver-facing match UI while speed > 0, as in R-S01-3.

### L-S06-2 / R-S06-2

- **Goal:** `G-S06-2` — Not be seen as shipping a mass-surveillance car
- **Loss:** Press describes the car as a rolling face-recognition network; OEM cancels the SKU.
- **REQ:** Uninvolved people photographed by the car are not identified by name or persistent id as part of ChildFind.
- **Harm note:** OEM brand risk is mostly about bystanders, not about missing children.

**ASM**
- `R-S06-2-A1`: Matching runs only while a search-id is active in the car's region. _(fragile: A 'pre-index everyone for speed' optimization will be proposed.)_
- `R-S06-2-A2`: No gallery of embeddings is kept between searches. _(fragile: On-device galleries make matching cheaper.)_
- `R-S06-2-A3`: License-plate plus face fusion will not be added as a 'bonus'. _(fragile: It will be asked for.)_

**SPEC**
- `R-S06-2-P1` [dashcam firmware]: Do not persist person embeddings across search-ids; wipe on expiry.
- `R-S06-2-P2` [person-recognition model]: Do not output a name or identity other than match_score vs the current search photo.
- `R-S06-2-P3` [dashcam firmware]: Do not run plate recognition as part of the ChildFind path unless a separate, authorized field is present in the search-alert.

### L-S06-3 / R-S06-3

- **Goal:** `G-S06-1` — Offer ChildFind as a differentiator without creating a recall
- **Loss:** Warranty returns spike because ChildFind overheats or bricks low-end units.
- **REQ:** Low-end hardware either performs matching within thermal limits or reports itself as non-participating rather than failing.
- **Harm note:** Heterogeneous compute is in the scenario.

**ASM**
- `R-S06-3-A1`: A single model will run on every SKU. _(fragile: It will not.)_
- `R-S06-3-A2`: Thermal throttling still leaves crash recording intact. _(fragile: Not if the SoC is shared.)_
- `R-S06-3-A3`: Owners accept that some SKUs only upload clips to the phone for matching. _(fragile: They must be told.)_

**SPEC**
- `R-S06-3-P1` [dashcam firmware]: If temperature or utilization exceeds a SKU-specific limit, stop matching and emit search-degraded.
- `R-S06-3-P2` [phone companion app]: Offer on-phone matching as a fallback only when the user has accepted the data/compute cost.
- `R-S06-3-P3` [cloud/search coordinator]: Treat search-degraded devices as uncovered in the density map.

### L-S06-4 / R-S06-4

- **Goal:** `G-S06-1` — Offer ChildFind as a differentiator without creating a recall
- **Loss:** A regulator treats always-on interior/cabin matching as illegal surveillance in the car.
- **REQ:** Cabin-facing cameras, if present, are not used to match passengers for ChildFind.
- **Harm note:** Many 'dashcams' are dual-channel.

**ASM**
- `R-S06-4-A1`: ChildFind uses only the outward road camera. _(fragile: A cabin cam would 'help' with kidnapped-in-car cases.)_
- `R-S06-4-A2`: Passengers consented because they sat down. _(fragile: They did not.)_
- `R-S06-4-A3`: OEM privacy mode already disables the cabin cam. _(fragile: Owners re-enable it for driver monitoring.)_

**SPEC**
- `R-S06-4-P1` [dashcam firmware]: Bind the ChildFind matcher input to the outward camera device id only.
- `R-S06-4-P2` [dashcam firmware]: Refuse search-alert processing if the configured source is a cabin device.
- `R-S06-4-P3` [phone companion app]: Show which camera is enrolled; no toggle to include cabin for ChildFind.

### L-S06-5 / R-S06-5

- **Goal:** `G-S06-2` — Not be seen as shipping a mass-surveillance car
- **Loss:** Dealers cannot explain the feature, so they disable it, leaving advertised coverage fictional.
- **REQ:** A car advertised as ChildFind-capable is actually enrolled or is labeled at sale as not enrolled.
- **Harm note:** Channel fiction shows up as empty density maps.

**ASM**
- `R-S06-5-A1`: Enrollment happens at delivery with a real owner account. _(fragile: It will be skipped.)_
- `R-S06-5-A2`: A factory default of 'on' is acceptable. _(fragile: Privacy law and the owner may disagree.)_
- `R-S06-5-A3`: Dealers will not promise coverage the car does not have. _(fragile: They will.)_

**SPEC**
- `R-S06-5-P1` [phone companion app]: Enrollment requires an explicit owner action after delivery; factory default is matching-off.
- `R-S06-5-P2` [cloud/search coordinator]: OEM inventory APIs must not mark a VIN as covering a fence until a device ack exists.
- `R-S06-5-P3` [cloud/search coordinator]: Provide a dealer-safe status: not-enrolled vs enrolled, with no search photos.

## S07: Person-recognition contractor

- **Kind:** direct
- **Who:** Vendor that supplies and helps fine-tune the person/face recognition stack.
- **Why included:** Their model is the ML component; their cloud/on-device choices change the threat model.
- **Power / vulnerability:** medium / low

**Values:** model IP; reputational accuracy; limited downstream liability

**Goals:**
- `G-S07-1`: Deliver a usable person-recognition stack without absorbing the manufacturer's product risk
- `G-S07-2`: Keep training data and weights from leaking via on-device deployment

### L-S07-1 / R-S07-1

- **Goal:** `G-S07-2` — Keep training data and weights from leaking via on-device deployment
- **Loss:** On-device weights are extracted from a consumer dashcam and republished.
- **REQ:** A person who buys a dashcam does not obtain a working copy of the contractor's production model weights.
- **Harm note:** Offline deployment is explicitly on the table in the scenario.

**ASM**
- `R-S07-1-A1`: Hardware is a secure enclave that owners cannot dump. _(fragile: Dashcams are cheap and routinely rooted.)_
- `R-S07-1-A2`: A distilled on-device model has no value if stolen. _(fragile: It still encodes the contractor's data.)_
- `R-S07-1-A3`: Matching can stay on the phone, which has a better TEE than the camera. _(fragile: Phones are also jailbroken; it also increases data movement.)_

**SPEC**
- `R-S07-1-P1` [person-recognition model]: Ship an on-device extractor/embedder that is not the full cloud model; keep the gallery comparison key on the coordinator if possible.
- `R-S07-1-P2` [dashcam firmware]: Store weights in a locked partition and refuse to export them over USB debug.
- `R-S07-1-P3` [person-recognition contractor]: Watermark embeddings so a leaked model can be attributed.

### L-S07-2 / R-S07-2

- **Goal:** `G-S07-1` — Deliver a usable person-recognition stack without absorbing the manufacturer's product risk
- **Loss:** Public audits show large error gaps on children or on darker skin, and the contractor is named.
- **REQ:** Disparities in whether a visible missing child is reported are not systematically associated with the child's age band or skin tone in deployed searches.
- **Harm note:** This is a world-level fairness requirement, not 'equal F1 on a benchmark'.

**ASM**
- `R-S07-2-A1`: Adult mugshot benchmarks predict child dashcam performance. _(fragile: They do not.)_
- `R-S07-2-A2`: Low-light robustness advertised by the contractor covers streetlights and headlights equally across skin tones. _(fragile: It often does not.)_
- `R-S07-2-A3`: We can collect child dashcam labels legally. _(fragile: Children's data is specially protected.)_

**SPEC**
- `R-S07-2-P1` [person-recognition model]: Report match_score distributions sliced by age-band and lighting tags on a sealed evaluation set, not only a single AUC.
- `R-S07-2-P2` [cloud/search coordinator]: Log (search-id, age-band, lighting-tag, match_score, reviewer-decision) for disparity review, without storing extra identity.
- `R-S07-2-P3` [dashcam firmware]: Attach a lighting/quality tag to each crop so slices are possible.

### L-S07-3 / R-S07-3

- **Goal:** `G-S07-1` — Deliver a usable person-recognition stack without absorbing the manufacturer's product risk
- **Loss:** Latency or downtime of a cloud Rekognition-like path misses the useful window.
- **REQ:** A sighting is not lost solely because a cloud inference endpoint was slow or unreachable.
- **Harm note:** The dashcam is already offline; adding a cloud round-trip stacks two radios.

**ASM**
- `R-S07-3-A1`: On-device or on-phone inference is always available as fallback. _(fragile: Low-end SKUs cannot run it.)_
- `R-S07-3-A2`: Cloud batching is fine because searches are rare. _(fragile: When a search is on, latency still matters.)_
- `R-S07-3-A3`: The contractor's SLA includes dashcam-like blur and night frames. _(fragile: Their SLA may be clean studio images.)_

**SPEC**
- `R-S07-3-P1` [dashcam firmware]: Run local matching when a search-alert is present; do not block on a cloud round-trip.
- `R-S07-3-P2` [phone companion app]: If local matching is incapable, queue crops and retry cloud inference without dropping the GPS/time that makes the report a sighting.
- `R-S07-3-P3` [person-recognition contractor]: Expose an offline SDK path, not only a hosted API.

### L-S07-4 / R-S07-4

- **Goal:** `G-S07-2` — Keep training data and weights from leaking via on-device deployment
- **Loss:** Fine-tuning uses photos the contractor had no license to train on, and a lawsuit lands on both companies.
- **REQ:** A child's photo provided for a live search is not used to train or advertise a model.
- **Harm note:** Live searches are the most sensitive data the contractor will ever see.

**ASM**
- `R-S07-4-A1`: Default cloud settings do not log production images into a training bucket. _(fragile: Many hosted APIs do, unless contracted off.)_
- `R-S07-4-A2`: Fine-tune infrastructure the manufacturer operates is isolated from the vendor's other customers. _(fragile: Shared GPUs and datasets are cheaper.)_
- `R-S07-4-A3`: Expired search photos cannot be recovered from experiment trackers. _(fragile: Weights-and-biases style tools hoard samples.)_

**SPEC**
- `R-S07-4-P1` [person-recognition contractor]: API option and default: do not persist request images; return only scores.
- `R-S07-4-P2` [cloud/search coordinator]: Manufacturer-operated fine-tune jobs read only a licensed corpus, never the live search-alert store.
- `R-S07-4-P3` [cloud/search coordinator]: Block experiment-tracker uploads of search-alert images at the gateway.

### L-S07-5 / R-S07-5

- **Goal:** `G-S07-1` — Deliver a usable person-recognition stack without absorbing the manufacturer's product risk
- **Loss:** The contractor is subpoenaed as the 'face recognition company' for every ChildFind case.
- **REQ:** The contractor does not receive a copy of every production video frame, only what the manufacturer must send to meet a specified inference path.
- **Harm note:** Data minimization is also liability minimization.

**ASM**
- `R-S07-5-A1`: On-device inference means the vendor never sees production frames. _(fragile: Updates and 'helpdesk' uploads will reintroduce them.)_
- `R-S07-5-A2`: A subpoena to the manufacturer is enough for courts. _(fragile: Plaintiffs will sue everyone in the chain.)_
- `R-S07-5-A3`: Support logs can be sampled without full video. _(fragile: Engineers will ask for the clip.)_

**SPEC**
- `R-S07-5-P1` [dashcam firmware]: Default inference path keeps frames on-device; cloud path sends crops not full video.
- `R-S07-5-P2` [person-recognition contractor]: Support channel accepts quality tags and scores, not raw clips, unless a named incident ticket is opened.
- `R-S07-5-P3` [cloud/search coordinator]: Separate the manufacturer case file from any vendor ticket so a vendor subpoena does not automatically include GPS trails.

## S08: Bystander / other road user

- **Kind:** indirect
- **Who:** Pedestrians, other drivers, and passengers whose faces appear in footage.
- **Why included:** Most faces the model will ever see are not missing children; they bear biometric risk.
- **Power / vulnerability:** low / high

**Values:** anonymity in public space; purpose limitation; no secondary use

**Goals:**
- `G-S08-1`: Move through streets without being biometrically identified by a consumer camera network
- `G-S08-2`: Not have an image from a sensitive place reused later

### L-S08-1 / R-S08-1

- **Goal:** `G-S08-1` — Move through streets without being biometrically identified by a consumer camera network
- **Loss:** A bystander's face is embedded and kept so they can be re-identified after the search ends.
- **REQ:** A person who is not the subject of an authorized search is not assigned a persistent identity from ChildFind processing.
- **Harm note:** This is the mass-surveillance requirement hiding inside a child-safety feature.

**ASM**
- `R-S08-1-A1`: We only compare to one search photo, so we are not identifying bystanders. _(fragile: Comparison still detects and embeds every face.)_
- `R-S08-1-A2`: Embeddings without names are not identifications. _(fragile: They are linkable identifiers.)_
- `R-S08-1-A3`: People in public have no remaining biometric expectation. _(fragile: Regulators disagree, especially for children bystanders.)_

**SPEC**
- `R-S08-1-P1` [dashcam firmware]: Do not store embeddings except the current search photo's embedding and in-memory crops of the current matching window.
- `R-S08-1-P2` [person-recognition model]: Output match_score versus the search photo only; do not output a gallery id for non-matches.
- `R-S08-1-P3` [dashcam firmware]: Zero in-memory crops when the search-id expires or the vehicle powers down.

### L-S08-2 / R-S08-2

- **Goal:** `G-S08-2` — Not have an image from a sensitive place reused later
- **Loss:** A still of a bystander at a clinic, shelter, or protest is later reused in another investigation.
- **REQ:** ChildFind stills are not available to reuse for a purpose other than the originating missing-child search.
- **Harm note:** Secondary use is how dashcams become police databases.

**ASM**
- `R-S08-2-A1`: Retention limits will be honored by every agency copy. _(fragile: Once emailed, they will not.)_
- `R-S08-2-A2`: The original crash-evidence recording is a separate store with its own warrant process. _(fragile: Police will ask to 'just look at ChildFind' instead of getting a warrant for the loop.)_
- `R-S08-2-A3`: Edge kiosks do not keep a longer archive than the car. _(fragile: Centralizing makes longer retention tempting.)_

**SPEC**
- `R-S08-2-P1` [cloud/search coordinator]: Bind every still to a search-id and refuse API access with a different purpose token.
- `R-S08-2-P2` [cloud/search coordinator]: Do not provide a free-text 'search all historical stills' endpoint.
- `R-S08-2-P3` [edge kiosk]: Purge cached clips on the same expiry as the car; no partner-side archive.

### L-S08-3 / R-S08-3

- **Goal:** `G-S08-1` — Move through streets without being biometrically identified by a consumer camera network
- **Loss:** People avoid streets, schools, or clinics known to be dense with enrolled cars.
- **REQ:** The public is not given a live map of which cars are currently matching faces.
- **Harm note:** Transparency can itself become a chilling-effect channel.

**ASM**
- `R-S08-3-A1`: Coverage maps for dispatch will stay inside the authority UI. _(fragile: Open-data pressure and marketing maps.)_
- `R-S08-3-A2`: A blinking LED on the dashcam is not a usable tracker of matching state. _(fragile: It still signals something.)_
- `R-S08-3-A3`: Journalists will not scrape enrollment density from leaked APIs. _(fragile: They will try.)_

**SPEC**
- `R-S08-3-P1` [cloud/search coordinator]: Public stats, if any, are delayed and aggregated at city level, not live car pins.
- `R-S08-3-P2` [phone companion app]: Do not show other users' enrollment on a map.
- `R-S08-3-P3` [dashcam firmware]: Do not advertise matching-active over Bluetooth beyond the paired phone.

### L-S08-4 / R-S08-4

- **Goal:** `G-S08-2` — Not have an image from a sensitive place reused later
- **Loss:** A child bystander's face is enrolled into a gallery 'to improve child recall' without a parent.
- **REQ:** Children who are not the missing child are not added to any biometric gallery from dashcam footage.
- **Harm note:** The obvious ML fix (more child faces) is itself a harm.

**ASM**
- `R-S08-4-A1`: We can use crash-loop video as extra child training data because the owner consented. _(fragile: The child bystander did not.)_
- `R-S08-4-A2`: Blurred or synthetic children are enough to improve recall. _(fragile: May be true; should be tried before harvesting.)_
- `R-S08-4-A3`: Parents of bystanders will opt in via a public campaign. _(fragile: Response rates will be tiny and biased.)_

**SPEC**
- `R-S08-4-P1` [person-recognition contractor]: Fine-tune corpora exclude unlabeled dashcam faces of minors.
- `R-S08-4-P2` [dashcam firmware]: No 'upload hard examples' path for non-match crops.
- `R-S08-4-P3` [cloud/search coordinator]: Reject training-ingest jobs whose source is production ChildFind crops.

### L-S08-5 / R-S08-5

- **Goal:** `G-S08-1` — Move through streets without being biometrically identified by a consumer camera network
- **Loss:** An employer, landlord, or immigration officer obtains a still showing where a bystander was.
- **REQ:** A ChildFind still of a bystander is not obtainable by a private party who wants to know where that person was.
- **Harm note:** The threat is not only the state.

**ASM**
- `R-S08-5-A1`: Only dispatch can see stills. _(fragile: Parents, volunteers, drivers, and kiosk staff may also see them.)_
- `R-S08-5-A2`: A still without a name cannot be linked. _(fragile: Reverse image search and acquaintance recognition exist.)_
- `R-S08-5-A3`: NDAs bind volunteers. _(fragile: NDAs do not bind screenshots.)_

**SPEC**
- `R-S08-5-P1` [cloud/search coordinator]: Minimize faces in a crop (subject-centered) and strip background license plates where feasible before a still leaves the device.
- `R-S08-5-P2` [cloud/search coordinator]: Watermark stills with the viewer id.
- `R-S08-5-P3` [phone companion app]: Drivers who confirm a match never receive a share button or a saved copy.

### L-S08-6 / R-S08-6

- **Goal:** `G-S08-1` — Move through streets without being biometrically identified by a consumer camera network
- **Loss:** A bystander is stopped because they were next to a possible match in the same frame.
- **REQ:** Presence in the same video frame as a possible match does not by itself cause a bystander to be treated as a suspect companion.
- **Harm note:** Association is a world harm the model does not even 'predict' explicitly.

**ASM**
- `R-S08-6-A1`: Officers will treat other people in the crop as scenery. _(fragile: They will ask 'who is that adult'.)_
- `R-S08-6-A2`: Crops can be tightly boxed on the candidate child. _(fragile: Wide context helps reviewers, which conflicts.)_
- `R-S08-6-A3`: Companion identification is out of scope. _(fragile: Someone will add 'abductor model' later.)_

**SPEC**
- `R-S08-6-P1` [dashcam firmware]: Default sighting still is a tight crop; a wider context image is available only behind a second dispatcher action.
- `R-S08-6-P2` [cloud/search coordinator]: UI copy: 'other people in the frame are not identified and are not suspects'.
- `R-S08-6-P3` [person-recognition model]: Do not emit identities or match_scores for additional faces in the context image.

## S09: Innocent lookalike child and caregiver

- **Kind:** indirect
- **Who:** A child or adult who resembles the search photo, and the adult with them.
- **Why included:** False positives cause police contact, which is a different harm than a miss.
- **Power / vulnerability:** low / high

**Values:** freedom from mistaken police contact; reputation; caregiver liberty

**Goals:**
- `G-S09-1`: Go about daily life without being treated as the missing child or their abductor
- `G-S09-2`: Have a way to end a false identification quickly

### L-S09-1 / R-S09-1

- **Goal:** `G-S09-1` — Go about daily life without being treated as the missing child or their abductor
- **Loss:** Police stop a lookalike child in public based on a ChildFind pin.
- **REQ:** A child who is not the missing child is not stopped by police solely because a dashcam produced a possible-match notice.
- **Harm note:** False-positive harm is the one developers underweight when they optimize recall.

**ASM**
- `R-S09-1-A1`: Officers treat a possible-match notice as a lead that requires corroboration, not as an identification. _(fragile: Missing-child calls are emotional and fast.)_
- `R-S09-1-A2`: Lookalikes are rare enough that a high threshold prevents stops. _(fragile: School uniforms and age bands create many lookalikes.)_
- `R-S09-1-A3`: The caregiver can immediately show the child's identity. _(fragile: A child may have no ID; a caregiver may not be believed.)_
- `R-S09-1-A4`: The notice is shown only to dispatch, not blasted to every patrol phone as 'FOUND'. _(fragile: Someone will want a push to all units.)_

**SPEC**
- `R-S09-1-P1` [cloud/search coordinator]: Every notice is labeled 'unconfirmed possible match' and includes match_score; there is no 'FOUND' state from software alone.
- `R-S09-1-P2` [cloud/search coordinator]: Do not fan a pin to all units; send it to the coordinating desk for assignment.
- `R-S09-1-P3` [person-recognition model]: Output match_score and a recommended-threshold band; do not output a binary identity claim.
- `R-S09-1-P4` [cloud/search coordinator]: Attach the search photo next to the still so a human compares before a stop is authorized.

### L-S09-2 / R-S09-2

- **Goal:** `G-S09-1` — Go about daily life without being treated as the missing child or their abductor
- **Loss:** The caregiver is arrested as an abductor because they are walking with a lookalike.
- **REQ:** An adult accompanying a child who is not missing is not arrested solely on a ChildFind possible-match.
- **Harm note:** The 'abductor' inference is a world action with no supporting SPEC unless we invent one.

**ASM**
- `R-S09-2-A1`: There is no abductor classifier in the system. _(fragile: Feature requests will add one.)_
- `R-S09-2-A2`: Officers will not treat 'adult + matching child' as kidnapping-in-progress. _(fragile: That is a common heuristic.)_
- `R-S09-2-A3`: The true missing-child bulletin includes whether an abductor is suspected. _(fragile: Sometimes it does not.)_

**SPEC**
- `R-S09-2-P1` [cloud/search coordinator]: If the case file has no suspected-companion field, the notice UI omits any companion language.
- `R-S09-2-P2` [person-recognition model]: No abductor/companion score is emitted on the ChildFind path.
- `R-S09-2-P3` [cloud/search coordinator]: Require a dispatcher note before a companion-adult description is added to a unit's assignment.

### L-S09-3 / R-S09-3

- **Goal:** `G-S09-1` — Go about daily life without being treated as the missing child or their abductor
- **Loss:** A school or store goes into lockdown because a public app showed a nearby match.
- **REQ:** Schools and businesses do not receive automated ChildFind match alerts about children on their premises.
- **Harm note:** The blast radius of a FP includes institutions.

**ASM**
- `R-S09-3-A1`: There is no public match feed. _(fragile: Someone will build a Twitter bot.)_
- `R-S09-3-A2`: Drivers will not film the stop and tag the school. _(fragile: They will.)_
- `R-S09-3-A3`: The non-profit will not 'partner' with school apps. _(fragile: It is a tempting expansion.)_

**SPEC**
- `R-S09-3-P1` [cloud/search coordinator]: No third-party webhook for match events other than the coordinating unit.
- `R-S09-3-P2` [phone companion app]: No share-to-social control on stills or pins.
- `R-S09-3-P3` [cloud/search coordinator]: Rate-limit and watermark to make scraping a live feed unattractive.

### L-S09-4 / R-S09-4

- **Goal:** `G-S09-2` — Have a way to end a false identification quickly
- **Loss:** A lookalike's photo remains associated with the case online after the true child is found.
- **REQ:** Once a possible-match is judged to be the wrong child, that still is not kept as part of a public or family-visible case story.
- **Harm note:** Correction has to be as operational as detection.

**ASM**
- `R-S09-4-A1`: Dispatchers will mark false matches. _(fragile: Busy desks will not.)_
- `R-S09-4-A2`: Copies have not already left the system. _(fragile: They may have.)_
- `R-S09-4-A3`: The lookalike family even hears that they were in a still. _(fragile: Often they only hear via a stop.)_

**SPEC**
- `R-S09-4-P1` [cloud/search coordinator]: A false-match disposition deletes or quarantines that still from family and volunteer views.
- `R-S09-4-P2` [cloud/search coordinator]: Propagate the disposition to any device that queued the same crop.
- `R-S09-4-P3` [cloud/search coordinator]: Keep a sealed audit copy only for complaint investigation, with a shorter TTL.

### L-S09-5 / R-S09-5

- **Goal:** `G-S09-1` — Go about daily life without being treated as the missing child or their abductor
- **Loss:** The lookalike child becomes afraid of cameras and of going outside.
- **REQ:** A mistaken ChildFind contact is followed by a clear, child-appropriate explanation that they are not in trouble and were not the missing child.
- **Harm note:** Dignity after a FP is a world requirement on operators, not on the model.

**ASM**
- `R-S09-5-A1`: Officers have a protocol for mistaken missing-child stops involving children. _(fragile: Many do not.)_
- `R-S09-5-A2`: The manufacturer is allowed to require training as a condition of API access. _(fragile: Agencies may refuse.)_
- `R-S09-5-A3`: The caregiver is present and calm. _(fragile: Not always.)_

**SPEC**
- `R-S09-5-P1` [cloud/search coordinator]: When a unit is assigned, the assignment packet includes a mistaken-identity script checklist.
- `R-S09-5-P2` [cloud/search coordinator]: After a false-match disposition, prompt the unit to record whether the script was used.
- `R-S09-5-P3` [cloud/search coordinator]: Do not show the lookalike child's still to additional units after disposition.

## S10: Privacy regulator / data-protection authority

- **Kind:** indirect
- **Who:** Agency enforcing biometric, children's-data, and purpose-limitation rules.
- **Why included:** Unlawful processing can shut the product down regardless of detection accuracy.
- **Power / vulnerability:** high / low

**Values:** lawful biometric processing; children's data protection; purpose limitation and auditability

**Goals:**
- `G-S10-1`: Biometric processing of the public has a legal basis, limits, and a way to challenge it
- `G-S10-2`: Children's data is treated as a special category, not as 'just another face'

### L-S10-1 / R-S10-1

- **Goal:** `G-S10-1` — Biometric processing of the public has a legal basis, limits, and a way to challenge it
- **Loss:** The network performs biometric processing of the general public without a valid legal basis.
- **REQ:** Faces of people who are not the search subject are not biometrically processed except as a transient comparison during an authorized, time-bounded search.
- **Harm note:** If this REQ fails, the feature is illegal even when it finds children.

**ASM**
- `R-S10-1-A1`: Owner consent covers bystanders in public. _(fragile: It generally does not.)_
- `R-S10-1-A2`: A missing-child emergency exception covers continuous embedding of everyone. _(fragile: Exceptions are narrow and time-bounded.)_
- `R-S10-1-A3`: Offline processing on a dashcam is not 'processing' under the statute. _(fragile: It still is, in many regimes.)_

**SPEC**
- `R-S10-1-P1` [dashcam firmware]: Start the matcher only after a valid search-alert with expiry is stored; stop at expiry.
- `R-S10-1-P2` [dashcam firmware]: Do not build a standing gallery; comparison is in-memory against the current search photo.
- `R-S10-1-P3` [cloud/search coordinator]: Record the legal-basis field on the search-id and refuse fan-out if it is empty.

### L-S10-2 / R-S10-2

- **Goal:** `G-S10-2` — Children's data is treated as a special category, not as 'just another face'
- **Loss:** Children's images move across borders to a contractor region without safeguards.
- **REQ:** A child's search photo and any matching still remain in the jurisdiction the case was opened in, unless a recorded transfer mechanism applies.
- **Harm note:** Rekognition-like infrastructure is often multi-region by default.

**ASM**
- `R-S10-2-A1`: The contractor's default region is the case region. _(fragile: Defaults are us-east-1.)_
- `R-S10-2-A2`: On-device matching avoids transfer entirely. _(fragile: Model updates and crash dumps may still leave.)_
- `R-S10-2-A3`: Authorities will not email stills to a personal Gmail. _(fragile: They will.)_

**SPEC**
- `R-S10-2-P1` [person-recognition contractor]: Pin inference and storage to a region field on the search-id.
- `R-S10-2-P2` [cloud/search coordinator]: Block fan-out to a device whose last country code is outside the case region unless an override token is present.
- `R-S10-2-P3` [dashcam firmware]: Prefer on-device comparison so the search photo is the only child image that must be fanned out.

### L-S10-3 / R-S10-3

- **Goal:** `G-S10-1` — Biometric processing of the public has a legal basis, limits, and a way to challenge it
- **Loss:** Accident-evidence recordings are silently joined to a police biometric store.
- **REQ:** Crash-loop recordings made for accident evidence are not searchable as a biometric database.
- **Harm note:** Purpose limitation between the two product jobs.

**ASM**
- `R-S10-3-A1`: Two stores (loop vs ChildFind) are technically and organizationally separate. _(fragile: One disk is cheaper.)_
- `R-S10-3-A2`: A warrant for a specific time window is how police get loop footage, as today. _(fragile: ChildFind will be pitched as skipping that.)_
- `R-S10-3-A3`: Owners understand they can still export a crash clip without enrolling in matching. _(fragile: UX may bundle them.)_

**SPEC**
- `R-S10-3-P1` [dashcam firmware]: ChildFind matcher reads frames in RAM; it does not index the crash-loop archive by face.
- `R-S10-3-P2` [cloud/search coordinator]: No API that takes a photo and scans stored crash loops.
- `R-S10-3-P3` [phone companion app]: Crash export and ChildFind enrollment are separate toggles.

### L-S10-4 / R-S10-4

- **Goal:** `G-S10-1` — Biometric processing of the public has a legal basis, limits, and a way to challenge it
- **Loss:** A subject cannot find out whether they were matched, or get deletion, because the system is opaque.
- **REQ:** A person who was the subject of a ChildFind still can have that still deleted through a defined request path once the search has closed, and can learn whether a still existed.
- **Harm note:** Opaque ML systems fail access/deletion rights.

**ASM**
- `R-S10-4-A1`: We can authenticate that the requester is the person in the still without collecting more biometrics. _(fragile: This is hard; a case-id + liaison path may be the only way.)_
- `R-S10-4-A2`: Offline devices will honor deletion when they next connect. _(fragile: Some never will.)_
- `R-S10-4-A3`: Law-enforcement copies are in scope of the same deletion. _(fragile: Often they are not.)_

**SPEC**
- `R-S10-4-P1` [cloud/search coordinator]: After case-closed, expose a deletion/status request keyed by search-id to the liaison and to a DPA portal.
- `R-S10-4-P2` [dashcam firmware]: On receiving a delete(search-id) message, wipe queued stills and ack.
- `R-S10-4-P3` [cloud/search coordinator]: Track outstanding device acks for deletion and report incomplete deletion as a compliance status.

### L-S10-5 / R-S10-5

- **Goal:** `G-S10-2` — Children's data is treated as a special category, not as 'just another face'
- **Loss:** A precedent is set that any emotional child-safety story justifies biometric scanning of a city.
- **REQ:** Each search remains individually authorized, time-bounded, and geographically bounded rather than becoming a standing scan of all enrolled cameras.
- **Harm note:** The 1-alert/day statistic is a design gift; ignore it and you get always-on scanning.

**ASM**
- `R-S10-5-A1`: Rarity of alerts will keep political appetite limited. _(fragile: One viral case can change that.)_
- `R-S10-5-A2`: Geo-fences will stay tight around last-seen areas. _(fragile: Statewide fences are easier.)_
- `R-S10-5-A3`: Expiry will be short. _(fragile: Nobody will want to be the person who expired a search one hour too soon.)_

**SPEC**
- `R-S10-5-P1` [cloud/search coordinator]: Require geo-fence + expiry on every search-id; default expiry is short and renewal is an explicit action.
- `R-S10-5-P2` [dashcam firmware]: Ignore alerts with empty fences or with expiry in the past.
- `R-S10-5-P3` [cloud/search coordinator]: Alert if a fence exceeds a configurable area or a renewal count exceeds a policy cap.

## S11: Gas-station / edge-kiosk partner

- **Kind:** direct
- **Who:** Business hosting drop-off or inference hardware that management wants to explore.
- **Why included:** The scenario explicitly invites edge computing; it creates a new surveillance place.
- **Power / vulnerability:** medium / medium

**Values:** customer goodwill; limited liability; predictable operating cost

**Goals:**
- `G-S11-1`: Host an edge drop-off without becoming a police checkpoint
- `G-S11-2`: Not pay unbounded bandwidth or eat a lawsuit

### L-S11-1 / R-S11-1

- **Goal:** `G-S11-1` — Host an edge drop-off without becoming a police checkpoint
- **Loss:** Customers treat the station as a surveillance site and stop coming.
- **REQ:** Drivers using the station are not shown, and do not have to pass, a face-matching checkpoint to buy fuel.
- **Harm note:** Edge computing excitement in the scenario is a product risk, not a free lunch.

**ASM**
- `R-S11-1-A1`: The kiosk only offloads encrypted queues from cars that already enrolled, like a USB stick. _(fragile: Someone will point a camera at the forecourt.)_
- `R-S11-1-A2`: Signage can make this feel like Wi-Fi, not CCTV. _(fragile: A camera on a pole will not.)_
- `R-S11-1-A3`: Staff will not watch stills on a back-office monitor. _(fragile: They will if we give them a UI.)_

**SPEC**
- `R-S11-1-P1` [edge kiosk]: Accept only encrypted sighting-report queues from authenticated dashcams; do not run a site-wide camera into the matcher.
- `R-S11-1-P2` [edge kiosk]: No staff UI that displays faces.
- `R-S11-1-P3` [cloud/search coordinator]: Do not list partner sites on a public 'coverage map'.

### L-S11-2 / R-S11-2

- **Goal:** `G-S11-2` — Not pay unbounded bandwidth or eat a lawsuit
- **Loss:** A child was at the pump and not reported; the station is sued for hosting the system.
- **REQ:** Hosting an offload kiosk is not treated as a promise that everyone on the forecourt will be matched.
- **Harm note:** Coverage fiction again, now at a place.

**ASM**
- `R-S11-2-A1`: The kiosk is not a camera. _(fragile: Press photos will show a camera-looking box.)_
- `R-S11-2-A2`: Contracts shift duty to the manufacturer. _(fragile: Plaintiffs still name the deep pocket they can find.)_
- `R-S11-2-A3`: Only enrolled cars offload, so most forecourt visitors are irrelevant. _(fragile: That is hard to explain after a miss.)_

**SPEC**
- `R-S11-2-P1` [edge kiosk]: Broadcast a machine-readable 'offload only, no site matching' capability flag.
- `R-S11-2-P2` [cloud/search coordinator]: Do not count kiosk locations as camera coverage in dispatch density maps.
- `R-S11-2-P3` [phone companion app]: Partner-facing status page states offload-only in the same words used internally.

### L-S11-3 / R-S11-3

- **Goal:** `G-S11-1` — Host an edge drop-off without becoming a police checkpoint
- **Loss:** Someone uses the kiosk network to pull faces of all customers.
- **REQ:** The partner network cannot be queried for people who did not just offload an enrolled dashcam queue.
- **Harm note:** A new shared phenomenon (the kiosk) is a new attack surface.

**ASM**
- `R-S11-3-A1`: The kiosk has no camera and no disk of faces. _(fragile: Feature creep: 'why not match the forecourt camera we already have'.)_
- `R-S11-3-A2`: Physical access to the box does not yield keys. _(fragile: Gas-station closets are not data centers.)_
- `R-S11-3-A3`: The partner's IT staff have no admin API for stills. _(fragile: They will want one for 'support'.)_

**SPEC**
- `R-S11-3-P1` [edge kiosk]: Forward-only: decrypt-at-coordinator; the kiosk stores opaque blobs with TTL.
- `R-S11-3-P2` [edge kiosk]: No query API; physical debug requires a manufacturer key and wipes on close.
- `R-S11-3-P3` [cloud/search coordinator]: Issue per-session keys so a stolen box cannot decrypt old blobs.

### L-S11-4 / R-S11-4

- **Goal:** `G-S11-2` — Not pay unbounded bandwidth or eat a lawsuit
- **Loss:** The kiosk is stolen or smashed and stored blobs are taken.
- **REQ:** Theft of a kiosk does not disclose identifiable stills or search photos.
- **Harm note:** Physical security of edge is not like cloud security.

**ASM**
- `R-S11-4-A1`: TTL is short enough that a stolen disk is empty. _(fragile: A busy holiday weekend queue may be large.)_
- `R-S11-4-A2`: Encryption keys are not on the same disk. _(fragile: They often are, for convenience.)_
- `R-S11-4-A3`: Thieves want cash, not blobs. _(fragile: Sometimes they want both.)_

**SPEC**
- `R-S11-4-P1` [edge kiosk]: Encrypt blobs with keys the kiosk cannot use to decrypt; coordinator holds the unwrap.
- `R-S11-4-P2` [edge kiosk]: Wipe blobs older than TTL even if not yet forwarded.
- `R-S11-4-P3` [cloud/search coordinator]: Revoke a kiosk's forwarding identity when tamper or theft is reported.

### L-S11-5 / R-S11-5

- **Goal:** `G-S11-2` — Not pay unbounded bandwidth or eat a lawsuit
- **Loss:** Bandwidth bills from video offload exceed the partnership's value.
- **REQ:** The partner is not asked to carry raw video, only small encrypted reports within a contracted byte budget.
- **Harm note:** If the design needs full video at the edge, the partnership dies or becomes extractive.

**ASM**
- `R-S11-5-A1`: Sighting-reports are kilobytes, not gigabytes. _(fragile: If we offload unmatched clips 'just in case', they are not.)_
- `R-S11-5-A2`: Nightly sync is enough. _(fragile: Faster-is-more-useful fights this.)_
- `R-S11-5-A3`: The manufacturer pays overage. _(fragile: Unless the contract is silent.)_

**SPEC**
- `R-S11-5-P1` [edge kiosk]: Refuse objects over a size cap; accept only sighting-report MIME types.
- `R-S11-5-P2` [dashcam firmware]: Build the kiosk offload from the same small sighting-report as the phone path.
- `R-S11-5-P3` [cloud/search coordinator]: Meter per-kiosk bytes and disable a site that exceeds contract rather than silently billing the partner.

## S12: Rideshare / fleet driver

- **Kind:** direct
- **Who:** Driver whose vehicle is a workplace and who may be required to keep the dashcam on.
- **Why included:** Passengers did not buy the dashcam; employment pressure changes opt-in assumptions.
- **Power / vulnerability:** low / high

**Values:** income; passenger privacy; not being punished for opting out

**Goals:**
- `G-S12-1`: Keep driving for a living without turning passengers into search subjects
- `G-S12-2`: Not be deactivated for refusing ChildFind

### L-S12-1 / R-S12-1

- **Goal:** `G-S12-1` — Keep driving for a living without turning passengers into search subjects
- **Loss:** A passenger is matched or still-captured without knowing a search was running in the car they hired.
- **REQ:** A rideshare passenger is not biometrically compared to a missing-child photo unless they have been told a search is active in that vehicle and can decline the ride.
- **Harm note:** Employment dashcams break the consumer opt-in story.

**ASM**
- `R-S12-1-A1`: Only the outward camera is used, so passengers are not in frame. _(fragile: Pickup happens at the curb, in frame; cabin cams exist.)_
- `R-S12-1-A2`: Platform terms cover this. _(fragile: Passengers do not read them; they may be unlawful anyway.)_
- `R-S12-1-A3`: A sticker on the window is notice. _(fragile: It is not a decline path.)_

**SPEC**
- `R-S12-1-P1` [phone companion app]: In fleet mode, show a passenger-notice card before matching is allowed to run, and log the notice event.
- `R-S12-1-P2` [dashcam firmware]: Fleet mode binds matching to the outward camera and disables cabin input, same as R-S06-4.
- `R-S12-1-P3` [cloud/search coordinator]: Fleet organizations cannot hide the search-active state from the rider-facing notice.

### L-S12-2 / R-S12-2

- **Goal:** `G-S12-2` — Not be deactivated for refusing ChildFind
- **Loss:** The driver is deactivated or loses a bonus for turning ChildFind off.
- **REQ:** A driver who disables ChildFind does not automatically lose the ability to work.
- **Harm note:** Otherwise 'opt-in' is fiction.

**ASM**
- `R-S12-2-A1`: The fleet will treat ChildFind as optional safety theater. _(fragile: They will treat it as a KPI.)_
- `R-S12-2-A2`: The manufacturer does not send enrollment status to the fleet. _(fragile: The fleet will demand it.)_
- `R-S12-2-A3`: Local law forbids making employment conditional on biometric enrollment. _(fragile: Varies by city.)_

**SPEC**
- `R-S12-2-P1` [cloud/search coordinator]: Do not provide an API whose only purpose is 'is this driver enrolled' to a fleet without a passenger-privacy role.
- `R-S12-2-P2` [phone companion app]: Driver opt-out does not emit a punishment-ready flag; it emits search-degraded like any other device.
- `R-S12-2-P3` [cloud/search coordinator]: Fleet dashboards show aggregate coverage, not named opt-out lists.

### L-S12-3 / R-S12-3

- **Goal:** `G-S12-1` — Keep driving for a living without turning passengers into search subjects
- **Loss:** A passenger gives a one-star review because a match prompt or LED made them feel watched.
- **REQ:** Passengers are not shown missing-child photos or match stills during a trip.
- **Harm note:** UX meant for volunteer drivers is wrong in a taxi.

**ASM**
- `R-S12-3-A1`: We already suppressed driver prompts while moving. _(fragile: A passenger phone might still be used as the paired device.)_
- `R-S12-3-A2`: LEDs can be dimmed. _(fragile: Platforms may require a recording LED.)_
- `R-S12-3-A3`: Explanation at pickup is enough to prevent the feeling of being watched. _(fragile: It can also increase it.)_

**SPEC**
- `R-S12-3-P1` [phone companion app]: Fleet mode disables all match previews on any paired phone in the vehicle.
- `R-S12-3-P2` [dashcam firmware]: No in-cabin display of crops.
- `R-S12-3-P3` [cloud/search coordinator]: Reviewer stills never route to a rider-facing app.

### L-S12-4 / R-S12-4

- **Goal:** `G-S12-1` — Keep driving for a living without turning passengers into search subjects
- **Loss:** Footage of a fare dispute is pulled because it happened to be in a ChildFind queue.
- **REQ:** A passenger–driver dispute is not investigated through ChildFind stills collected for a missing-child search.
- **Harm note:** Secondary use inside the same car.

**ASM**
- `R-S12-4-A1`: ChildFind stills are useless for dispute resolution because they are tight face crops of people on the street. _(fragile: A wide FOV at pickup will include the passenger.)_
- `R-S12-4-A2`: Platforms already have a separate cabin-cam process. _(fragile: They will still ask for whatever exists.)_
- `R-S12-4-A3`: Purpose tokens hold under a platform lawyer's request. _(fragile: Pressure will be high.)_

**SPEC**
- `R-S12-4-P1` [cloud/search coordinator]: Refuse platform-support accessors on the ChildFind store; send them to the crash-loop/warrant path.
- `R-S12-4-P2` [dashcam firmware]: Tag ChildFind blobs with purpose=missing-child so they cannot be pulled by the dispute export job.
- `R-S12-4-P3` [phone companion app]: No 'download today's stills' for the driver.

### L-S12-5 / R-S12-5

- **Goal:** `G-S12-2` — Not be deactivated for refusing ChildFind
- **Loss:** The driver's personal phone plan is billed for fleet matching uploads.
- **REQ:** Cellular bytes used for ChildFind on a fleet vehicle are not charged to the driver's personal plan without their agreement.
- **Harm note:** Same data-cost REQ as S01, but the payer is different.

**ASM**
- `R-S12-5-A1`: The paired phone is a company device. _(fragile: Often it is the driver's phone.)_
- `R-S12-5-A2`: OEM telematics will carry the bytes. _(fragile: Aftermarket cameras will not.)_
- `R-S12-5-A3`: Drivers notice the budget UI. _(fragile: They are busy.)_

**SPEC**
- `R-S12-5-P1` [phone companion app]: In fleet mode, require a fleet-paid network identity or a pre-set budget bound to the organization, not the driver's personal default.
- `R-S12-5-P2` [dashcam firmware]: Prefer kiosk/Wi-Fi offload on fleet vehicles.
- `R-S12-5-P3` [cloud/search coordinator]: Billable-byte reports go to the fleet org, not to the driver email.

## Cross-cutting observation (not a substitute for key_results.md)

Many losses collapse to the same two fragile assumptions: (1) the dashcam has a timely network path, and (2) a face match on an adult-tuned model is a reliable proxy for 'this child was here'. Those are called out in `key_results.md` rather than repeated as fifty 'improve the model' items.

