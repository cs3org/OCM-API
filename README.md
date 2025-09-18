<p align="center">
  <img src="logo/svg/OpenCloudMesh-text-vertical.svg" alt="Open Cloud Mesh Logo"/>
</p>
<br/>

# Open Cloud Mesh Protocol Specification

This repository contains the text of the [Open Cloud Mesh IETF Draft](https://datatracker.ietf.org/doc/draft-lopresti-open-cloud-mesh/), as well as the equivalent [OpenAPI](https://github.com/OAI/OpenAPI-Specification) (fka Swagger) specification for its API rendered as HTML (by [ReDoc](https://github.com/Redocly/redoc)).

The documents are available as follows:
* **Latest official version, 1.2.1**: [RFC-formatted Draft](https://github.com/cs3org/OCM-API/blob/v1.2.1/IETF-RFC.md) | [API spec](https://cs3org.github.io/OCM-API/docs.html?branch=v1.2.1&repo=OCM-API&user=cs3org)
* Development branch: [RFC-formatted Draft](IETF-RFC.md) | [API spec](https://cs3org.github.io/OCM-API/docs.html?branch=develop&repo=OCM-API&user=cs3org)

[SemVer](https://semver.org) versioning applies to OCM, and backwards compatibility is supported unless stated otherwise by an implementation.

## Testing

In this Org we maintain an [OCM-stub](https://github.com/cs3org/OCM-stub) reference implementation, and a [test suite](https://github.com/cs3org/ocm-test-suite?tab=readme-ov-file#open-cloud-mesh-test-suite-) to run UI-based tests between implementers and the stub.

## Contributing

The Open Cloud Mesh API specification is an open source, community-driven project. The project is actively working on forming an [IETF Working Group](https://www.ietf.org/process/wgs/), please join our [IETF Mailing List](https://mailman3.ietf.org/mailman3/lists/ocm.ietf.org/) if you are interested.

If you'd like to contribute, please follow the [Contributing Guidelines](CONTRIBUTING.md) and the [IETF Note Well](https://www.ietf.org/about/note-well/).

To contribute to the Draft, please do all edits in `IETF-RFC.md` only. A [GitHub action](https://github.com/cs3org/OCM-API/actions/workflows/rfc.yml) is available to prepare a new version of the `IETF-RFC.xml` file for submission to the IETF Datatracker.

## History and Changelog

The history of the Open Cloud Mesh project is [available here](HISTORY.md), including links to external material.

Previously released versions ([changelog](CHANGELOG.md)):
* Version 1.2.0: [RFC-formatted Draft](https://github.com/cs3org/OCM-API/blob/v1.2.0/IETF-RFC.md) | [API spec](https://cs3org.github.io/OCM-API/docs.html?branch=v1.2.0&repo=OCM-API&user=cs3org)
* Version 1.1.0: [README](https://github.com/cs3org/OCM-API/blob/v1.1.0/README.md) | [API spec](https://cs3org.github.io/OCM-API/docs.html?branch=v1.1.0&repo=OCM-API&user=cs3org)
* Version 1.0.0: [API spec](https://cs3org.github.io/OCM-API/docs.html?branch=v1.0.0&repo=OCM-API&user=cs3org)
