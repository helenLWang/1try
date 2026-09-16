# Human review log (checkpoint notes)

This is the human-in-the-loop step the assignment asks for. The JSON in this directory is **approved** for the submitted report.

## Stakeholders

- Started from a 16-name brainstorm; kept 12. Dropped "investors" and "competitors" (real stakeholders, weak ChildFind-specific losses).
- Added S11 (edge kiosk) because the scenario name-drops gas stations and it is exactly the kind of stakeholder a model trained on "dashcam app" omits.
- Added S12 (fleet/rideshare) because consumer opt-in is false when the car is a workplace.
- Marked S02 and S09 as high vulnerability / low power on purpose: they do not buy the product.

## Losses / REQs

- Deleted rows whose REQ mentioned accuracy %, "the neural network", or "Rekognition".
- Rewrote remaining REQs until they only mentioned world phenomena (stops, notices received, identities assigned, bills, crashes).
- Merged three "camera misses the child" variants into R-S02-1 so FTA has one top event.
- Kept L-S08-4 (do not harvest bystander children for training) as a trap for the obvious ML fix.

## ASM / SPEC

- SPEC verbs are accept/emit/store/queue/label on named messages (`search-alert`, `sighting-report`, `match_score`).
- ASM that said "the model is robust" was rewritten as a world mapping (photo resembles the child; officers treat a pin as a lead).
- Flagged fragile ASMs in `why_fragile` so prioritize/curation can see assumption risk, not only severity.

## Four key results

Chosen in `key_results.md`. Not the first four rows, not the LLM ranker's top four. `priorities.json` is a *candidate* ranking I wrote to mimic what `python -m hazard_tool prioritize` should surface (connectivity, lookalikes, purpose limitation, child domain gap). I still picked R-S01-6 (location oracle) over the child-domain-gap row because the legal vacuum is in the prompt and is more surprising than "faces of children are hard."
