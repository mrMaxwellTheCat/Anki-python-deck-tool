# Manual Setup Guide for Anki Python Deck Tool

This guide covers everything you need to set up manually, including API keys, secrets, and configurations.

## Table of Contents
1. [GitHub Repository Secrets](#github-repository-secrets)
2. [Codecov Integration](#codecov-integration)
3. [PyPI Publishing Setup](#pypi-publishing-setup)
4. [Dependabot Configuration](#dependabot-configuration)
5. [Optional: GitHub Pages](#optional-github-pages)
6. [Verification Steps](#verification-steps)

---

## 1. GitHub Repository Secrets

GitHub Secrets are used to store sensitive information like API tokens. You need to add these manually through the GitHub web interface.

### How to Add Secrets

1. Go to your repository on GitHub: `https://github.com/mrMaxwellTheCat/Anki-python-deck-tool`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the secrets listed below

---

## 2. Codecov Integration

**Status: OPTIONAL** - The CI workflow will work without this, but coverage reports won't be uploaded.

### What is Codecov?
Codecov provides visual coverage reports and tracks coverage over time. It's free for open-source projects.

### Setup Steps

#### Step 1: Sign Up for Codecov
1. Go to [https://codecov.io](https://codecov.io)
2. Click **Sign up** with GitHub
3. Authorize Codecov to access your repositories

#### Step 2: Add Your Repository
1. After signing in, Codecov should automatically detect your repository
2. If not, click **Add repository** and select `Anki-python-deck-tool`

#### Step 3: Get the Codecov Token
1. In Codecov, go to your repository settings
2. Find the **Upload token** (also called repository token)
3. Copy the token (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

#### Step 4: Add Token to GitHub Secrets
1. Go to GitHub: **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `CODECOV_TOKEN`
4. Value: Paste the token from Codecov
5. Click **Add secret**

### What Happens After Setup
- Every push to main will upload coverage reports to Codecov
- The coverage badge in README.md will show live coverage %
- You'll get detailed coverage reports at `https://codecov.io/gh/mrMaxwellTheCat/Anki-python-deck-tool`

### If You Skip This
- ✅ CI will still pass (we set `fail_ci_if_error: false`)
- ❌ No coverage reports or visualizations
- ⚠️ Coverage badge will show "unknown"

---

## 3. PyPI Publishing Setup

**Status: REQUIRED for releases** - Only needed when you want to publish to PyPI.

### What is PyPI?
PyPI (Python Package Index) is where Python packages are published so users can install them with `pip install anki-yaml-tool`.

### Option A: Trusted Publishing (RECOMMENDED - No Token Needed!)

This is the modern, secure way. GitHub Actions can publish directly to PyPI without storing tokens.

#### Prerequisites
- You must already have published the package once manually, OR
- You must be added as a maintainer to an existing PyPI project

#### Setup Steps

1. **Create PyPI Account** (if you don't have one)
   - Go to [https://pypi.org](https://pypi.org)
   - Create an account
   - **IMPORTANT**: Enable 2FA (Two-Factor Authentication) for security

2. **Configure Trusted Publishing on PyPI**
   - Go to your PyPI account: [https://pypi.org/manage/account/publishing/](https://pypi.org/manage/account/publishing/)
   - Click **Add a new publisher**
   - Fill in the form:
     - **PyPI Project Name**: `anki-yaml-tool` (must match `name` in `pyproject.toml`)
     - **Owner**: `mrMaxwellTheCat` (your GitHub username)
     - **Repository name**: `Anki-python-deck-tool`
     - **Workflow name**: `release.yml`
     - **Environment name**: Leave blank (not using environments)
   - Click **Add**

3. **That's it!** No tokens needed. When you push a tag, GitHub Actions can publish automatically.

### Option B: Manual Token Setup (Legacy Method)

Only use this if trusted publishing doesn't work.

#### Setup Steps

1. **Generate PyPI API Token**
   - Go to PyPI account settings: [https://pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)
   - Click **Add API token**
   - Token name: `github-actions-anki-yaml-tool`
   - Scope: Select **Project: anki-yaml-tool** (or "Entire account" if project doesn't exist yet)
   - Click **Add token**
   - **IMPORTANT**: Copy the token immediately (starts with `pypi-`). You won't see it again!

2. **Add Token to GitHub Secrets**
   - Go to GitHub: **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `PYPI_API_TOKEN`
   - Value: Paste the token from PyPI
   - Click **Add secret**

3. **Update Release Workflow**
   - If you used Option A (trusted publishing), you're already good!
   - If using a token, the workflow might need modification (current version uses trusted publishing)

### How to Publish a Release

Once set up, releasing is simple:

```bash
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md with release notes
# 3. Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.2.0"
git push

# 4. Create and push a version tag
git tag v0.2.0
git push origin v0.2.0
```

The release workflow will automatically:
1. Build the package
2. Run checks
3. Publish to PyPI
4. Create a GitHub Release

---

## 4. Dependabot Configuration

**Status: AUTOMATIC** - Already configured, no manual setup needed!

### What is Dependabot?
Dependabot automatically creates pull requests to update your dependencies weekly.

### What's Already Configured
- ✅ Weekly dependency updates for Python packages
- ✅ Weekly updates for GitHub Actions
- ✅ Automatic PR creation with grouped updates

### What You Need to Do
**Nothing!** Dependabot will start working automatically. Just:
1. Watch for PRs from `dependabot[bot]`
2. Review and merge them
3. The PRs will include changelogs and compatibility info

### Example Dependabot PR
```
Update pytest from 7.4.0 to 7.4.3
- Changelog: https://...
- Commits: pytest-dev/pytest@7.4.0...7.4.3
```

---

## 5. Optional: GitHub Pages

**Status: OPTIONAL** - For hosting documentation website.

If you want to host documentation (Phase 4 from roadmap):

### Setup Steps

1. Go to **Settings** → **Pages**
2. Under **Source**, select:
   - Source: **Deploy from a branch**
   - Branch: `gh-pages` (or `main` if you put docs in `/docs` folder)
   - Folder: `/` (root) or `/docs`
3. Click **Save**

### Future Use
- When you create documentation with MkDocs or Sphinx (Phase 4)
- The docs will be accessible at: `https://mrMaxwellTheCat.github.io/Anki-python-deck-tool/`

---

## 6. Verification Steps

### Verify GitHub Actions Work

After adding secrets, test that workflows pass:

#### Test CI Workflow
```bash
# Make a small change and push
git add .
git commit -m "Test CI workflow"
git push origin main
```

Check at: `https://github.com/mrMaxwellTheCat/Anki-python-deck-tool/actions`

You should see:
- ✅ Lint with Ruff (passing)
- ✅ Type Check with mypy (passing)
- ✅ Test with pytest (9 jobs, all passing)

#### Test Security Workflow

Security workflow runs automatically on push and weekly. Check:
- Go to **Actions** → **Security**
- You should see successful runs (or runs that complete with continue-on-error)

#### Test Coverage Upload

If you set up Codecov:
1. Push a commit
2. Wait for CI to complete
3. Check Codecov dashboard: `https://codecov.io/gh/mrMaxwellTheCat/Anki-python-deck-tool`
4. Coverage badge in README should update

---

## Summary: What's Required vs Optional

### ✅ Already Done (No Action Needed)
- GitHub Actions workflows configured
- Dependabot configured
- Pre-commit hooks configured
- All CI/CD infrastructure ready

### 🔴 Required for Full Functionality
1. **Codecov Token** (for coverage reports)
   - 5 minutes setup
   - Free for open source
   - Highly recommended

2. **PyPI Trusted Publishing** (for releases)
   - 5 minutes setup
   - Only needed when ready to publish
   - Can wait until v1.0

### 🟢 Optional
- GitHub Pages (for documentation website)
- Additional GitHub integrations

---

## Quick Start Checklist

For immediate functionality, do these in order:

- [ ] **Step 1**: Sign up for Codecov (5 min)
- [ ] **Step 2**: Add `CODECOV_TOKEN` to GitHub Secrets (2 min)
- [ ] **Step 3**: Push a commit and verify CI passes (2 min)
- [ ] **Step 4**: Check coverage badge updates (1 min)
- [ ] **Step 5** (Optional): Set up PyPI trusted publishing (5 min, can do later)

**Total Time**: ~15 minutes for full setup

---

## Troubleshooting

### CI Failing?

**Check 1: Type-check job fails**
- Fixed: Now uses `pip install -e ".[dev]"` instead of deleted `requirements.txt`
- Solution: Pull latest changes from main

**Check 2: Coverage upload fails**
- If you see "Codecov token not found" - add `CODECOV_TOKEN` secret
- If you haven't set up Codecov yet - CI will still pass (non-blocking)

**Check 3: Tests fail on Windows/Mac**
- Check the specific failure in GitHub Actions logs
- Tests should pass on all platforms (they do locally)

### Codecov Not Working?

**Issue: Badge shows "unknown"**
- Wait 5-10 minutes after first upload
- Check Codecov dashboard for successful upload
- Verify token is correct

**Issue: Coverage not uploading**
- Check CI logs for Codecov step
- Verify `CODECOV_TOKEN` secret is set
- Check token hasn't expired

### PyPI Release Fails?

**Issue: "Trusted publisher not configured"**
- You need to set up trusted publishing on PyPI first
- See Option A in PyPI Publishing Setup above

**Issue: "Permission denied"**
- Verify you're a maintainer of the PyPI project
- Check your PyPI account permissions

---

## Need Help?

If you encounter issues:

1. **Check GitHub Actions logs**:
   - Go to Actions tab → Click failed workflow → Check job logs

2. **Check this repository's issues**:
   - [GitHub Issues](https://github.com/mrMaxwellTheCat/Anki-python-deck-tool/issues)

3. **Common documentation**:
   - [GitHub Actions docs](https://docs.github.com/en/actions)
   - [Codecov docs](https://docs.codecov.com)
   - [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/)

---

## File Locations Reference

For quick reference, here's where everything is:

```
.github/
├── workflows/
│   ├── ci.yml          # Main CI pipeline (lint, type-check, test, coverage)
│   ├── security.yml    # Security scanning (pip-audit, bandit)
│   └── release.yml     # PyPI publishing on tags
├── dependabot.yml      # Dependency updates configuration
├── ISSUE_TEMPLATE/     # Issue templates
└── PULL_REQUEST_TEMPLATE.md

pyproject.toml          # Dependencies, tool configs, coverage settings
SECURITY.md            # Security policy
CODE_OF_CONDUCT.md     # Community guidelines
CHANGELOG.md           # Version history
```

---

**Status**: All workflows fixed and ready to use! 🎉
