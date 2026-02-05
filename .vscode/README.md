# VSCode Tasks for Anki Python Deck Tool

This directory contains VSCode tasks that replicate GitHub Actions workflows for local testing.

## Quick Start

### Running Tasks

**Method 1: Command Palette**
1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type "Tasks: Run Task"
3. Select a task from the list

**Method 2: Keyboard Shortcuts**
- `Ctrl+Shift+B`: Run default build task
- `Ctrl+Shift+T`: Run default test task

**Method 3: Terminal Menu**
- Menu: **Terminal → Run Task...**

---

## Available Tasks

### 🎯 Most Important

| Task | Description | Use When |
|------|-------------|----------|
| **CI Workflow: Full Pipeline (All Checks)** | Runs ALL checks sequentially | Before pushing to GitHub |
| **CI: Test - pytest with Coverage** | Run tests with coverage reports | After making code changes |
| **Format: Apply Ruff Formatting** | Auto-format all code | Before committing |

---

## Task Categories

### 🔍 Individual CI Tasks (GitHub Actions Equivalents)

These match exactly what runs in GitHub Actions:

- **CI: Lint - Ruff Check** - Check for linting issues (→ `.github/workflows/ci.yml` lint job)
- **CI: Lint - Ruff Format Check** - Check code formatting (→ `.github/workflows/ci.yml` lint job)
- **CI: Type Check - mypy** - Static type checking (→ `.github/workflows/ci.yml` type-check job)
- **CI: Test - pytest (basic)** - Run tests without coverage (quick)
- **CI: Test - pytest with Coverage** - Run tests with coverage report (→ `.github/workflows/ci.yml` test job)
- **CI: Security - pip-audit** - Scan for dependency vulnerabilities (→ `.github/workflows/security.yml`)
- **CI: Security - bandit** - Scan for code security issues (→ `.github/workflows/security.yml`)

### 📦 Composite Workflows

Run multiple checks together:

- **CI Workflow: Lint Job** - Both ruff checks (check + format)
- **CI Workflow: Security Job** - Both security scans (pip-audit + bandit)
- **CI Workflow: Full Pipeline (All Checks)** - ⭐ **RECOMMENDED** - Run everything

### 🛠️ Utility Tasks

- **Format: Apply Ruff Formatting** - Auto-format your code
- **Format: Apply Ruff Auto-Fixes** - Auto-fix linting issues
- **Coverage: Open HTML Report** - Open coverage report in browser (after running coverage task)

### 📥 Installation Tasks

- **Install: Dev Dependencies** - Install all dev dependencies (`pip install -e ".[dev]"`)
- **Install: Security Tools** - Install pip-audit and bandit

### 🐛 Debug Task

- **Build and Push Debug Deck** - Build and push the debug deck to Anki (existing task)

---

## Common Workflows

### Before Committing

Run the full CI pipeline locally:

```
Ctrl+Shift+P → "Tasks: Run Task" → "CI Workflow: Full Pipeline (All Checks)"
```

This runs (in order):
1. Ruff check
2. Ruff format check
3. mypy type check
4. pytest with coverage
5. pip-audit
6. bandit

If all pass ✅, your code is ready to push!

### After Writing Code

Quick test run:

```
Ctrl+Shift+T (or run "CI: Test - pytest with Coverage")
```

### Fixing Linting Issues

Auto-fix what can be fixed:

```
1. Run "Format: Apply Ruff Auto-Fixes"
2. Run "Format: Apply Ruff Formatting"
3. Run "CI: Lint - Ruff Check" to verify
```

### First Time Setup

If you just cloned the repo:

```
1. Run "Install: Dev Dependencies"
2. Run "Install: Security Tools"
3. Run "CI Workflow: Full Pipeline (All Checks)" to verify everything works
```

---

## Task Output

- **success**: All tasks show their output in the integrated terminal
- **clear**: Most tasks clear the terminal before running for clean output
- **panel**: Tasks share a panel to avoid clutter
- **problemMatcher**: Type check tasks integrate with VSCode's problems panel

---

## Keyboard Shortcuts (Recommended)

Add these to your `keybindings.json` (File → Preferences → Keyboard Shortcuts → Open Keyboard Shortcuts JSON):

```json
[
  {
    "key": "ctrl+shift+f5",
    "command": "workbench.action.tasks.runTask",
    "args": "CI Workflow: Full Pipeline (All Checks)"
  },
  {
    "key": "ctrl+shift+f6",
    "command": "workbench.action.tasks.runTask",
    "args": "CI: Test - pytest with Coverage"
  },
  {
    "key": "ctrl+shift+f7",
    "command": "workbench.action.tasks.runTask",
    "args": "Format: Apply Ruff Formatting"
  }
]
```

Then:
- `Ctrl+Shift+F5`: Run full CI pipeline
- `Ctrl+Shift+F6`: Run tests with coverage
- `Ctrl+Shift+F7`: Auto-format code

---

## Comparing with GitHub Actions

| GitHub Workflow | VSCode Task |
|----------------|-------------|
| `.github/workflows/ci.yml` → Lint job | **CI Workflow: Lint Job** |
| `.github/workflows/ci.yml` → Type-check job | **CI: Type Check - mypy** |
| `.github/workflows/ci.yml` → Test job | **CI: Test - pytest with Coverage** |
| `.github/workflows/security.yml` | **CI Workflow: Security Job** |
| All workflows combined | **CI Workflow: Full Pipeline (All Checks)** |

---

## Troubleshooting

### Task not found?
Reload VSCode window: `Ctrl+Shift+P` → "Developer: Reload Window"

### Command not found (ruff, pytest, etc.)?
Run `Install: Dev Dependencies` and `Install: Security Tools` first.

### Tests failing locally but pass in CI?
Make sure you're running in the same Python version (3.10+).

---

## Tips

1. **Run full pipeline before pushing** to catch issues early
2. **Use coverage reports** to identify untested code
3. **Security scans** use `continue-on-error` like CI, so warnings won't block
4. **Format regularly** to maintain code consistency
5. **Watch the terminal** for detailed error messages

---

## File Structure

```
.vscode/
├── tasks.json          # Task definitions (this is what you configured)
└── README.md          # This file (documentation)
```

---

For more information about the CI/CD setup, see:
- `MANUAL_SETUP_GUIDE.md` - GitHub Actions secrets setup
- `.github/workflows/` - Actual GitHub Actions workflows
- `CONTRIBUTING.md` - Development guidelines
