# Open Cloud Mesh Protocol Specification

![Open Cloud Mesh Protocol Specification](logo.png)

This repository contains the specification of the Open Cloud Mesh protocol, including
the [OpenAPI](https://github.com/OAI/OpenAPI-Specification) (fka Swagger) specification for its API. This specification describes disovery and use of the RESTful API endpoints, request and response headers, possible response codes, request and response formats, hypermedia controls, error handling, and other API design best practices which vendors should support to make sharing of resources between different vendors possible.

* [Scope and assumptions](#scope-and-assumptions)
* [Specification](#specification)
  * [Discovery](#discovery)
  * [Share Creation](#create)
  * [Share Acceptance](#accept)
  * [Share Deletion](#unshare)
  * [Share Updating](#update)
  * [Resharing](#reshare)

* [Contributing](#contributing)

## Scope and assumptions

* Provider knows the consumer (both endpoint and user) when it creates a share with the consumer (also see [#26](https://github.com/cs3org/OCM-API/issues/26)). How this is known is not part of this spec.
* Consumer doesn't have to accept a share, the resource will be available to the consumer immediately (#25).
* Dealing with incoming shares is a vendor specific implementation. One vendor might use an 'accept before' process while another vendor might use a 'decline after' approach. This is considered part of the UX and thus not part of the interaction between different vendors. However, the consumer could notify the provider by using the introduced `/notifications` endpoint (also see [#27](https://github.com/cs3org/OCM-API/issues/27)).
* Reverting access to outgoing shares is a vendor specific implementation. One vendor might delete an entire share while another might invalidate an access token. This is considered part of vendor specific internals and thus not part of the interaction between different vendors. However, the provider could notify the consumer by using the introduced `/notifications` endpoint (also see [#27](https://github.com/cs3org/OCM-API/issues/27)).
* The actual file sync isn't a part of this specification. To keep this specification 'future proof', the file sync protocol will be embedded as a separate object in Open Cloud Mesh API calls. This protocol object contains all protocol specific options, e.g. WebDAV specific options.


## Specification
### Discovery
Authentication between services is already established. This means that this specification doesn't cover the way a service authenticates incoming API calls (e.g. through an API Key, VPN connection or IP whitelisting). In this scope we assume that the services are already authenticated.

If a finite whitelist of receiver servers exists on the sender
side, then this list may already contain all necessary endpoint details.

When a sending server allows sending to any internet-hosted receiving server, then discovery can happen from the sharee address, using the `/ocm-provider` well-known URL that receiving servers MAY provide. For instance, if `alice at sender.com` wants to share a resource with `bob at receiver.com` then a GET call can be made to
`https://receiver.com/ocm-provider` to which the receiving server MAY respond with
a JSON document containing for instance:
```json
{
  "enabled":true,
  "apiVersion":"1.0-proposal1",
  "endPoint": "https://receiver.com/api/ocm",
  "resourceTypes": [
    {
      "name":"file",
      "shareTypes": ["user", "group"],
      "protocols": {
        "webdav": (any string)
      }
    }
  ]
}
```

### Share Creation
To create a share, the sending server SHOULD make a HTTP POST request to the `/shares` endpoint of the receiving server ([docs](https://cs3org.github.io/OCM-API/docs.html?branch=develop&repo=OCM-API&user=cs3org#/paths/~1shares/post)).

### Share Acceptance
In response to a share creation, the receiving server MAY send back a [notification](https://cs3org.github.io/OCM-API/docs.html?branch=develop&repo=OCM-API&user=cs3org#/paths/~1notifications/post) to the sending server, with  `notificationType` set to `"SHARE_ACCEPTED"` or `"SHARE_DECLINED"`. The sending server MAY expose this information to the end user. 

### Share Deletion
A `"SHARE_ACCEPTED"` notification followed by a `"SHARE_UNSHARED"` notification is
equivalent to a `"SHARE_DECLINED"` notification.

### Share Updating
TODO: document `"RESHARE_CHANGE_PERMISSION"`

### Resharing
The `"REQUEST_RESHARE"` and `"RESHARE_UNDO"` notification types may be user by the
receiving server to persuarde the sending server to share the same resource with another share recipient.
TODO: document how receiver.com can know if sender.com understood and processed the
reshare request.

## Contributing

The specification can be rendered as HTML documentation using [ReDoc](https://github.com/Redocly/redoc):

* [API Reference Documentation](https://cs3org.github.io/OCM-API/docs.html)


The Open Cloud Mesh API specification is an open source, community-driven project. If you'd like to contribute, please follow the [Contributing Guidelines](CONTRIBUTING.md).

To stage the changes of your PR, you can change the repo and branch in the URL.
For instance to see the proposed changes of https://github.com/cs3org/OCM-API/pull/41, use:
[https://cs3org.github.io/OCM-API/docs.html?branch=add-endpoint-to-accept-invite&repo=OCM-API&user=LovisaLugnegard](https://cs3org.github.io/OCM-API/docs.html?branch=add-endpoint-to-accept-invite&repo=OCM-API&user=LovisaLugnegard)
