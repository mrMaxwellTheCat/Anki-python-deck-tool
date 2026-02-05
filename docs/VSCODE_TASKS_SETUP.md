# VSCode Tasks Setup Summary

## What Was Created

### 1. `.vscode/tasks.json` (17 tasks total)

Complete task configuration that mirrors GitHub Actions workflows.

#### Task Categories:

**Individual CI Tasks (7)** - Match GitHub Actions exactly:
- `CI: Lint - Ruff Check` → `.github/workflows/ci.yml` lint job
- `CI: Lint - Ruff Format Check` → `.github/workflows/ci.yml` lint job
- `CI: Type Check - mypy` → `.github/workflows/ci.yml` type-check job
- `CI: Test - pytest (basic)` - Quick test run
- `CI: Test - pytest with Coverage` → `.github/workflows/ci.yml` test job
- `CI: Security - pip-audit` → `.github/workflows/security.yml`
- `CI: Security - bandit` → `.github/workflows/security.yml`

**Combined Workflows (3)**:
- `CI Workflow: Lint Job` - Runs both lint checks
- `CI Workflow: Security Job` - Runs both security scans
- `CI Workflow: Full Pipeline (All Checks)` - ⭐ **Runs everything**

**Utility Tasks (4)**:
- `Format: Apply Ruff Formatting` - Auto-format code
- `Format: Apply Ruff Auto-Fixes` - Auto-fix linting issues
- `Coverage: Open HTML Report` - Open coverage in browser
- `Build and Push Debug Deck` - Existing debug task (preserved)

**Installation Tasks (2)**:
- `Install: Dev Dependencies` - `pip install -e ".[dev]"`
- `Install: Security Tools` - Install pip-audit and bandit

---

### 2. `.vscode/README.md`

Comprehensive documentation covering:
- How to run tasks (3 methods)
- Complete task reference
- Common workflows
- Recommended keyboard shortcuts
- Troubleshooting guide
- Comparison with GitHub Actions

---

### 3. `VSCODE_TASKS.md`

Quick reference card for easy lookup:
- Most common tasks listed
- All tasks organized by category
- Recommended keyboard shortcuts
- Quick workflow guide

---

## How to Use

### Method 1: Command Palette (Most Common)

```
Ctrl+Shift+P → "Tasks: Run Task" → Select task
```

### Method 2: Keyboard Shortcuts (Recommended)

Add to your `keybindings.json` (**File → Preferences → Keyboard Shortcuts → Open JSON**):

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

Then use:
- **Ctrl+Shift+F5**: Run full CI pipeline (all checks)
- **Ctrl+Shift+F6**: Run tests with coverage
- **Ctrl+Shift+F7**: Auto-format code

### Method 3: Terminal Menu

```
Menu: Terminal → Run Task...
```

---

## Most Important Task

### ⭐ CI Workflow: Full Pipeline (All Checks)

**Run this before pushing to GitHub!**

It executes in sequence:
1. ✅ Ruff check
2. ✅ Ruff format check
3. ✅ mypy type check
4. ✅ pytest with coverage (96.77%)
5. ✅ pip-audit (dependency vulnerabilities)
6. ✅ bandit (code security)

If all pass, your code is ready to push and CI will pass on GitHub.

---

## Common Workflows

### Before Committing
```
1. Make changes
2. Ctrl+Shift+P → "CI Workflow: Full Pipeline (All Checks)"
3. Wait for all checks to pass ✅
4. Commit & Push
```

### Quick Test Loop
```
1. Write code
2. Ctrl+Shift+P → "CI: Test - pytest with Coverage"
3. Fix issues
4. Repeat
```

### Auto-Fix Linting
```
1. Ctrl+Shift+P → "Format: Apply Ruff Auto-Fixes"
2. Ctrl+Shift+P → "Format: Apply Ruff Formatting"
3. Verify with "CI: Lint - Ruff Check"
```

---

## File Structure

```
.vscode/
├── tasks.json          # Task definitions (17 tasks)
└── README.md          # Detailed documentation

VSCODE_TASKS.md        # Quick reference (root of repo)
```

---

## Benefits

### ✅ Catch Issues Early
Run the same checks locally before pushing → faster feedback loop

### ✅ No Surprises
If local checks pass, GitHub Actions will pass (identical commands)

### ✅ Faster Development
No waiting for CI → instant feedback

### ✅ Learn CI/CD
See exactly what GitHub Actions runs

---

## Integration with GitHub Actions

Each task uses **the exact same command** as GitHub Actions:

| VSCode Task                     | GitHub Actions File              | Command                                 |
|---------------------------------|----------------------------------|-----------------------------------------|
| CI: Lint - Ruff Check           | `.github/workflows/ci.yml`       | `ruff check .`                          |
| CI: Lint - Ruff Format Check    | `.github/workflows/ci.yml`       | `ruff format --check .`                 |
| CI: Type Check - mypy           | `.github/workflows/ci.yml`       | `mypy src --ignore-missing-imports`     |
| CI: Test - pytest with Coverage | `.github/workflows/ci.yml`       | `pytest tests/ -v --tb=short --cov=...` |
| CI: Security - pip-audit        | `.github/workflows/security.yml` | `pip-audit --desc --skip-editable`      |
| CI: Security - bandit           | `.github/workflows/security.yml` | `bandit -r src/ -c pyproject.toml`      |

---

## Tips

1. **Run full pipeline before every push** - saves time catching issues early
2. **Use coverage reports** - Run `Coverage: Open HTML Report` after testing
3. **Auto-format frequently** - Keeps code consistent
4. **Security scans won't block** - They use `continue-on-error` like CI
5. **Watch terminal output** - Detailed error messages help debugging

---

## Requirements

All tools are already in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.9",
    "mypy>=1.7.0",
    ...
]
```

To install everything:
```bash
pip install -e ".[dev]"
pip install pip-audit bandit[toml]
```

Or use the tasks:
- `Install: Dev Dependencies`
- `Install: Security Tools`

---

## Troubleshooting

### "Command not found" errors?
**Solution**: Run `Install: Dev Dependencies` and `Install: Security Tools`

### Tasks not showing up?
**Solution**: Reload VSCode window (`Ctrl+Shift+P` → "Developer: Reload Window")

### Tests failing locally but pass in CI?
**Solution**: Check Python version (should be 3.10+)

### Want to see what a task does?
**Solution**: Check `.vscode/tasks.json` - all commands are visible

---

## Next Steps

1. **Open VSCode** in this project
2. **Try it out**: `Ctrl+Shift+P` → "Tasks: Run Task" → "CI: Test - pytest with Coverage"
3. **Set up shortcuts**: Add keyboard bindings (see above)
4. **Use before pushing**: Run "CI Workflow: Full Pipeline (All Checks)"

---

## Documentation

- **Full Guide**: `.vscode/README.md` (comprehensive documentation)
- **Quick Reference**: `VSCODE_TASKS.md` (this file location in repo root)
- **Task Definitions**: `.vscode/tasks.json` (actual configuration)

---

## Summary

✅ **17 VSCode tasks created** mirroring all GitHub Actions workflows
✅ **Comprehensive documentation** for easy adoption
✅ **Quick reference** for daily use
✅ **Keyboard shortcuts** for efficiency
✅ **Full CI pipeline** runnable locally before push

**Result**: Faster development with earlier issue detection! 🚀
