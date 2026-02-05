# VSCode Tasks Quick Reference

## Run Tasks: `Ctrl+Shift+P` → "Tasks: Run Task"

### ⭐ Most Common

| Task                                        | Description                   |
|---------------------------------------------|-------------------------------|
| **CI Workflow: Full Pipeline (All Checks)** | Run ALL checks before pushing |
| **CI: Test - pytest with Coverage**         | Run tests (use this often)    |
| **Format: Apply Ruff Formatting**           | Auto-format code              |

### 📋 All Available Tasks

#### Individual CI Tasks
- `CI: Lint - Ruff Check` - Check linting
- `CI: Lint - Ruff Format Check` - Check formatting
- `CI: Type Check - mypy` - Type check with mypy
- `CI: Test - pytest (basic)` - Quick test run
- `CI: Test - pytest with Coverage` - Full test with coverage
- `CI: Security - pip-audit` - Check dependencies
- `CI: Security - bandit` - Check code security

#### Combined Workflows
- `CI Workflow: Lint Job` - All linting checks
- `CI Workflow: Security Job` - All security scans
- `CI Workflow: Full Pipeline (All Checks)` - **Everything**

#### Utilities
- `Format: Apply Ruff Formatting` - Auto-format
- `Format: Apply Ruff Auto-Fixes` - Auto-fix issues
- `Coverage: Open HTML Report` - View coverage
- `Install: Dev Dependencies` - Setup dev environment
- `Install: Security Tools` - Setup security tools

---

## Recommended Keyboard Shortcuts

Add to `keybindings.json`:

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

---

## Quick Workflow

1. **Write code**
2. `Ctrl+Shift+F7` - Format
3. `Ctrl+Shift+F6` - Test
4. `Ctrl+Shift+F5` - Full CI check
5. **Commit & Push** ✅

---

See `.vscode/README.md` for detailed documentation.
