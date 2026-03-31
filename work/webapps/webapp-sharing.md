# Design: Complete Spec for WebApp Sharing

The current webapp protocol in OCM (Section 6, lines 924-939 of
IETF-RFC.md) is underspecified. It defines only three fields (`uri`,
`viewMode`, `sharedSecret`) and leaves critical questions unanswered:

1. **Authentication**: Existing PoCs use redirects with credentials in
   the URL, which leaks tokens in browser history, server logs, and
   Referer headers. This violates the spec's own requirement ("MUST NOT
   appear in any URI").
2. **Embedding**: No specification for how to present the remote app to
   the user (iframe, popup, redirect, or something else).

## Design Principles

- Stay consistent with OCM's server-to-server philosophy.
- Build on existing patterns (discovery capabilities, protocol objects,
  Code Flow).

## Definitions

For the purposes of this document, we define a `webapp share` to be "a
resource together with the app to use it".

The resource may be a single file (e.g. a document opened in Collabora)
or a collection of files and environment (e.g. a Jupyter notebook
bundled with its data files, kernel, and runtime environment). What
matters is that the sender provides everything needed to use the
resource, the receiver does not need to supply any part of the
application or data stack.

The alternative would be that a webapp share is a bare app that the
receiver can open arbitrary resources in, but that doesn't match the use
cases we're targeting (document editors, Jupyter notebooks), has major
security implications and would require a more complex discovery
mechanism for the receiver. Hence, a webapp share is not an app you can
open arbitrary documents in, but a specific resource served by an app,
with enough metadata for the receiver to present it meaningfully.

## Architecture Overview

The design has three layers:

```
Layer 1: WebApp Embedding Capabilities
         (extends /.well-known/ocm)
Layer 2: Update WebApp Protocol Object
         (extends share creation)
Layer 3: Application Access
         (uses tokenEndPoint + Form POST)
```

---

## Layer 1: WebApp Embedding Capabilities

When a server receives a webapp share, it needs to present the remote
application to the user. There are three different ways to do this:
iframe, popup, or redirect. Each has different security-,
implementation-, and UX-implications. The receiving server must
advertise which of these modes it supports so that the sending server
can set the appropriate `viewMode` in the protocol object, or decide not
to offer a webapp share at all if the receiver cannot present it.

### Spec Changes

Add three new capabilities to the discovery response.

```
"capabilities": [
  "accept-webapp-iframe",
  "accept-webapp-redirect",
  "accept-webapp-popup",
  ...
]
```

#### Capability definitions

| Capability               | Meaning                                                                                                                           |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| `accept-webapp-iframe`   | This server can embed a remote webapp in an iframe within its own UI. Requires CSP `frame-ancestors` cooperation from the sender. |
| `accept-webapp-redirect` | This server can handle webapp shares by redirecting the user's browser to the remote app.                                         |
| `accept-webapp-popup`    | This server can open the remote webapp in a new browser window/tab.                                                               |

A server MAY advertise multiple capabilities. A server that advertises
none of these does not support receiving webapp shares.

### Usage

The sending server checks the receiver's discovery document before
creating a share with a webapp protocol object. If the receiver supports
the sender's preferred embed mode, the sender uses it. Otherwise, the
sender falls back to a mode the receiver does support, or omits the
webapp protocol entirely.

---

## Layer 2: Enhanced WebApp Protocol Object

The current webapp protocol object carries only a URI and viewMode. The
receiving server cannot determine which application generated the URI,
how to present it to the user, or how to embed it.

The protocol object needs to carry enough information for the receiver
to present the share meaningfully: what the app is called, what it looks
like, and how to display it.

### Spec Changes

Repurpose `viewMode` to describe how the app should be presented to the
user. Replace the current permission semantics of `viewMode` with a
`permissions` array that uses the same format as the webdav protocol
object.

Add optional fields for app presentation.

#### Example

```json
{
  "protocol": {
    "name": "multi",
    "webdav": {
      "uri": "7c084226-d9a1-11e6-bf26-cec0c932ce01",
      "sharedSecret": "server-to-server-secret",
      "permissions": ["read", "write"]
    },
    "webapp": {
      "uri": "7c084226-d9a1-11e6-bf26-cec0c932ce01",
      "sharedSecret": "server-to-server-secret",
      "viewMode": "iframe",
      "permissions": ["read", "write"],
      "appName": "Collabora Online",
      "appIcon": "https://sender.example.org/apps/richdocuments/img/icon.svg"
    }
  }
}
```

#### Changed fields

| Field      | Required | Type   | Description                                                                          |
| ---------- | -------- | ------ | ------------------------------------------------------------------------------------ |
| `viewMode` | Yes      | string | How the app should be presented to the user: `"iframe"`, `"popup"`, or `"redirect"`. |

#### New fields

| Field         | Required | Type            | Description                                                                                                          |
| ------------- | -------- | --------------- | -------------------------------------------------------------------------------------------------------------------- |
| `permissions` | Yes      | array of string | The permissions granted to the sharee, using the same values as the webdav protocol: `"read"`, `"write"`, `"share"`. |
| `appName`     | No       | string          | Human-readable name of the application, used for displaying in the UI (e.g. "Open in Collabora Online").             |
| `appIcon`     | No       | string          | Absolute URI to an application icon. Used by the receiving server to display alongside the app name.                 |

### Notes on `viewMode`

- `"iframe"` - App is embedded within the receiving server's UI. Best UX
  for document editors. The sending server MUST include the receiving
  server's origin (derived from its OCM endpoint) in the
  `Content-Security-Policy: frame-ancestors` directive for the app
  response.
- `"popup"` - App opens in a new browser window. Suitable for complex
  apps that need full-page control.
- `"redirect"` - Browser navigates to the app, leaving the receiving
  server's UI. Simplest to implement, similar to current PoC behavior.

The sending server chooses the mode based on what its application
supports and what the receiver's discovery capabilities indicate it can
handle. A sending server MUST NOT offer a webapp share that the receiver
can not support.

### Role of `sharedSecret`

With the addition of Layer 3, the `sharedSecret` in the webapp object is
used the same way as in the webdav case: it is a **server-to-server
credential** exchanged via the existing Code Flow `tokenEndPoint` for a
bearer token. It is never exposed to the browser. WebApp sharing MUST
use the Code Flow.

---

## Layer 3: Application Access Protocol

A browser cannot set `Authorization` headers on navigations (redirects,
iframe src, window.open). The current PoC puts credentials in the URL,
which is insecure. We need a mechanism that:

1. Keeps tokens out of URLs.
2. Works for all view modes (iframe, popup, redirect).

### 3a. Token Exchange via Existing Code Flow

The receiving server uses the existing OCM Code Flow (Section 8 of the
spec) to exchange the webapp `sharedSecret` for a bearer token via the
sending server's `tokenEndPoint`. This is the same mechanism already
used for webdav token exchange.

The token endpoint issues a token scoped to the permissions that were
advertised in the webapp protocol object's `permissions` array. The
receiving server does not need to request specific permissions or
actions, the sending server already knows what was granted when the
share was created.

For webapp shares, the `access_token` serves as the credential that the
app uses for the entire editing session (e.g. as the WOPI access token
in Collabora/OnlyOffice). The sending server SHOULD therefore issue the
token with a lifetime sufficient for the expected editing session (e.g.
Nextcloud issues WOPI access tokens with 10 hours life time for rich
text editing in Collabora), as communicated via the `expires_in` field.

#### Request

The request follows the existing Code Flow format:

```http
POST {tokenEndPoint} HTTP/1.1
Host: sender.example.org
Content-Type: application/x-www-form-urlencoded
Signature: <httpsig per RFC 9421>

grant_type=authorization_code&code=<webapp sharedSecret>
```

#### Response

The response follows the existing Code Flow format.

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "ocm-webapp-bearer-token",
  "token_type": "Bearer",
  "expires_in": 36000,
}
```

The `access_token` is scoped to the permissions from the webapp protocol
object. The receiving server uses it in the Form POST flow below, it
MUST never placed in a URL.

### 3b. Form POST Authentication

The receiving server delivers the `access_token` to the browser via an
HTML form POST to the webapp `uri` from the protocol object. As per the
existing spec, if `uri` is relative it MUST be resolved against the
sender's OCM endpoint prefix. This keeps the token out of the URL in all
view modes.

The form includes two hidden fields:

- `access_token` - the bearer token from the Code Flow response.
- `access_token_ttl` - the token's expiry as a Unix timestamp in
  milliseconds. This is included for compatibility with WOPI-based apps
  (Collabora, OnlyOffice) which expect this field. Calculated as
  `current_time + expires_in` from the Code Flow response, converted to
  milliseconds.

```html
<!-- viewMode: "iframe" -->
<iframe name="ocm-app-frame" id="ocm-app-frame"> </iframe>
<form
  id="ocm-app-form"
  action="{webapp.uri}"
  method="POST"
  target="ocm-app-frame"
>
  <input
    type="hidden"
    name="access_token"
    value="ocm-webapp-bearer-token"
  />
  <input type="hidden" name="access_token_ttl" value="1743451200000" />
</form>
<script>
  document.getElementById("ocm-app-form").submit();
</script>

<!-- viewMode: "popup" - same, target="_blank" -->
<!-- viewMode: "redirect" - same, target="_top" -->
```

| viewMode   | Form `target` | Result                    |
| ---------- | ------------- | ------------------------- |
| `iframe`   | iframe name   | App loads inside iframe   |
| `popup`    | `_blank`      | App loads in new window   |
| `redirect` | `_top`        | App replaces current page |

The sending server's endpoint at `webapp.uri`:

1. Receives the POST with `access_token` in the body.
2. Validates the token (unexpired, matches share).
3. Establishes a session and returns the application HTML.

How the sending server manages the session after validating the token is
an implementation detail. It may set a session cookie, establish a
WebSocket connection, or use the token internally for further API calls
(as WOPI-based apps like Collabora and OnlyOffice do). OCM does not
prescribe the session mechanism, only that the `access_token` is
delivered via Form POST and MUST NOT appear in a URL.

### WOPI PostMessage

A receiving server that advertises the `accept-webapp-iframe` capability
MAY implement the WOPI PostMessage API for communication between the
host page and the embedded app iframe. This enables richer integration
such as close notifications (`UI_Close`), loading status
(`App_LoadingStatus`), and focus management (`Blur_Focus`,
`Grab_Focus`).

OCM does not define its own PostMessage protocol. Implementors that need
lifecycle events between the host page and embedded app SHOULD use the
WOPI PostMessage API, which is already supported by Collabora,
OnlyOffice, and Microsoft 365.

The `PostMessageOrigin` used for origin validation SHOULD be set to the
receiving server's origin (derived from its OCM endpoint) in the WOPI
`CheckFileInfo` response.

---

## Implementation Note: Collabora Integration

For WOPI-based apps like Collabora, the sending server constructs the
webapp `uri` by combining the app URL from Collabora's WOPI discovery
with a `WOPISrc` parameter pointing to the sending server's own WOPI
endpoint for the shared file. For example:

```
https://collabora.example.org/browser/dist/cool.html
  ?WOPISrc=https://sender.example.org/wopi/files/12345
```

The receiving server's browser Form POSTs the `access_token` and
`access_token_ttl` to this URL. From Collabora's perspective this is a
standard WOPI session, it uses the `access_token` to call back to the
sender's WOPI endpoint (`CheckFileInfo`, `GetFile`, `PutFile`) exactly
as it would for a local user.

---

## Implementation Note: JupyterHub Integration

JupyterHub represents a different integration pattern from WOPI-based
apps. Rather than a single document, the shared resource is typically a
notebook bundled with its data files and runtime environment, a complete
computational context.

The `webapp.uri` points directly at JupyterHub, which uses a custom
authenticator that accepts the OCM `access_token` from the Form POST:

1. The browser Form POSTs the `access_token` directly to JupyterHub (at
   `webapp.uri`).
2. A custom JupyterHub authenticator extracts the `access_token` from
   the POST body and validates it against the sending server's
   `tokenEndPoint` or local token store.
3. The authenticator creates or maps a JupyterHub user from the token's
   context and sets up file access to the shared notebook and its
   bundled data.
4. JupyterHub sets a session cookie and serves the notebook interface.

The sending server SHOULD set the `expiration` field on the share
(already part of the OCM share creation notification) and clean up
temporary resources when the share expires or is deleted.

The protocol object would look like:

```json
{
  "webapp": {
    "uri": "https://jupyterhub.sender.org/hub/ocm/login",
    "sharedSecret": "server-to-server-secret",
    "viewMode": "iframe",
    "permissions": ["read", "write"],
    "appName": "JupyterHub",
    "appIcon": "https://sender.example.org/apps/integration_jupyterhub/img/icon.svg"
  }
}
```

---

## Full Flow Example

Alice (on sender.example.org) shares a document with Bob (on
receiver.example.org). Bob opens it in Collabora via the receiving
server's UI.

```
 Bob's Browser       Receiver Server    Sender Server
      |                   |                     |
      |  1. Click "Open   |                     |
      |   in Collabora"   |                     |
      |  ---------------->|                     |
      |                   |                     |
      |                   | 2. POST             |
      |                   |  {tokenEndPoint}    |
      |                   |  grant_type=        |
      |                   |  authorization_code |
      |                   |  code=<secret>      |
      |                   |  Sig: <httpsig>     |
      |                   | ------------------->|
      |                   |                     |
      |                   | 3. 200 OK           |
      |                   |  { access_token }   |
      |                   | <-------------------|
      |                   |                     |
      |  4. HTML page     |                     |
      |   with form POST  |                     |
      |   into iframe     |                     |
      |  <----------------|                     |
      |                   |                     |
      |  5. Form submits: |                     |
      |   POST webapp.uri |                     |
      |   access_token=.. |                     |
      |  -------------------------------------->|
      |                                         |
      |  6. App validates token,                |
      |   establishes session,                  |
      |   returns editor HTML                   |
      |  <--------------------------------------|
      |                                         |
      |  [Bob edits document]                   |
```

---

## Open Questions

1. **Capability naming.** Are `accept-webapp-iframe`,
   `accept-webapp-redirect`, and `accept-webapp-popup` the right names?
