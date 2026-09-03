# Developer guides

Start with the [Project structure](structure.md) and the
[Architecture](architecture.md). Frequent tasks:

- [Modify the knowledge base](tasks/modify-kb.md)
- [Implement behaviour](tasks/implement-rule.md)
- [Verify rules](tasks/verify-rules.md)
- [Generate test and parity reports](tasks/generate-test-reports.md)
- [Diagnose failures](tasks/diagnose-bug.md)
- [Modify the application](tasks/modify-application.md)
- [Develop and distribute](tasks/develop-and-release.md)

Application-specific documents:

- [Mordheim Combat Lab verification corpus](../tests/specs/README.md)
- [Campaign Manager guide](campaign-manager.md)
- [Campaign architecture direction](campaign-architecture.md)

## Central command line

Every command in these guides can be run through the single launcher script
`tools/mordheim-utils.py` (no installation needed): `python
tools/mordheim-utils.py --help` lists everything and `<command> --help` shows
the detailed arguments of the delegated command. The lab commands (`verify`,
`parity`, `benchmark`, `audit`, `test-report`, `validate`) behave exactly
like the Combat Lab CLI; the test suites are reached with `python
tools/mordheim-utils.py tests --scope <area>`.

Semantic expectations are reviewed against the written sources, never against
historical engine output.
