"""Hard-coded Dashcam child-safety scenario (assignment I3)."""

SYSTEM_NAME = "ChildFind Dashcam Search"

SYSTEM_DESCRIPTION = """
Dashcams are installed in many vehicles. We are a commercial dashcam manufacturer
selling to end consumers and to automotive OEMs. Together with a non-profit
organization we are building ChildFind: instead of public Amber-style broadcasts,
participating dashcams search their video recordings for children reported missing.

The person-recognition model (face/person matching in distorted and low-light
images) is contracted out. The contractor builds on infrastructure similar to
Amazon Rekognition but can customize components, including offline/on-device
deployment. They provide infrastructure for us to fine-tune and serve models.

Constraints and context:
- Dashcams have no direct Internet. They communicate over USB, Bluetooth, or
  Wi-Fi with phones, the car, or Wi-Fi hotspots.
- Dashcams may run on battery but are usually powered by the car while it runs.
  On-device compute varies by model.
- Searches are coordinated with authorities and the non-profit. Legal details
  are not settled. Searches are infrequent (Amber alerts: about 1/day nationwide).
- Faster sighting reports are more useful to authorities.
- Users worry about privacy and cellular data charges.
- Management is interested in edge computing, including partner hardware at
  gas stations or drive-throughs.

World-vs-machine vocabulary (Jackson):
- REQ: desired phenomena in the environment only (the world). Never mention
  models, scores, packets, or software internals.
- ASM: environmental phenomena, or how those map onto shared interface
  phenomena the software can observe or produce (sensors, human operators,
  radios, cameras, officers reading a report).
- SPEC: only shared interface phenomena (messages in/out, sensor readings
  presented to software, actuator/report outputs). Do not mention "the child"
  or "the police decide" unless those are represented as interface data.
""".strip()

WORLD_MACHINE_RULES = """
When writing REQ / ASM / SPEC, obey Jackson's world-vs-machine split:
- REQ mentions only world phenomena (a child being visible on a road, an
  officer stopping a caregiver, a parent being notified, a bystander remaining
  unidentified). Bad REQ: "the model shall have 99% recall".
- ASM may mention world phenomena and the mapping to shared phenomena
  (camera points at the road; GPS samples track the vehicle; officers treat a
  'possible match' notice as a lead not a positive identification; a paired
  phone provides a cellular path within N minutes).
- SPEC mentions only interface data and actions of software (accept a
  search-alert message; emit a sighting-report with GPS/time/crop; queue
  reports when the radio is down; output a match_score in [0,1]).
- Check: ASM ∧ SPEC ⊨ REQ. If the software did exactly SPEC and the world
  behaved as ASM, the REQ would hold.
""".strip()
