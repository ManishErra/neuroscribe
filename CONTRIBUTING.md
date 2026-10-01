# Contributing to NeuroScribe

## Development principles

1. Preserve patient/owner isolation.
2. Keep clinical answers grounded in available records.
3. Do not introduce diagnostic, suicide-risk, or medication-recommendation behavior.
4. Prefer small, reviewable pull requests.
5. Do not commit secrets or real patient information.
6. Add regression coverage for behavior changes.

## Before opening a pull request

Run:

~~~bash
cd client
npm ci
npm run build
~~~

and:

~~~bash
cd ../backend
python -m compileall -q .
~~~

Run the relevant backend test suites when Python dependencies are available.

## Pull request checklist

- [ ] The change has a clear purpose.
- [ ] Existing patient isolation behavior is preserved.
- [ ] No secrets or patient-identifying data were added.
- [ ] Relevant tests or regression cases were added/updated.
- [ ] Frontend build passes.
- [ ] Documentation was updated when behavior or configuration changed.
- [ ] Deployment/configuration changes are explicitly described.

## Commit style

Use concise conventional-style messages where practical:

- feat: new functionality
- fix: bug fix
- refactor: internal restructuring
- docs: documentation-only change
- test: test-only change
- chore: maintenance/tooling
- security: security hardening

Keep commits focused so they can be reviewed or reverted independently.
