# Open Cloud Mesh API Specification

![Open Cloud Mesh API](logo.png)

This repository contains the [OpenAPI](https://github.com/OAI/OpenAPI-Specification) (fka Swagger) specification for the Open Cloud Mesh API. This specification describes the RESTful API endpoints which vendors should support to make sharing of resources between different vendors possible.

* [Scope and assumptions](#scope-and-assumptions)
* [API Documentation](#api-documentation)
* [Contributing](#contributing)

## Scope and assumptions

* Provider knows the consumer (both endpoint and user) when it creates a share with the consumer (#26). How this is known is not part of this spec.
* Consumer doesn't have to accept a share, the resource will be available to the consumer immediately (#25).
* Dealing with incoming shares is a vendor specific implementation. One vendor might use an 'accept before' process while another vendor might use a 'decline after' approach. This is considered part of the UX and thus not part of the interaction between different vendors. The consumer could send a notification though, t 
* Reverting access to outgoing shares is a vendor specific implementation. One vendor might delete an entire share while another might invalidate an access token. This is considered part of venor specific internals and thus not part of the intraction between different vendors.
* The actual file sync isn't a part of this specification. To keep this specification 'future proof', the file sync protocol will be embedded as a separate object in Open Cloud Mesh API calls. This protocol object contains all protocol specific options, e.g. WebDAV specific options.

## API Documentation

The specification can be rendered as HTML documentation using [ReDoc](https://github.com/Rebilly/ReDoc):

* [API Reference Documentation](https://rawgit.com/GEANT/OCM-API/v1/docs.html)

## Contributing

The Open Cloud Mesh API specification is an open source, community-driven project. If you'd like to contribute, please follow the [Contributing Guidelines](CONTRIBUTING.md).