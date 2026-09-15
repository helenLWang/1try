# Office-hours notes (not a graded deliverable)

Short script so I can explain the solution without re-deriving it live. The 20-point conversation is the point of this file.

## How I curated the four

I generated a large catalog (12 stakeholders, 64 losses) with the same schema the LLM tool uses, then **threw most of it away**. Ranking I actually used:

1. Would this change the architecture this quarter, or is it "get a better model"?
2. Does the *scenario text* already warn us (no Internet, unsettled law, data charges, edge kiosks) and would a designer still miss it?
3. Can I say the REQ in the world, the SPEC on messages/sensors, and the ASM as the mapping — and does ASM ∧ SPEC still entail REQ?

That is why the four are: (1) timely sighting that dies on Bluetooth, (2) lookalike police stop from optimizing recall, (3) bystander embeddings as identity, (4) fake search-id as a location oracle. I explicitly did **not** pick "hackers steal weights" or "collect more child faces," even though both appear in the catalog.

If asked "did you just accept the model's top-4?": no. `prioritize` is a candidate list. `key_results.md` states the rule. Several LLM-shaped REQs that said "the model shall have 99% recall" were rewritten or deleted because that sentence is a SPEC, not a REQ.

## Reflection prompts

**Was the automation useful?** Yes for *coverage* (I would not have listed fleet drivers, kiosk partners, and sibling faces in one sitting). No for *judgment*. Unchecked, it emits fifty ways of saying the model is wrong. The useful automation is the checkpoint: JSON you can delete from.

**If the tool had dashcam source code?** I would want it to bind SPEC ids to actual messages (search-alert schema, queue implementation, whether infotainment can show a crop). Hazard analysis on prose will always invent interfaces the code does not have, and miss the ones it does (cabin cam, crash-loop on the same disk). Code would not replace STPA; it would make SPEC checkable.

**What surprised me?** (1) "We only match one photo" still builds a biometric pipeline over everyone. (2) False positives steal the last rural patrol from the true child — recall and precision are not a private ML tradeoff. (3) Parent live-maps are a stalking feature. (4) Gas-station edge, as management pitched it, is a new place, not a faster USB stick, unless we freeze the kiosk as forward-only blobs.

**What would it take to adopt this on a real project?** A one-page catalog like `key_results.md` plus two fault trees, done before the first OEM slide. Not a 64-row markdown file. The 64-row file is how you *find* the one-pager. Also: someone with authority to reject "just lower the threshold" and "give parents a map."

## Tooling, briefly

- `hazard_tool/` — LLM client (OpenAI-compatible / Anthropic / Gemini), prompts that enforce Jackson wording, CLI with approve gates.
- `python -m hazard_tool seed` rebuilds the reviewed catalog without a key so graders can render the report.
- Fault trees: `scripts/make_fault_trees.py` → `figures/*.svg`. Mitigations M1/M2 are radios+kiosk and human top-k, not more data.
