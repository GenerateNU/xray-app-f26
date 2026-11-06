# luXRay Operator App — Architecture & Notes

The operator app for the X-ray survey machine. A gantry moves a radiation sensor around the outside of the Neptune CT scanner and measures leakage. The app lets an operator pick which sides of the scanner to scan, set a radiation threshold, start / pause / cancel a scan, jog the gantry by hand, and save the results.

Built with **PySide6** (Qt) for the UI and **PyVista + CadQuery** for the 3D model.

> Status: frontend covers every main Figma screen. Backend (serial to the MCU) is in progress.

---

## Table of contents

1. [How to run](#how-to-run)
2. [File structure](#file-structure)
3. [How the app is organized](#how-the-app-is-organized)
4. [Page flow](#page-flow)
5. [The 3D model (STEP)](#the-3d-model-step)
6. [The face table](#the-face-table)
7. [Backend plan](#backend-plan)
8. [Motion planner notes (future)](#motion-planner-notes-future)
9. [Temporary / test code to clean up](#temporary--test-code-to-clean-up)
10. [Gotchas we've hit](#gotchas-weve-hit)
11. [Open questions](#open-questions)

---

## How to run

See the README for full setup. Short version, from the repo root:

```bash
just setup   # make the venv + install requirements
just run     # launch the app
```

Without `just`:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app/src/main.py
```

**Requirements:** `PySide6`, `pyvista`, `pyvistaqt`, `cadquery` (and `pyserial` once the real backend exists).

> The first launch after installing CadQuery can be slow (macOS scans the new CAD libraries the first time). Loading the STEP file also adds a few seconds to startup. Both are normal.

---

## File structure

```
app/src/
├── main.py                  # the window: nav bar, page stack, and all the wiring between pages (+ backend later)
├── theme.py                 # every color + font in one place
├── face_table.py            # groups the STEP's CAD faces into scan sides (side1–side5)
├── step_model.py            # StepModel: loads the STEP once, keeps exact faces + drawable meshes
│
├── assets/
│   └── neptune.step         # 3D model of the Neptune scanner (from Michael), in millimeters
│
├── pages/
│   ├── home_page.py         # HomePage: 3D model (pick sides), radiation level, START / JOG, double confirm
│   └── vizx/
│       ├── vizx_page.py             # VizXPage: idle screen, START / JOG
│       ├── scanning_page.py         # ScanPage: progress bar, 3D model (view-only), STOP
│       ├── scanning_stopped_page.py # ScanStoppedPage: paused, RESUME / CANCEL
│       ├── scanning_done_page.py    # ScanDonePage: 3D model, START / JOG, reports, DOWNLOAD
│       ├── jogging_page.py          # JoggingPage: jog pad, SCAN
│       └── error_page.py            # ErrorPage: SYSTEM HALTED, red box, REHOME only
│
├── widgets/                 # reusable pieces, used by multiple pages
│   ├── clickable_label.py   # ClickableLabel: text you can click (nav tabs, links)
│   ├── status.py            # StatusLabel: the "SYSTEM SCANNING..." style text
│   ├── progress_bar.py      # ProgressBar: thin vertical bar + % label
│   ├── jog_pad.py           # JogPad: the round hold-to-move jog controller
│   └── model_view.py        # ModelView: the interactive 3D model (click to pick sides)
│
├── backend/                 # (in progress) talks to the machine
│   ├── base.py              # Backend: the "contract" every backend follows
│   └── fake_backend.py      # FakeBackend: pretend machine for testing without hardware
│
├── test_step.py             # dev script: prints info about every face in the STEP
└── view_step.py             # dev script: shows the model colored by side (checks the face table)

repo root/
├── justfile                 # `just setup`, `just run`
├── requirements.txt
└── README.md
```

**Rule of thumb for where things go:**

| Kind of thing | Goes in |
|---|---|
| A full screen | `pages/` (or `pages/vizx/` for the viz-x side) |
| A piece used on more than one screen | `widgets/` |
| Colors / fonts | `theme.py` |
| Talking to the machine | `backend/` |
| Data about the scanner (face groups) | `face_table.py` |
| Scripts you run directly | `src/` (not inside `widgets/` or `pages/`, or imports break) |

---

## How the app is organized

### The main rule: signals out, methods in

- **Pages never talk to each other, and never touch serial.**
- **A page announces what the user did** with a Qt signal (`start_requested`, `stop_requested`, `jog_pressed`, ...).
- **A page receives updates** through public methods (`start_scan(...)`, `set_progress(...)`, `show_error(...)`, ...).
- **`main.py` is the glue.** It connects page signals to other pages' methods (and later to the backend).

```
pages ──signals──▶ main.py ──calls──▶ backend ──serial──▶ MCU
pages ◀──methods── main.py ◀──signals── backend ◀──serial── MCU
```

This means a page can be redesigned without breaking the others, and the backend can be swapped (fake ↔ real) by changing one line in `main.py`.

### Naming conventions

| Pattern | Meaning |
|---|---|
| `_build_ui`, `_on_start`, `_confirm_scan` | leading underscore = private, only used inside that class |
| `start_scan`, `set_progress`, `show_results` | no underscore = public, meant to be called from outside (main.py / backend) |
| `something_requested` | a signal meaning "the user wants this to happen" |

### Page stack + nav

- All pages live in one `QStackedWidget` in `main.py`. Only one shows at a time.
- Pages are switched with `self.pages.setCurrentWidget(page)` (by object, not index, so the order pages are added doesn't matter).
- **Nav underline:** `_update_nav` runs automatically on every page change (`currentChanged` signal). Home underlines Home; everything else underlines viz-x.
- **Nav lock:** `_set_nav_locked(True)` during a scan, while stopped, and on errors, so the operator can't wander off mid-scan. Locked tabs go gray (`NAV_DISABLED`).

### Shared data

- The STEP file is loaded **once** in `main.py` (`self.step_model = StepModel()`) and passed to every page that shows the 3D model (Home, scanning, done).

---

## Page flow

```
                ┌──────────── JOG ────────────┐
                ▼                             │
HOME ──START──▶ confirm ──▶ final check ──▶ SCANNING ──100%──▶ DONE
 ▲   (pick sides,  (level +     (Enter =      │  (progress,      │ START → HOME
 │    set level)    faces)       Cancel)      │   nav locked)    │ JOG   → JOGGING
 │                                            │                  │ DOWNLOAD → name → save → ✓ / ✗ retry
 │                                          STOP                 │ reports → popup
 │                                            ▼
 │                                         STOPPED ──RESUME──▶ back to SCANNING (progress kept)
 │◀──────────────────────────────CANCEL───────┘
 │
 │◀──REHOME── ERROR (e-stop / radiation over threshold, from ANY page, nav locked, REHOME only)
 │
VIZ-X (idle) ──START──▶ HOME (scans are always set up on Home)
             ──JOG────▶ JOGGING ──SCAN──▶ HOME
                                ──STOP──▶ HOME
```

| Page | Class | Signals out | Public methods in |
|---|---|---|---|
| Home | `HomePage` | `start_requested(list, float)`, `jog_requested` | — |
| viz-x | `VizXPage` | `start_requested`, `jog_requested` | — |
| Scanning | `ScanPage` | `stop_requested`, `scan_finished(list, float)` | `start_scan(faces, level)`, `set_progress(percent)`, `finish_scan()` |
| Stopped | `ScanStoppedPage` | `resume_requested`, `cancel_requested` | — |
| Done | `ScanDonePage` | `new_scan_requested`, `jog_requested` | `show_results(faces, level)`, `set_reports(reports)` |
| Jogging | `JoggingPage` | `stop_requested`, `scan_requested`, `jog_pressed(str, int)`, `jog_released` | — |
| Error | `ErrorPage` | `rehome_requested` | `show_error(message)` |

**Safety details:**
- **Two confirms before a scan starts.** The second one defaults to Cancel, so mashing Enter can't start the machine.
- **STOP = pause** (resumable). **Errors = halt** (e-stop, radiation over threshold); the only way out is REHOME, because the machine can't trust its position after a hard stop.
- **`_finish_scan` ignores "finished" if you're not on the scanning page**, so a late message after STOP/CANCEL can't jump to the done page.
- **Jog is hold-to-move:** press = move, release = stop. Release still fires if the mouse slides off the pad.

---

## The 3D model (STEP)

### Why STEP (not STL)

We have both files, but use the **STEP** because:

- It has **real CAD faces** (77 of them), so face selection is exact, no guessing from triangle directions.
- It keeps **exact geometry + units (mm)**, which the motion planner needs for ~1 mm precision around things that stick out.
- It's the actual CAD file, so it doesn't drift from the design.

Tradeoff: CadQuery is a big dependency (adds a few hundred MB to a PyInstaller build, and slower startup in one-file mode; use `--onedir`).

> The old STL was in **inches**, the STEP is in **millimeters**. Same scanner: ~1867 × 879 × 2044 mm.

### The pipeline

```
assets/neptune.step
   │  CadQuery (importStep)
   ▼
exact CAD faces (77)  ──────────────────▶  kept in StepModel.faces  (for the planner later)
   │  tessellate (0.5 mm)
   ▼
one triangle mesh per face  ────────────▶  kept in StepModel.meshes {face_id: mesh}
   │  PyVista
   ▼
ModelView draws each face as its own actor  →  click → face_id → face table → side
```

### `step_model.py` → `StepModel`

| Attribute | What it is | Used by |
|---|---|---|
| `faces` | list of exact CadQuery faces | motion planner (later) |
| `meshes` | `{face_id: pyvista.PolyData}` | `ModelView` (drawing) |

- `tolerance=0.5` means the drawn triangles stay within 0.5 mm of the real surface. **Display only**; the planner should use the exact `faces`.
- Load it **once** and share it.

### `widgets/model_view.py` → `ModelView`

A `QtInteractor` (PyVista's plotter that is also a Qt widget).

| Thing | What it does |
|---|---|
| `ModelView(step_model)` | clickable (Home) |
| `ModelView(step_model, selectable=False)` | view-only (scanning, done) |
| `face_actors` | `{face_id: actor}`, used to recolor faces. (Not `actors`, that name is taken by PyVista.) |
| `side_of` | `{face_id: side}`, built from the face table |
| `mesh.field_data["face_id"]` | each mesh is "name-tagged" with its face number so a click knows which face it hit |
| `selected_sides()` | sorted list of picked sides, e.g. `["side2", "side5"]` |
| `set_selected(sides)` | pick exactly these sides (select all / clear / highlight what's being scanned) |
| `selection_changed` (signal) | fires with the picked sides whenever the selection changes |

**Clicking:** clicking any face of a side (including its details) toggles the **whole side**. Legs / bottom / feet do nothing.

**Colors:** `MODEL_COLOR` normally, `SELECTED_COLOR` when picked. Background is `BACKGROUND` so the model floats on the page.

**For Deven's readings overlay:** add one method to `ModelView` (e.g. `show_readings(...)`). Because every page uses the same widget, it will show up on scanning and done automatically.

### Dev scripts

| Script | What it does |
|---|---|
| `test_step.py` | prints face count, overall size, and type / area / center / normal for every face (sorted biggest first) |
| `view_step.py` | opens the model colored by side (gray = not in any side), to check the face table |

---

## The face table

`face_table.py` groups the STEP's 77 CAD faces into the 5 scan sides. It's **just data**, no logic.

```python
FACE_TABLE = {
    "side1": {"normal": (0, 1, 0),  "main": [12, 29], "details": [33, 36, 37, 38, 39, 40]},
    "side2": {"normal": (0, -1, 0), "main": [13, 28], "details": [32, 41, 42, 73, 74, 75, 76]},
    "side3": {"normal": (1, 0, 0),  "main": [21, 19], "details": [15]},
    "side4": {"normal": (-1, 0, 0), "main": [23, 25], "details": [16]},
    "side5": {"normal": (0, 0, 1),  "main": [22],     "details": [71, 72]},
}
```

| Side | Direction | Main (sweep these) | Details (work around these) |
|---|---|---|---|
| side1 | +Y | 12 (upper), 29 (lower) | 33 recessed band; 36–40 small box sticking out ~25 mm |
| side2 | −Y | 13 (upper), 28 (lower) | 32 recessed band; 41–42 panel sticking out ~68 mm; 73–76 knob sticking out ~94 mm |
| side3 | +X | 21 (upper), 19 (lower) | 15 recessed band |
| side4 | −X | 23 (upper), 25 (lower) | 16 recessed band |
| side5 | top | 22 | 71–72 post sticking up ~254 mm |
| *not scanned* | | legs (cylinders 45–70, plates 14–35), feet (0–11, 43–62), bottom (27), band ledges (20, 24) | |

- Recessed bands sit around z ≈ 849 mm and are set in ~6–14 mm.
- Every main face is flat (`PLANE`). The 15 round (`CYLINDER`) faces are legs and small details.
- **Side names must match everywhere** (Home selection, face table, planner).
- `side1`–`side5` are placeholder names. Rename to real-world names (front, back, ...) once the team agrees.

> ⚠️ **Face numbers come from the order faces appear in the STEP file.** If the STEP is re-exported, the numbers can change even if the design didn't. Re-run `view_step.py` after every new STEP. Long-term option: find each side's faces by rule (normal + position) instead of hardcoded numbers.

---

## Backend plan

### Two backends, one contract

| | `FakeBackend` | `SerialBackend` |
|---|---|---|
| What it does | pretends to be the machine (fake progress, fake errors) | talks to the real MCU with pyserial |
| Needs hardware? | no | yes |
| Why | test the whole app anywhere, trigger errors on purpose, safe | the real thing |

Both inherit from `Backend` (in `backend/base.py`), so `main.py` only changes one line to switch:

```python
self.backend = FakeBackend()     # testing
self.backend = SerialBackend()   # real hardware
```

### The contract (`backend/base.py`)

| Direction | Name | Meaning |
|---|---|---|
| machine → app (signal) | `connection_changed(bool)` | connected to the MCU or not (→ connection status dot) |
| machine → app (signal) | `progress(int)` | scan progress 0–100 (→ progress bar) |
| machine → app (signal) | `scan_finished()` | scan done (→ done page) |
| machine → app (signal) | `error(str)` | something serious (→ error page) |
| machine → app (signal) | `homed()` | homing finished (→ unlock nav after REHOME) |
| app → machine (method) | `open_connection()` | connect (named this because `QObject` already has `connect`) |
| app → machine (method) | `start_scan(faces, level)` | start a scan |
| app → machine (method) | `pause()` / `resume()` / `abort()` | STOP / RESUME / CANCEL |
| app → machine (method) | `jog(axis, direction)` / `jog_stop()` | hold-to-move jogging |
| app → machine (method) | `home()` | REHOME |

### Where it plugs into `main.py`

Every `# TODO backend` comment in `main.py` becomes a backend call:

| main.py method | Backend call |
|---|---|
| `_start_scan` | `backend.start_scan(faces, level)` |
| `_pause_scan` | `backend.pause()` |
| `_resume_scan` | `backend.resume()` |
| `_cancel_scan` | `backend.abort()` |
| `_jog_start` / `_jog_stop` | `backend.jog(...)` / `backend.jog_stop()` |
| `_rehome` | `backend.home()` (then wait for `homed` before unlocking) |
| `_system_error` | triggered by `backend.error` |

### Steps

1. `Backend` base class
2. `FakeBackend`
3. Wire into `main.py` (replaces the TEMP timers)
4. `SerialBackend` (pyserial, reading on its own thread so the UI never freezes)
5. Connection status dot (grey = not connected, green = getting good readings)

### Things the real backend should eventually do

- Change screens **after the MCU confirms** (e.g. "stopped"), so the screen never lies about the machine.
- Show "HOMING..." after REHOME until `homed` arrives.
- Move file saving (scan data) into the backend once real readings exist.

---

## Motion planner notes (future)

Not built yet. Notes from planning:

- **Input:** the picked side names → look up `FACE_TABLE` → exact faces in `StepModel.faces`.
- **Layer 1 — raster sweep per side:** serpentine back-and-forth over each side's main faces at a fixed standoff.
- **Layer 2 — STEP refinement:** adjust each waypoint using the exact surface under it (holds standoff over bumps / recesses, avoids the panel / knob / post). Needed because some parts stick out and the target is ~1 mm.
- **Output:** a list of waypoints, each with a **position + normal**. The normal is handed to the rotation subsystem (not part of the motion planner).
- **Sequencing between sides:** back away along the normal → travel around the scanner (bounding box + margin, or real geometry if clearance is tight) → approach the next side.
- **Things to pin down:** gantry travel limits, where the scanner sits relative to gantry zero (after homing), sensor footprint (sets step size), detector dwell time (sets speed), required standoff, waypoint format for the rotation team.

---

## Temporary / test code to clean up

| Where | What | Replace with |
|---|---|---|
| `main.py` `_start_scan` | `QTimer.singleShot(...)` fake finish / fake error | `FakeBackend` signals |
| `main.py` `_finish_scan` | `set_reports([...])` fake reports | real reports from the backend |
| `main.py` `_jog_start` / `_jog_stop` | `print(...)` | backend jog calls |
| `home_page.py` | any leftover `print` | delete |
| `src/` | `test_step.py`, `view_step.py` | keep as dev tools, or move to a `scripts/` folder |
| all pages | unused imports copied from Home | delete |

---

## Gotchas we've hit

| Problem | Cause | Fix |
|---|---|---|
| `AttributeError: property 'actors' ... has no setter` | `actors` is already a PyVista property | named ours `face_actors` |
| Spin box text invisible on macOS | `setButtonSymbols(NoButtons)` breaks drawing on macOS | keep the arrows (or hide via stylesheet width 0) |
| `ModuleNotFoundError` for a script in `widgets/` | scripts run from inside a subfolder can't see `src/` modules | keep runnable scripts in `src/` |
| A test script opened a separate PyVista window | importing a script runs all of it (incl. `plotter.show()`) | never import test scripts; keep them out of `widgets/` |
| Pages swapped places | `addWidget` order sets the index | switch pages with `setCurrentWidget(page)` |
| Method "doesn't exist" | `def` indented inside another method, or two methods with the same name | every method `def` is 4 spaces in; Python keeps the last duplicate |
| `"""` comment broke the file | triple quotes can't wrap code that has its own `"""` | delete old code, or use Cmd+/ |
| `STEP File could not be loaded` | wrong path (CadQuery doesn't say "file not found") | file lives at `src/assets/neptune.step` |
| Wrong import name | import path must match file name exactly | `from pages.vizx.scanning_done_page import ScanDonePage` |

---

## Open questions

| Question | Who |
|---|---|
| Real default radiation level (currently `1.0`) | Sean |
| Are the sensor's units actually μSv/h? | Deven |
| Real names for side1–side5 | team |
| Serial: baud rate, command format, what the MCU sends back | firmware |
| Is the radiation sensor on the same serial connection as the motion MCU? | Deven |
| Is the underline enough for "make Home / viz-x clearer"? | Liz |
| Does the survey standard require a specific standoff distance (e.g. 5 cm)? | Sean / Liz |
