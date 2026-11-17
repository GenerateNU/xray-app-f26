# LuX-RAY APP 
this is the repository for the app for LuX-Ray.

## Project Structure
```
app/src/
    main.py          # app window, nav bar, page switching
    theme.py         # all colors and fonts
    pages/
        home_page.py # face select, radiation level, START / JOG
        vizx/        # viz-x, scanning, and jogging pages
    widgets/         # reusable pieces (status label, etc.)
```

## Requirements
Python 3.14 (see `.python-version`)
- (optional) [`just`](https://github.com/casey/just) for shortcut commands
  - Mac: `brew install just`

### Option 1: Using `just` (recommended)

```bash
just setup   # make the venv and install all requirements
just run     # launch the app
```

Run `just` by itself to see every available command.

---

### Option 2: Without `just`

**1. Make a virtual environment**
```bash
python3 -m venv .venv
```

**2. Activate it**
```bash
# Mac / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**3. Install requirements**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**4. Run the app**
```bash
python app/src/main.py
```

---

## Documentation
Documentation, style-guides, and best practices should be kept in a repo level folder `docs/`. It is crucial to have
your team reference these docs extensively to provide a consistent styling of code across the repo.

## CI/CD
It is critical that on every single merge to main, you enable a specific subset of checks to run. These should include
- Linting/Formatting
- Unit/Integration Tests
- Deployments (Sometimes its better to allocate another branch for deployments, such as `release` or `production`)

You might find it useful to call some upstream workflows from [Shiperate](https://github.com/GenerateNU/shiperate/tree/main)

## Branch Information: 

gui-3d --> all 3d modeling features

gui --> basic frontend features. 