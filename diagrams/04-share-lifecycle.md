# Share Lifecycle

Informative: end-to-end share interaction across the four planes.
Diagrams add no new normative rules; see IETF-OCM.md.

```mermaid
flowchart TD
    RECV["Receiver publishes<br/>/.well-known/ocm"] --> PRE["Preflight OK<br/>(see 03-discovery-<br/>sender-consume)"]
    PRE --> CREATE["POST /shares<br/>(sign if http-sig)"]
    RFS["POST /request-share<br/>(MAY trigger)"] -.-> CREATE
    CREATE --> ADM{"admit share?"}
    ADM -- "No" --> DISC["discard notification<br/>(sig/trust/allow/<br/>deny/invite/protocol)"]
    ADM -- "Yes" --> NTF{"notify sender<br/>with outcome?"}
    NTF -- "SHARE_DECLINED" --> END_DECL["SHARE_DECLINED<br/>(terminate)"]
    NTF -- "SHARE_ACCEPTED" --> ACC["POST /notifications<br/>SHARE_ACCEPTED (MAY)"]
    NTF -- "No notification" --> NO_NTF["no notification<br/>(sender polls)"]
    ACC --> ACCESS["receiver accesses<br/>the resource"]
    NO_NTF --> ACCESS
    ACCESS --> N{"protocol?"}
    N -- "webapp" --> WAPP["webapp access<br/>(see 06-access-<br/>webapp-code-flow)"]
    N -- "webdav" --> EXW{"must-exchange-token<br/>in requirements[]?"}
    EXW -- "Yes" --> MUST["MUST exchange<br/>(strict; no legacy;<br/>see 05-access-webdav-paths)"]
    EXW -- "No (DT#4 only)" --> Q["sharedSecret access<br/>(legacy fallback)"]
    EXW -- "No + MAY attempt" --> ATT["MAY attempt exchange<br/>(see 05-access-webdav-paths)"]
    ATT -- "fail -> legacy" --> Q
    MUST --> BEAR["bearer WebDAV access<br/>(see 05-access-webdav-paths)"]
    ATT -- "success" --> BEAR
    ACCESS --> UNSH["SHARE_UNSHARED<br/>(SHOULD sign)"]
    ACCESS --> REVOKE["silent revoke<br/>(MAY; no notify)"]

    classDef disc fill:#e8f0fe,stroke:#1a73e8,color:#174ea6
    classDef gate fill:#fef7e0,stroke:#b06000,color:#7a5900
    classDef ok fill:#e6f4ea,stroke:#188038,color:#0d652d
    classDef fail fill:#fce8e6,stroke:#d93025,color:#a50e0e
    classDef term fill:#f7d4d0,stroke:#d93025,color:#a50e0e
    classDef neutral fill:#f1f3f4,stroke:#5f6368,color:#3c4043
    classDef share fill:#fce4ec,stroke:#ad1457,color:#9c0066
    classDef sign fill:#e0f7fa,stroke:#00838f,color:#006064
    classDef verify fill:#e8eaf6,stroke:#3949ab,color:#1a237e

    class RECV,PRE,WAPP disc
    class ADM,NTF,N,EXW gate
    class CREATE,RFS,ACC share
    class ACCESS ok
    class DISC fail
    class END_DECL,REVOKE term
    class NO_NTF,Q neutral
    class MUST,ATT,BEAR ok
    class UNSH sign
```

- Discovery publish and sender preflight are detailed in
  [02-discovery-receiver-publish.md](02-discovery-receiver-publish.md)
  and [03-discovery-sender-consume.md](03-discovery-sender-consume.md).
- Discard reasons follow [Decision to
  Discard](../IETF-OCM.md#decision-to-discard) (signature, trust/JWKS,
  allow/deny lists, invite trust, protocol/resource checks).
- Share Acceptance Notification is MAY; see [Share Acceptance
  Notification](../IETF-OCM.md#share-acceptance-notification).
- WebDAV access paths preserve legacy fallback on DT#4-only shares
  and on failed optional exchange; see
  [05-access-webdav-paths.md](05-access-webdav-paths.md).
- Post-access updates: `SHARE_UNSHARED` SHOULD be signed; silent revoke
  MAY omit notification. See [General
  Flow](../IETF-OCM.md#general-flow).
