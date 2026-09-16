# ChildFind: goals and measurement

Layered goals for ChildFind and one 3-step measure per layer, written so someone else could re-run the measurement.

## Organizational goals (dashcam manufacturer)

- **O1. Distinctive revenue.** Grow consumer and OEM sales of ChildFind-capable units against competitors who only record accidents.
- **O2. Unit economics.** Keep cloud, radio, and contractor-inference cost small relative to hardware margin, given that searches are rare (~1 Amber-like event per day nationwide).
- **O3. Brand survival.** Avoid becoming "the face-recognition car company"; a privacy or wrongful-stop scandal should not destroy the core dashcam business.
- **O4. Partnership option value.** Keep the non-profit and OEM channels, including a possible edge offload path, without buying it with liability.

## System goals (ChildFind feature)

- **P1. Useful sightings.** During an authorized search, if a missing child is physically in view of a participating camera, coordinating authorities get a located notice while the child is still in that area.
- **P2. Bounded purpose.** Matching runs only for an authorized, time-bounded, geo-bounded missing-child search — not as a standing biometric index of the street.
- **P3. Offline-tolerant delivery.** Sightings survive the product's lack of native Internet (USB / Bluetooth / Wi-Fi to a phone, car, or hotspot).
- **P4. Cheap in the common case.** Between searches, ChildFind must not destroy crash-loop recording, battery, or the owner's data budget.
- **P5. Non-identifying by default.** People who are not the search subject are not named or lastingly identified.

## User / stakeholder goals (four stakeholders)

- **U-driver.** Keep a private accident record; do not become a public search node; do not pay surprise cellular bills; do not get crash-causing prompts.
- **U-family.** Recover the child quickly; receive truthful status (including "cameras are not actually covering this area"); do not expose siblings' photos or the home address.
- **U-dispatch.** Get a small number of located, unconfirmed leads — not a firehose and not a silent miss — without dropping ordinary canvassing.
- **U-bystander (indirect).** Move through public space without being biometrically filed by a consumer camera network.

## Model goals (person-recognition component)

- **M1. Child-in-dashcam recall.** When a search photo of *this* child is compared to a usable dashcam crop of *this* child, the score is high enough that the crop is not dropped.
- **M2. Precision at the operating point.** Scores that trigger a sighting-report are rare for other children and adults, including siblings and school-uniform lookalikes.
- **M3. Calibrated, not binary.** Downstream software needs a score (or a low-confidence band), not a `FOUND` bit.
- **M4. Conditions of the road.** Motion blur, night headlights, rain, and off-axis faces are the deployment distribution — not studio mugshots.
- **M5. Operable on heterogeneous hardware.** A useful (possibly weaker) on-device or on-phone path exists when cloud inference is unreachable.

## How the goals relate — and where they do not

**Support.** M1 and P3 together serve P1 and U-family: a correct on-device score is worthless if the report sits in a car whose phone is in a house. O1 is supposed to follow from P1 if families, cities, and OEMs believe sightings are real. P4 and U-driver protect O3: if the feature bricks crash recording or surprises people on their phone bill, they disable it and P1's coverage map becomes fiction.

**Conflict.** M1 (recall) fights M2 and U-bystander / lookalikes: lowering the threshold produces officer stops of the wrong child (see `key_results.md`). P1's "faster is more useful" fights P2 and O3 if we pre-index every face or light up driver UIs. O4's edge kiosks help P3 only if they remain *offload* points; if they grow site cameras, U-bystander and S11's customers are harmed. U-dispatch's need for context images fights U-bystander's need for tight crops. **Better model accuracy does not automatically raise children recovered** if ASM-connectivity or ASM-operator-attention fails; that is why measurement at the system layer cannot be replaced by M1.

## Measures (measure → data → operationalization)

### Organizational goal O1 — ChildFind-attributed unit sales

- **Measure.** Number of *ChildFind-capable units sold* in quarter *Q*, minus the number of units of the matched pre-ChildFind SKU sold in *Q−4*, minus the percentage change in the manufacturer's *non-ChildFind* dashcam units over the same year-over-year window (so we do not credit a rising dashcam market to the feature).
- **Data.** ERP/sales records: `sku`, `childfind_capable` flag, `channel` (DTC vs OEM), `invoice_date`, `units`. Same extract for all dashcam SKUs.
- **Operationalization.** For quarter Q, let \(C_Q\) be units with `childfind_capable=true`, \(C_{Q-4}\) the same SKU family a year earlier, \(B_Q,B_{Q-4}\) non-ChildFind dashcam units. Report \(C_Q - C_{Q-4}\cdot(B_Q/B_{Q-4})\) and the two raw series. Exclude internal/demo units. Recompute from the same SQL on the snapshot dated the first Monday after quarter close.

### System goal P1 — timely notice given a true in-view event

- **Measure.** Among *scripted true-positive exercises* in a quarter, the median time from "child first enters the participating camera's field of view" to "coordinating-unit inbox shows a sighting-notice with GPS," and the fraction of exercises where that time is ≤ 15 minutes.
- **Data.** For each exercise: a time-synchronized log of (a) a GPS ground-truth track of a volunteer child-sized mannequin or consented youth actor, (b) dashcam power/matching state, (c) radio-session timestamps, (d) inbox ingest timestamps. Do **not** use live missing-child cases as the primary measure (base rate is too low and ethically wrong to instrument). Run ≥ 20 exercises per quarter, stratified by: phone-in-car vs phone-elsewhere, day vs night, low-end vs high-end SKU.
- **Operationalization.** Mark \(t_0\) as the first video frame where a human annotator agrees the actor is unoccluded and in view. Mark \(t_1\) as inbox ingest of a notice whose GPS is within 200 m of the actor's GNSS at \(t_0\). Drop exercises where the camera was powered off (those belong to coverage, not this measure). Report median(\(t_1-t_0\)), p90, and hit-rate at 15 minutes, with 95% Wilson intervals on the hit-rate.

### User goal U-driver — ChildFind cellular bytes vs agreed budget

- **Measure.** Per enrolled device-month, *ChildFind-attributed cellular uplink bytes* as a fraction of the owner's stated budget, and the fraction of device-months that exceeded the budget without a confirmed owner override.
- **Data.** Companion-app counters: bytes tagged `purpose=childfind` on the cellular interface; the owner's integer budget (bytes/month) at month start; override events. Cross-check a 5% random sample against the phone OS's per-app cellular statistic (Android `NetworkStatsManager` / iOS equivalent) for the companion app.
- **Operationalization.** For each device-month with enrollment ≥ 14 days, compute `min(1, childfind_cellular_bytes / budget)` and an `exceeded_without_override` boolean. Report mean fraction, p95 bytes, and exceedance rate. Device-months with budget=0 (matching explicitly off) are excluded from the fraction and counted separately as opt-outs.

### Model goal M1 — recall at a high-precision operating point on child dashcam crops

- **Measure.** Recall of the person-recognition *score* for the labeled identity, at the smallest threshold \(\tau\) such that precision on a held-out **impstor** set is ≥ 0.99. Evaluation is on dashcam-like images of children, not adult mugshots.
- **Data.** A sealed evaluation set, rebuilt quarterly: (positives) time-aligned crops of consented children (or legally licensed child-actor footage) from dashcam rigs under day/night/rain; (impostors) crops of other children and adults from the same rigs, plus sibling pairs when available. No live search photos. Age-band and lighting tags on every crop. The set is not used for training.
- **Operationalization.** For each positive identity with ≥ 5 probes, count a hit if \(\max_j s(i,j) \ge \tau\). Sweep \(\tau\) on a disjoint calibration split until impostor precision ≥ 0.99; freeze \(\tau\); report recall on the remaining positives overall and sliced by age-band {0–4, 5–11, 12–17} and lighting {day, night}. Publish \(\tau\), n, and slice counts. A drop > 5 points in any slice versus the previous quarter is a go/no-go input for firmware release — not a reason to silently lower \(\tau\) in production (that would steal from M2 and U-lookalike).
