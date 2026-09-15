# Four curated losses / requirements

The full catalog in `analysis_results.md` is 64 losses. Most of it is a firehose a developer would ignore. These four are the ones I would actually take to a design review. I did **not** take the LLM ranker's top four. `workspace/priorities.json` is only a candidate list; the selection and the "why it matters" paragraphs below are mine.

**Selection rule I used.** Keep a result if (a) it changes architecture, not just "get a better model", (b) it is easy for this scenario's designers to miss because the scenario *invites* the wrong assumption, and (c) REQ / ASM / SPEC still compose as ASM ∧ SPEC ⊨ REQ. I dropped dozens of items that were restatements of "the model is inaccurate."

---

## 1. Missed timely sighting — missing child (S02), goal G-S02-1

**Loss.** The child remains missing even though they walked through a participating camera's view.

**REQ R-S02-1 (world only).** If a missing child is physically visible in the field of view of a participating dashcam during an authorized search, the coordinating law-enforcement unit learns of that co-location while the child is still in the same local area.

**Why this is the one I would staff first.** It is the mission requirement, and it is *not* a model-accuracy requirement. The scenario already tells us the camera has no Internet. A perfect match that sits in flash until the owner opens the garage is a miss. I also picked it for FTA because it honestly depends on the ML component (wrong prediction must appear in the tree) *and* on radios, photos, and operators.

**ASM (world / shared).**

1. The dashcam is powered and the lens is unobstructed whenever the vehicle is on a public road.
2. The child's face or other distinctive appearance is not fully covered for the entire time they are in view.
3. Within a short interval after the child is in view, the dashcam or paired phone obtains a network path that can deliver a small report.
4. The search packet contains a photograph that still resembles the child's current appearance.
5. Operators read inbound sighting notices rather than discarding them as noise.

**SPEC (interface only).**

1. Phone app, on a search-alert message (photo, search-id, fence, expiry), stores it until expiry and forwards it to the dashcam.
2. Person-recognition component outputs a `match_score` for each in-scope person crop against the search photo.
3. Firmware, when `match_score` exceeds threshold, emits a sighting-report with search-id, timestamp, GPS sample, and cropped still.
4. If no radio is up, firmware queues that report until the next Bluetooth/Wi-Fi/USB session or expiry.
5. Coordinator, on ingest, presents the report in the coordinating-unit inbox with map pin and still (no silent second model drop).

Fault tree and two *system-level* mitigations: `fault_tree.md`.

---

## 2. Police stop of a lookalike — innocent child/caregiver (S09), goal G-S09-1

**Loss.** Police stop a lookalike child in public based on a ChildFind pin.

**REQ R-S09-1 (world only).** A child who is not the missing child is not stopped by police solely because a dashcam produced a possible-match notice.

**Why this was surprising to me, and why I kept it.** The instinct in this project is to optimize recall for S02. Every "just lower the threshold" or "auto-dispatch the nearest unit" move makes *this* REQ worse. False positives are not a victimless precision metric: they are a child being stopped, and they also steal the only patrol car from the true vicinity (R-S02-4). The LLM catalog produced many "model inaccurate" losses; it did **not** by itself emphasize that the *officer* is the actuator and that a `FOUND` bit is a specification smell.

**ASM.**

1. Officers treat a possible-match notice as a lead that needs corroboration, not as an identification. *(fragile on missing-child calls.)*
2. Lookalikes are rare enough that a high threshold prevents stops. *(school uniforms, siblings.)*
3. The caregiver can immediately show the child's identity. *(often false.)*
4. The notice is not blasted to every patrol phone as `FOUND`.

**SPEC.**

1. Coordinator labels every notice `unconfirmed possible match` and includes `match_score`; software cannot enter a `FOUND` state by itself.
2. Coordinator does not fan a pin to all units; it goes to the coordinating desk for assignment.
3. Model outputs a score and a recommended-threshold band, not a binary identity claim.
4. Coordinator attaches the search photo next to the still so a human compares before a stop is authorized.

---

## 3. Bystander becomes a persistent identity — other road users (S08), goal G-S08-1

**Loss.** A bystander's face is embedded and kept so they can be re-identified after the search ends.

**REQ R-S08-1 (world only).** A person who is not the subject of an authorized search is not assigned a persistent identity from ChildFind processing.

**Why this is easy to miss.** Designers say "we only compare to one search photo, so we are not identifying bystanders." Comparison still *detects and embeds every face*. An embedding without a name is still a linkable identifier. The 1-alert/day national rate is an argument for *ephemeral* matching, not for building a gallery "so the next search is faster." Edge kiosks (S11) make this worse if they grow a site camera. This REQ is what stops ChildFind from being a rolling Rekognition network — which is also the OEM's brand risk (O3 / S06).

**ASM.**

1. Comparing to one search photo means bystanders are not identified. *(false: detection+embedding is identification infrastructure.)*
2. Nameless embeddings are not identifications. *(they are linkable IDs.)*
3. People in public have no remaining biometric expectation. *(regulators, especially for child bystanders, disagree.)*

**SPEC.**

1. Firmware does not store embeddings except the current search photo and in-memory crops of the current matching window.
2. Model outputs `match_score` versus the search photo only; no gallery id for non-matches.
3. Firmware zeros in-memory crops when the search-id expires or the vehicle powers down.

---

## 4. Fake "missing child" search as a location oracle — dashcam owner (S01), goal G-S01-1

**Loss.** Someone uses a fake missing-child enrollment to reconstruct the owner's routine from sighting metadata.

**REQ R-S01-6 (world only).** A person who is not the subject of a bona fide, authority-backed search cannot obtain a trail of where the owner's car has been.

**Why I think this is the most scenario-specific surprise.** The assignment literally says legal details are not worked out, and that searches are coordinated with authorities. The product temptation — "give parents a live map" — turns every enrolled car into a location sensor for whoever can mint a search-id. That is not an ML failure. It is an authorization/interface failure. It also collides with domestic-violence cases (R-S02-6) and purpose creep into shoplifting/immigration (R-S04-4). I would rather ship slower parent status ("search active / recovered") than GPS-bearing stills on a parent login.

**ASM.**

1. Only authorities/non-profit can create a search-id, and they vet the requester. *(legal details unsettled.)*
2. Sighting-reports are not visible to the original requester, only to the coordinating unit. *(parents will ask for the live map.)*
3. A search photo of an adult cannot be submitted under a child-search type.

**SPEC.**

1. Coordinator accepts new search-ids only from authenticated authority/non-profit accounts, not from end-user accounts.
2. Coordinator does not return sighting GPS to the requester account; only to the coordinating-unit inbox.
3. Coordinator rejects packets marked 18+ or that fail a child-age gate.

---

## What I discarded on purpose

- Generic "hackers steal the model" (S07-1): real, but it does not change whether a child is found or a lookalike is stopped this quarter.
- "Collect more child faces from the street to fix M1": that *is* loss L-S08-4. The ML fix is the privacy incident.
- LLM-suggested REQs that mentioned "the model shall have 99% recall": those are SPECs, and I rewrote or deleted them during review of `workspace/hazards.json`.
