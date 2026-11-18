# Contributing Guidelines

Our [Issues tracker](https://github.com/cs3org/OCM-API/issues) can be used to discuss problems or additions to the current or next version of the Open Cloud Mesh API specification. Additionally, in our [Discussions forum](https://github.com/cs3org/OCM-API/discussions) you are welcome to bring up ideas, questions, and any other item that may be of interest for Open Cloud Mesh.

Please follow these guidelines before opening an issue:

* Make sure your issue is not a duplicate.
* Make sure your issue is relevant to the specification.

To contribute to the Internet Draft, please do all edits in the markdown files only. A [GitHub action](https://github.com/cs3org/OCM-API/actions/workflows/rfc.yml) is available to prepare a new version of the `IETF-RFC.xml` file for submission to the IETF Datatracker.

To preview the changes of your PR, you can change the repo and branch in the API docs URL.
For instance to see the proposed changes of https://github.com/cs3org/OCM-API/pull/41, use:
[https://cs3org.github.io/OCM-API/docs.html?repo=OCM-API&branch=add-endpoint-to-accept-invite](https://cs3org.github.io/OCM-API/docs.html?repo=OCM-API&branch=add-endpoint-to-accept-invite)

## Draft checks

Pull requests check clear sentence boundaries in changed draft prose against
the [RFC 7322 spacing convention](https://www.rfc-editor.org/rfc/rfc7322.html#section-3.2).
The source checker skips code examples and leaves all source files unchanged.

The workflow renders all three drafts with kramdown-rfc and xml2rfc, then
runs [idnits](https://github.com/ietf-tools/idnits). New idnits errors fail
the check; `.github/ietf/idnits-baseline.json` allows eight existing long
example lines individually, preserving their literal contents.

Selected [ietf-vale](https://github.com/OR13/ietf-vale) community rules
provide advisory prose suggestions. Download the `internet-drafts` artifact
from the Actions run for XML, text and HTML previews, idnits reports and
`prose.json`.

Run the source checks locally with:

```sh
python tools/check_draft_style.py --base develop IETF-*.md
python -m unittest discover -s tests -p test_draft_style.py
```

Use your PR's base branch for `--base`. Omit it to check all prose, including
older spacing issues. Manual workflow runs also check the complete sources.

The render commands and pinned tools are in
`.github/workflows/draft-validation.yml`.
