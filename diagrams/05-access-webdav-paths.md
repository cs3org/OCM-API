# WebDAV Resource Access Paths

Informative: WebDAV access decisions on the Receiving Server.
Diagrams add no new normative rules; see IETF-OCM.md.

```mermaid
flowchart TD
    START["Receiving Server<br/>accesses WebDAV resource"]
    START --> INS["Inspect<br/>protocol.webdav.requirements[]"]
    INS --> MFA{"must-use-mfa<br/>present?"}
    MFA -- "Yes" --> MFAY["Ensure MFA session<br/>before access"]
    MFA -- "No" --> EXW{"must-exchange-token<br/>present?"}
    MFAY --> EXW
    EXW -- "Yes" --> SIGN{"http-sig<br/>capability?"}
    SIGN -- "Yes" --> POSTS["Signed POST<br/>{tokenEndPoint}"]
    SIGN -- "No" --> POSTU["POST {tokenEndPoint}"]
    POSTS --> BEAR["Bearer-only access:<br/>PROPFIND + Authorization"]
    POSTU --> BEAR
    POSTS -- "exchange fails" --> NLEG["No legacy fallback<br/>(strict share)"]
    POSTU -- "exchange fails" --> NLEG
    EXW -- "No" --> PEER{"sender advertises<br/>exchange-token?"}
    PEER -- "Yes" --> ATT{"http-sig<br/>capability?"}
    ATT -- "Yes" --> POSTS2["Signed POST<br/>{tokenEndPoint}"]
    ATT -- "No" --> POSTU2["POST<br/>{tokenEndPoint}"]
    POSTS2 -- "success" --> BEAR
    POSTU2 -- "success" --> BEAR
    POSTS2 -- "fail -> legacy" --> LEG["sharedSecret WebDAV<br/>(legacy fallback)"]
    POSTU2 -- "fail -> legacy" --> LEG
    PEER -- "No" --> LEG
    BEAR --> URI["Compose WebDAV URI<br/>sender-ocm-path + id"]
    URI --> DONE["Resource access<br/>complete"]

    classDef disc fill:#e8f0fe,stroke:#1a73e8,color:#174ea6
    classDef gate fill:#fef7e0,stroke:#b06000,color:#7a5900
    classDef ok fill:#e6f4ea,stroke:#188038,color:#0d652d
    classDef fail fill:#fce8e6,stroke:#d93025,color:#a50e0e
    classDef term fill:#f7d4d0,stroke:#d93025,color:#a50e0e
    classDef neutral fill:#f1f3f4,stroke:#5f6368,color:#3c4043
    classDef share fill:#fce4ec,stroke:#ad1457,color:#9c0066
    classDef sign fill:#e0f7fa,stroke:#00838f,color:#006064
    classDef verify fill:#e8eaf6,stroke:#3949ab,color:#1a237e

    class START,INS,URI disc
    class MFA,EXW,SIGN,PEER,ATT gate
    class MFAY,POSTU,POSTU2,BEAR,DONE ok
    class POSTS,POSTS2 sign
    class NLEG fail
    class LEG neutral
```

- WebDAV URI composition uses the sender's
  `resourceTypes[0].protocols.webdav` (`<sender-ocm-path>`, from the
  sender's discovery queried at the share `sender` FQDN) plus the
  share's `protocol.webdav.uri` as `<id>` when it is not a complete
  URI; PROPFIND targets `https://<sender-host><sender-ocm-path>/<id>`.
- When `must-exchange-token` is in `requirements[]`, the receiver MUST
  exchange via `{tokenEndPoint}` and MUST NOT fall back to
  `sharedSecret` (strict arm; see 03-discovery-sender-consume.md).
- When the requirement is absent but the sender advertises
  `exchange-token`, the receiver MAY attempt exchange and MAY fall back
  to `sharedSecret` on failure.
- `must-use-mfa` in requirements triggers MFA enforcement before access.
- Signed POST to `{tokenEndPoint}` applies when the sender advertises
  `http-sig`; see [Code Flow](../IETF-OCM.md#code-flow).
