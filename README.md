# Open Cloud Mesh API Specification

![Open Cloud Mesh API Specification](logo.png)

This repository contains the [OpenAPI](https://github.com/OAI/OpenAPI-Specification) (fka Swagger) specification for the Open Cloud Mesh API. This specification describes the RESTful API endpoints, request and response headers, possible response codes, request and response formats, hypermedia controls, error handling, and other API design best practices which vendors should support to make sharing of resources between different vendors possible.

* [Scope and assumptions](#scope-and-assumptions)
* [API Documentation](#api-documentation)
* [Contributing](#contributing)

## Scope and assumptions

* Authentication between services is already established. This means that this specification doesn't cover the way a service authenticates incoming API calls (e.g. through an API Key, VPN connection or IP whitelisting). In this scope we assume that the services are already authenticated.
* Provider knows the consumer (both endpoint and user) when it creates a share with the consumer (also see [#26](https://github.com/cs3org/OCM-API/issues/26)). How this is known is not part of this spec.
* Consumer doesn't have to accept a share, the resource will be available to the consumer immediately (#25).
* Dealing with incoming shares is a vendor specific implementation. One vendor might use an 'accept before' process while another vendor might use a 'decline after' approach. This is considered part of the UX and thus not part of the interaction between different vendors. However, the consumer could notify the provider by using the introduced `/notifications` endpoint (also see [#27](https://github.com/cs3org/OCM-API/issues/27)).
* Reverting access to outgoing shares is a vendor specific implementation. One vendor might delete an entire share while another might invalidate an access token. This is considered part of vendor specific internals and thus not part of the interaction between different vendors. However, the provider could notify the consumer by using the introduced `/notifications` endpoint (also see [#27](https://github.com/cs3org/OCM-API/issues/27)).
* The actual file sync isn't a part of this specification. To keep this specification 'future proof', the file sync protocol will be embedded as a separate object in Open Cloud Mesh API calls. This protocol object contains all protocol specific options, e.g. WebDAV specific options.

## API Documentation

The specification can be rendered as HTML documentation using [ReDoc](https://github.com/Redocly/redoc):

* [API Reference Documentation](https://cs3org.github.io/OCM-API/docs.html)

## Contributing

The Open Cloud Mesh API specification is an open source, community-driven project. If you'd like to contribute, please follow the [Contributing Guidelines](CONTRIBUTING.md).
