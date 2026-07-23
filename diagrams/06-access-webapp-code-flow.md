# WebApp Code Flow Access

Informative: Receiving Server presents a shared WebApp to the user.
Diagrams add no new normative rules; see IETF-OCM.md.

```mermaid
sequenceDiagram
    autonumber
    actor RP as Receiving Party
    participant B as Receiving Party Browser
    box Receiving Server
        participant RS as Receiving Server
    end
    box Sending Server
        participant TE as Sending Server tokenEndPoint
    end
    box Sending WebApp
        participant SWA as protocol.webapp.uri
    end

    RP->>B: Open shared WebApp in local UI
    B->>RS: Request WebApp presentation
    RS->>RS: Intersect webapp targets<br/>with webapp-receive.targets

    alt No common target
        RS-->>B: WebApp unusable for this share
    else Common target (iframe or blank)
        opt must-use-mfa in requirements
            RS->>B: Ensure MFA session
            B-->>RS: MFA session established
        end

        Note over RS,TE: sharedSecret stays<br/>server-side.
        Note over RS,TE: WebApp requirements carry<br/>must-exchange-token.

        RS->>TE: Code Flow POST<br/>(sign if http-sig)<br/>code=sharedSecret
        TE-->>RS: access_token (short-lived)

        RS->>B: Auto-submit HTML form<br/>(iframe, _blank, or _top)
        B->>SWA: POST<br/>access_token +<br/>expired_session_redirect_uri
        Note over B,SWA: Browser receives access_token only,<br/>never sharedSecret.
        SWA-->>B: Establish session and serve UI

        opt Session expires later
            SWA->>B: Navigate to<br/>expired_session_redirect_uri
            B->>RS: Receiver-controlled restart
            Note over RS,SWA: Receiver may repeat exchange<br/>and form POST.
        end
    end
```

- WebApp shares MUST use the Code Flow; `protocol.webapp.requirements[]`
  always includes `must-exchange-token`. See [Code
  Flow](../IETF-OCM.md#code-flow).
- The Receiving Server POSTs `sharedSecret` to the sender's
  `tokenEndPoint`; signing applies when the sender
  advertises `http-sig`.
- Presentation targets come from intersecting `protocol.webapp.targets`
  with `webapp-receive.targets` in discovery.
- On session expiry the Sending WebApp navigates to
  `expired_session_redirect_uri` (normative field); the receiver may
  repeat exchange and form POST.
- See also [05-access-webdav-paths.md](05-access-webdav-paths.md) for
  WebDAV access and [07-signing-directions.md](07-signing-directions.md)
  for signing on `{tokenEndPoint}`.
