# Security Policy

NeuroScribe is a clinical workflow project. Treat every security issue as potentially sensitive.

## Do not report

Do not place API keys, passwords, JWT secrets, database credentials, access tokens, or real patient records in GitHub issues or pull requests.

## Reporting

For a suspected vulnerability, use a private security-reporting channel available to the repository owner rather than publishing exploit details publicly.

When reporting an issue, include:

- affected component/file
- reproducible conditions
- security impact
- minimal proof of concept
- suggested remediation, if known

Redact all secrets and patient-identifying information.

## Security invariants

Changes must preserve:

- authenticated access to protected clinical endpoints
- owner-level authorization
- patient-level retrieval isolation
- secret loading exclusively from environment configuration
- sanitized API error responses
- evidence-grounded clinical generation

## Clinical safety boundary

NeuroScribe must not be changed to independently diagnose patients, assess suicide risk, or prescribe/recommend medication. Clinical information returned by the system should remain traceable to available records.
