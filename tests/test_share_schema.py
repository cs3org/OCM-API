"""Core share constraints and published-example checks from IETF-OCM.md."""

from copy import deepcopy
import base64
import hashlib
import json
import re
import shlex
import unittest

from jsonschema import Draft4Validator
from jsonschema.validators import validator_for

from test_extension_schemas import ROOT, load_spec


def share_request(draft):
    blocks = []
    for match in re.finditer(
            r'<sourcecode\b([^>]*)>\n(.*?)\n</sourcecode>', draft, re.S):
        if 'anchor=core-share-request-example' in shlex.split(match[1]):
            blocks.append(match[2])
    if len(blocks) != 1:
        raise ValueError("expected exactly one core-share-request-example anchor")
    http = blocks[0]
    body = http.split("\n\n", 1)[1]
    return http, body, json.loads(body)


def check_example_relations(share):
    """Local example assertions; structure must be validated first."""
    protocol = share["protocol"]
    webapp = protocol.get("webapp", {})
    names = [app["name"] for app in webapp.get("apps", [])]
    assert len(names) == len(set(names)), "duplicate app name"
    if "webdav" in protocol and "webapp" in protocol:
        assert (set(protocol["webdav"].get("requirements", [])) ==
                set(webapp.get("requirements", []))), "requirements disagree"
    if "encryption" in share:
        encryption = share["encryption"]
        selected = encryption.get(encryption["scheme"])
        assert isinstance(selected, dict), "missing selected scheme object"
        if encryption["scheme"] == "ocm-pgp":
            fingerprints = selected.get("fingerprints")
            assert (isinstance(fingerprints, list) and fingerprints and
                    all(isinstance(value, str) and value for value in fingerprints)), \
                "missing PGP fingerprints"


class ShareSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_spec()
        cls.draft = (ROOT / "IETF-OCM.md").read_text(encoding="utf-8")
        cls.http, cls.body, cls.share = share_request(cls.draft)
        properties = cls.spec["components"]["schemas"]["NewShare"]["properties"]
        cls.protocols = properties["protocol"]["example"]
        cls.encryption = properties["encryption"]["example"]

    def check(self, schema, value, expected=True):
        validator = Draft4Validator({
            "$ref": f"#/components/schemas/{schema}",
            "components": self.spec["components"],
        })
        errors = list(validator.iter_errors(value))
        self.assertEqual(not errors, expected, [error.message for error in errors])

    def full_contexts(self, protocol):
        ip = deepcopy(protocol)
        for entry in ip.values():
            if isinstance(entry, dict):
                entry.pop("sharedSecret", None)
        return (
            ("NewShare", {**self.share, "protocol": protocol}),
            ("IPShareProvisioningRequest", {**self.share, "protocol": ip}),
            ("OCMIPClaim", {"providerId": self.share["providerId"],
                            "resourceType": "file", "protocol": ip}),
        )

    def test_collection_metadata(self):
        cases = (
            ("absent", {}, True),
            ("id only", {"collectionId": "opaque @collection/id?#"}, True),
            ("empty id", {"collectionId": "", "collectionSize": 1}, True),
            ("minimum", {"collectionId": "opaque", "collectionSize": 1}, True),
            ("known size", {"collectionId": "opaque", "collectionSize": 3}, True),
            ("missing id", {"collectionSize": 1}, False),
            ("null id", {"collectionId": None, "collectionSize": 1}, False),
            ("wrong id", {"collectionId": 7, "collectionSize": 1}, False),
            ("zero", {"collectionId": "opaque", "collectionSize": 0}, False),
            ("fractional", {"collectionId": "opaque", "collectionSize": 1.5}, False),
            ("string", {"collectionId": "opaque", "collectionSize": "1"}, False),
            ("boolean", {"collectionId": "opaque", "collectionSize": True}, False),
            ("null size", {"collectionId": "opaque", "collectionSize": None}, False),
        )
        contexts = {"ShareFields": {}, **dict(self.full_contexts(self.share["protocol"]))}
        for schema in ("ShareFields", "NewShare", "IPShareProvisioningRequest"):
            base = {k: v for k, v in contexts[schema].items()
                    if k not in ("collectionId", "collectionSize")}
            for label, metadata, expected in cases:
                with self.subTest(schema=schema, metadata=label):
                    self.check(schema, {**base, **metadata}, expected)

    def test_share_resource_types(self):
        schemas = self.spec["components"]["schemas"]
        contexts = self.full_contexts(self.share["protocol"])
        mls = schemas["MLSEncryptedShare"]["example"]
        for resource, expected in (("file", True), ("folder", True),
                                    ("future-resource", True), ("Collection", True),
                                    ("collection", False), ("federation", False),
                                    ("Federation", True), (7, False), (None, False)):
            for schema, payload in (*contexts, ("MLSEncryptedShare", mls)):
                value = {**payload, "resourceType": resource}
                if schema == "OCMIPClaim":
                    value.update(owner={}, collectionSize=2)
                with self.subTest(schema=schema, resourceType=resource):
                    self.check(schema, value, expected)
            for schema in ("IPSelfContainedTokenClaims",
                           "IPActiveSelfContainedIntrospectionResponse"):
                value = deepcopy(schemas[schema]["example"])
                value["ocm_ip"].update(resourceType=resource, owner={}, collectionSize=2)
                with self.subTest(schema=schema, resourceType=resource):
                    self.check(schema, value, expected)
        for metadata, expected in (({"collectionSize": 2}, False),
                                    ({"collectionId": "opaque @id/?#",
                                      "collectionSize": 2}, True)):
            with self.subTest(schema="MLSEncryptedShare", metadata=metadata):
                self.check("MLSEncryptedShare", {**mls, **metadata}, expected)

    def test_discovery_resource_types(self):
        standalone = json.loads((ROOT / "schemas/ocm-discovery.json").read_text(
            encoding="utf-8"))
        dialect = validator_for(standalone)
        dialect.check_schema(standalone)
        validator = dialect(standalone)
        discovery = {"enabled": True, "apiVersion": "1.5.1",
                     "endPoint": "https://cloud.example.org/ocm",
                     "resourceTypes": [{"name": "file", "shareTypes": ["user"],
                                        "protocols": {"webdav": "/dav/"}}]}
        for name, expected in (("file", True), ("folder", True),
                                ("future-resource", True), ("Collection", True),
                                ("collection", False), ("federation", False),
                                ("Federation", True), (7, False), (None, False)):
            value = deepcopy(discovery)
            value["resourceTypes"][0]["name"] = name
            with self.subTest(schema="Discovery", dialect="Draft4", name=name):
                self.check("Discovery", value, expected)
            with self.subTest(schema="StandaloneDiscovery", dialect=dialect.__name__, name=name):
                self.assertEqual(validator.is_valid(value), expected)

    def test_webdav_optional_permissions(self):
        dav = deepcopy(self.share["protocol"]["webdav"])
        del dav["permissions"]
        for permissions, expected in ((None, True), ([], True),
                                      (["read", "write"], True), (["view"], False)):
            entry = {**dav, "requirements": []}
            if permissions is not None:
                entry["permissions"] = permissions
            for schema, payload in self.full_contexts({"name": "multi", "webdav": entry}):
                with self.subTest(schema=schema, permissions=permissions):
                    self.check(schema, payload, expected)

    def test_granular_protocol_permissions(self):
        for protocol in ("webdav", "webapp"):
            entry = deepcopy(self.protocols["multipleProtocols"][protocol])
            for permission in ("create", "update", "delete", "view", "admin"):
                entry["permissions"] = [permission]
                expected = permission != "admin" and (protocol == "webapp" or permission != "view")
                for schema, payload in self.full_contexts({"name": "multi", protocol: entry}):
                    with self.subTest(schema=schema, protocol=protocol, permission=permission):
                        self.check(schema, payload, expected)

    def test_community_recipients(self):
        for recipient in ("user", "group", "community", "federation"):
            for schema, payload in self.full_contexts(self.share["protocol"]):
                with self.subTest(schema=schema, recipient=recipient):
                    self.check(schema, {**payload, "shareType": recipient}, recipient != "federation")

    def test_ssh_full_and_partial(self):
        for entry, expected in (({}, False), ({"accessTypes": ["datatx"]}, False),
                                ({"uri": "alice@host.example:22/path"}, True)):
            for schema, payload in self.full_contexts({"name": "ssh", "ssh": entry}):
                with self.subTest(schema=schema, entry=entry):
                    self.check(schema, payload, expected)
        for schema in ("IPShareProvisioningResponse", "IPTokenPreparationResponse"):
            self.check(schema, {"protocol": {"ssh": {"accessTypes": ["datatx"]}}})

    def test_webapp_token_membership(self):
        app = self.protocols["multipleProtocols"]["webapp"]
        for requirements, expected in (
                (None, False), ([], False), (["must-use-mfa"], False),
                (["must-exchange-token"], True),
                (["must-exchange-token", "must-use-mfa"], True),
                (["must-use-mfa", "must-exchange-token"], True)):
            entry = {k: deepcopy(v) for k, v in app.items() if k != "requirements"}
            if requirements is not None:
                entry["requirements"] = requirements
            for schema, payload in self.full_contexts({"name": "multi", "webapp": entry}):
                with self.subTest(schema=schema, requirements=requirements):
                    self.check(schema, payload, expected)
            for schema in ("IPShareProvisioningResponse", "IPTokenPreparationResponse"):
                partial = {} if requirements is None else {"requirements": requirements}
                with self.subTest(schema=schema, requirements=requirements):
                    self.check(schema, {"protocol": {"webapp": partial}},
                               requirements is None or expected)
        for schema in ("IPShareProvisioningResponse", "IPTokenPreparationResponse"):
            self.check(schema, {"protocol": {"webapp": {"uri": app["uri"]}}})

    def test_encryption_map(self):
        self.check("NewShare", self.share)
        future = {"resourceId": "opaque/id", "scheme": "future-scheme",
                  "future-scheme": {"opaque": True}}
        for encryption in (self.encryption, future):
            self.check("NewShare", {**self.share, "encryption": encryption})
        for value in ("scalar", 7, None, []):
            with self.subTest(parameters=value):
                self.check("NewShare", {**self.share, "encryption": {
                    **future, "future-scheme": value}}, False)
        for field in ("resourceId", "scheme"):
            with self.subTest(missing=field):
                self.check("NewShare", {**self.share, "encryption": {
                    k: v for k, v in future.items() if k != field}}, False)

    def test_published_examples(self):
        encoded = self.body.encode("utf-8")
        self.assertEqual(int(re.search(r"Content-Length: (\d+)", self.http)[1]), len(encoded))
        digest = base64.b64encode(hashlib.sha256(encoded).digest()).decode()
        self.assertEqual(re.search(r"Content-Digest: sha-256=:(.*):", self.http)[1], digest)
        for protocol in (self.share["protocol"], *self.protocols.values()):
            with self.subTest(protocol=protocol):
                share = {**self.share, "protocol": protocol}
                self.check("NewShare", share)
                check_example_relations(share)
        share = {**self.share, "encryption": self.encryption}
        self.check("NewShare", share)
        check_example_relations(share)
        reordered = self.draft.replace(
            'type="http" anchor="core-share-request-example"',
            'anchor="core-share-request-example" type="http"')
        self.assertEqual(share_request(reordered), (self.http, self.body, self.share))
        for draft in (self.draft.replace('anchor="core-share-request-example"', ""),
                      self.draft + '\n<sourcecode anchor="core-share-request-example">\n' +
                      self.http + '\n</sourcecode>'):
            with self.assertRaisesRegex(ValueError, "exactly one"):
                share_request(draft)

    def test_example_relations(self):
        share = {**self.share, "protocol": deepcopy(self.protocols["multipleProtocols"]),
                 "encryption": deepcopy(self.encryption)}
        share["protocol"]["webapp"]["requirements"].reverse()
        self.check("NewShare", share)
        check_example_relations(share)
        duplicate = deepcopy(share)
        apps = duplicate["protocol"]["webapp"]["apps"]
        apps[1]["name"] = apps[0]["name"]
        mismatch = deepcopy(share)
        mismatch["protocol"]["webdav"]["requirements"] = ["must-exchange-token"]
        missing_scheme = deepcopy(share)
        del missing_scheme["encryption"]["ocm-pgp"]
        missing_fingerprints = deepcopy(share)
        missing_fingerprints["encryption"]["ocm-pgp"]["fingerprints"] = []
        for invalid, message in ((duplicate, "duplicate app name"),
                                 (mismatch, "requirements disagree"),
                                 (missing_scheme, "missing selected scheme object"),
                                 (missing_fingerprints, "missing PGP fingerprints")):
            with self.subTest(message=message):
                self.check("NewShare", invalid)
                with self.assertRaisesRegex(AssertionError, message):
                    check_example_relations(invalid)

    def test_mime_strings(self):
        for types, expected in ((["text/plain", "text/html"], True),
                                (["text/plain", "text/plain"], False), ([], False),
                                (["text/plain", "Text/Plain"], True)):
            with self.subTest(mediaTypes=types):
                app = deepcopy(self.protocols["multipleProtocols"]["webapp"])
                app["apps"] = [{"name": "Editor", "mediaTypes": types}]
                self.check("NewShare", {**self.share, "protocol": {
                    "name": "multi", "webapp": app}}, expected)


if __name__ == "__main__":
    unittest.main()
