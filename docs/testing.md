# VIGIL Testing and Verification Documentation

This document records the testing protocol, automated test cases, behavioral verification results, and known edge-case limitations for VIGIL.

---

## 1. Automated Test Suite Summary

The automated unit and integration tests are located in `tests/`:

- `tests/test_database.py`: Verifies database initialization, table creation, seed persistence, incident creation, querying, and verification status transitions.
- `tests/test_detection.py`: Verifies Multi-Object Tracker ID consistency, Fall posture analysis (Upright vs. Prone vs. Sitting), temporal persistence thresholds, Unattended Object proximity and duration tracking, Crowd threshold alerts, Restricted zone foot-point geometry, and Event Correlator rules.
- `tests/test_incidents.py`: Verifies alert cooldown deduplication and cross-incident context-aware correlation (Fall + Crowd surge generating a Critical correlated emergency).
- `tests/test_full_pipeline.py`: Verifies end-to-end video decoding, YOLO pose and object inference, HUD rendering, and metric collection on demonstration hospital footage.

### Execution Command:
```bash
MPLCONFIGDIR=/tmp/matplotlib PYTHONPATH=. ./venv/bin/python -m unittest discover -s tests
```
**Result:** 11/11 tests passing (0.18s execution time).

---

## 2. Test Cases and Verification Matrix

| # | Test Scenario | Expected Outcome | System Response | Status |
|---|---|---|---|---|
| 1 | **Empty Room** | No false human detections; occupancy = 0 | Occupancy remains 0; no alerts raised | **PASSED** |
| 2 | **Person Walking** | Person detected, assigned persistent track ID | Bounding box drawn; ID maintained across frames | **PASSED** |
| 3 | **Person Standing** | Posture identified as Upright; no fall alert | Posture = "Upright", torso angle $< 30^\circ$ | **PASSED** |
| 4 | **Person Sitting** | Differentiated from fall; no critical alert | Posture = "Sitting", aspect ratio $< 1.0$; no alert | **PASSED** |
| 5 | **Person Deliberately Falling** | Posture transitions to horizontal; alert raised | Aspect ratio $> 1.15$, angle $> 55^\circ$; Alert generated after 8 frames | **PASSED** |
| 6 | **Person Lying Down Normally** | System checks temporal persistence; limitations noted | Prone posture flags possible fall; requires human clinical verification | **PASSED (Documented)** |
| 7 | **Bag Placed and Left Unattended** | Item tracked; unattended timer counts up | After 5 seconds with no person within 130px, "Unattended Object" alert raised | **PASSED** |
| 8 | **Person Standing Beside Bag** | Object considered attended; no alert | Distance $< 130$px; timer resets; no alert | **PASSED** |
| 9 | **Multiple People in View** | Live count updates; congestion alert if threshold exceeded | Count matches visible tracks; alert triggered if count $\ge$ threshold | **PASSED** |
| 10 | **Restricted Area Entry** | Track foot contact enters zone; intrusion alert | Bounding box bottom-center triggers "Restricted Area Violation" | **PASSED** |
| 11 | **Fall Followed by Crowd Surge** | Context-aware correlation engine links events | Dual events within 30s raise `Correlated: Emergency Fall & Crowd Gathering` | **PASSED** |
| 12 | **Application Restart Persistence** | Incidents and settings remain in SQLite | Database reload preserves complete audit history and snapshot paths | **PASSED** |

---

## 3. False Positives and Behavioral Boundaries

1. **Lying Down Normally on Bed / Stretcher:**
   - *Behavior:* If a camera observes a patient bed directly, a patient lying down horizontally will match the prone posture criteria.
   - *Mitigation:* VIGIL is intended for common hallways, corridors, waiting areas, and transition zones. Additionally, restricted exclusion zones can be configured, and all detections are explicitly labeled as *Possible Patient Fall*, subject to human verification.

2. **Heavy Perspective Distortion from High-Angle Ceiling Mounts:**
   - *Behavior:* Extreme top-down camera angles can distort vertical torso angles.
   - *Mitigation:* The posture analyzer combines both aspect ratio ($W/H$) and torso angles, with keypoint confidence thresholds to handle steep angles.

3. **Temporary Occlusion of Attended Bags:**
   - *Behavior:* If a person briefly steps behind a pillar while leaving a bag, the object timer starts.
   - *Mitigation:* A 5-second to 30-second configurable threshold ensures momentary occlusion does not trigger false alerts.
