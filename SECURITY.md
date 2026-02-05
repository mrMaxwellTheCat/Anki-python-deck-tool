# Security Policy

## Supported Versions

We currently support the following versions of Anki Python Deck Tool with security updates:

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Anki Python Deck Tool seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report a Security Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **GitHub Security Advisories** (Preferred):
   - Go to the [Security tab](https://github.com/mrMaxwellTheCat/Anki-python-deck-tool/security) of this repository
   - Click on "Report a vulnerability"
   - Fill out the form with details about the vulnerability

2. **GitHub Issues** (For less critical issues):
   - Create a new issue with the label "security"
   - Include as much detail as possible about the vulnerability

### What to Include in Your Report

Please include the following information in your report:

- Type of vulnerability (e.g., code injection, cross-site scripting, authentication bypass)
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability, including how an attacker might exploit it

### What to Expect

After you submit a report, you can expect:

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 3 business days.

2. **Investigation**: We will investigate the vulnerability and keep you informed of our progress.

3. **Resolution Timeline**:
   - Critical vulnerabilities: Patch within 7 days
   - High severity: Patch within 30 days
   - Medium/Low severity: Patch in next release

4. **Disclosure**: Once a fix is available, we will:
   - Release a patched version
   - Credit you in the security advisory (unless you prefer to remain anonymous)
   - Publish a security advisory with details about the vulnerability

### Security Best Practices for Users

To use Anki Python Deck Tool securely:

1. **Keep Updated**: Always use the latest version of the tool
2. **Review YAML Files**: Don't build decks from untrusted YAML files
3. **Verify Sources**: Only download example configurations from trusted sources
4. **AnkiConnect**: Ensure AnkiConnect is only accessible locally (not exposed to the internet)
5. **Dependencies**: Keep your Python environment and dependencies up to date
6. **Virtual Environments**: Use virtual environments to isolate dependencies

### Automated Security Scanning

This project uses:
- **pip-audit**: Weekly scans for known vulnerabilities in dependencies
- **bandit**: Static analysis for common security issues in Python code
- **Dependabot**: Automated dependency updates

Security scan results are available in the [Actions tab](https://github.com/mrMaxwellTheCat/Anki-python-deck-tool/actions).

## Known Security Considerations

### YAML Parsing
- This tool uses `yaml.safe_load()` which is safe against arbitrary code execution
- However, extremely large or deeply nested YAML files could cause performance issues
- Always review YAML files from untrusted sources before processing

### AnkiConnect
- AnkiConnect runs on `127.0.0.1:8765` by default
- Never expose AnkiConnect to the internet without proper authentication
- This tool assumes AnkiConnect is running locally and trusted

### File System Access
- The tool reads YAML files and writes .apkg files to specified locations
- Ensure you have appropriate permissions for the directories you're using
- Be cautious with file paths from untrusted sources

## Acknowledgments

We appreciate the security research community's efforts to responsibly disclose vulnerabilities. Contributors who report valid security issues will be credited in our security advisories (unless they prefer anonymity).

## Questions?

If you have questions about this security policy, please open an issue with the "question" label.
