# Sample Scanner Output

Realistic but **entirely synthetic** scanner output used for parser tests
and local development. No real infrastructure, credentials, or findings.

| File | Scanner | What it demonstrates |
|------|---------|----------------------|
| `trivy_sample.json` | Trivy | Container image scan — OS + Python dep vulns |
| `semgrep_sample.json` | Semgrep | SAST scan — SQL injection, hardcoded secret detection, weak crypto |

The Stripe key visible in `semgrep_sample.json` is Stripe's own
[documentation example key](https://stripe.com/docs/keys) and is not a real credential.
It is intentionally present to demonstrate SPECTRA's hardcoded-secret detection.
