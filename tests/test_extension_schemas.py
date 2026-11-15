"""Structural IP payload checks derived from IETF-OCM-IP.md."""

from copy import deepcopy
import base64
import hashlib
import json
from pathlib import Path
import re
import unittest

from jsonschema import Draft4Validator
import yaml


ROOT = Path(__file__).resolve().parents[1]


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate YAML key: {key}", key_node.start_mark)
        result[key] = loader.construct_object(value_node)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def load_spec(path=ROOT / "spec.yaml"):
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)


def draft_examples():
    draft = (ROOT / "IETF-OCM-IP.md").read_text(encoding="utf-8")
    http = re.search(
        r'<sourcecode type="http">(.*?)\n</sourcecode>', draft, re.S).group(1)
    body = http.split("\n\n", 1)[1]
    header, provisioned, contained = (
        json.loads(block) for block in re.findall(
            r"~~~ json\n(.*?)\n~~~", draft, re.S))
    revoke = re.search(
        r"POST /services/ocm/revoke.*?\n\n(\{.*?\})\n~~~", draft, re.S)
    active = re.search(
        r"HTTP/1.1 200 OK\nContent-Type: application/json\n\n"
        r"(\{\n.*?\})\n~~~", draft, re.S)
    return http, body, {
        "IPShareProvisioningRequest": json.loads(body),
        "IPShareProvisioningResponse": {"status": "stored"},
        "IPShareRevocationRequest": json.loads(revoke.group(1)),
        "IPShareRevocationResponse": {"status": "revoked"},
        "IPAccessTokenHeader": header,
        "IPProvisionedTokenClaims": provisioned,
        "IPSelfContainedTokenClaims": contained,
        "IPIntrospectionResponse": json.loads(active.group(1)),
    }


def boundary_cases():
    _, _, examples = draft_examples()
    request = examples["IPShareProvisioningRequest"]
    claim = examples["IPSelfContainedTokenClaims"]["ocm_ip"]
    cases = []

    def add(group, schema, value, expected=True, label=""):
        cases.append({"group": group, "schema": schema,
                      "instance": deepcopy(value), "expected": expected,
                      "label": label or f"case-{len(cases)}"})

    def missing(group, schema, value, fields):
        for field in fields:
            invalid = deepcopy(value)
            del invalid[field]
            add(group, schema, invalid, False, f"missing {field}")

    for schema, value in examples.items():
        add("examples", schema, value, label=schema)
    add("examples", "IPIntrospectionRequest", {"token": "shr-9wq4xkz7vmd2"})
    add("requests", "IPShareProvisioningRequest",
        {k: v for k, v in request.items() if k != "name"})
    add("requests", "IPShareProvisioningRequest", {**request, "extension": 1})
    missing("requests", "IPShareProvisioningRequest", request,
            ("sender", "owner", "shareWith", "providerId", "shareType",
             "resourceType", "protocol"))
    missing("requests", "IPShareRevocationRequest",
            examples["IPShareRevocationRequest"], ("sender", "providerId"))
    add("requests", "IPShareRevocationRequest", {"sender": 3, "providerId": "x"}, False)
    add("requests", "IPIntrospectionRequest", {}, False)
    add("requests", "IPIntrospectionRequest", {"token": 3}, False)
    missing("requests", "OCMIPClaim", claim,
            ("protocol", "providerId", "resourceType"))
    for protocol in ({}, {"name": 3}, {"name": "multi", "webdav": {}},
                     {"name": "multi", "webapp": {}},
                     {"name": "multi", "webdav": {"uri": "x", "permissions": ["view"]}},
                     {"name": "multi", "ssh": {"accessTypes": ["invalid"]}},
                     {"name": "multi", "custom": "invalid"}):
        add("requests", "IPShareProvisioningRequest",
            {**request, "protocol": protocol}, False)
    webapp = request["protocol"]["webapp"]
    for field in ("uri", "targets", "permissions", "requirements"):
        invalid = {k: v for k, v in webapp.items() if k != field}
        add("requests", "IPShareProtocol", {"name": "multi", "webapp": invalid}, False)
    for change in ({"targets": []}, {"permissions": []}, {"requirements": []},
                   {"apps": [{"name": "Editor"}]},
                   {"apps": [{"mediaTypes": ["text/plain"]}]}):
        add("requests", "IPShareProtocol",
            {"name": "multi", "webapp": {**webapp, **change}}, False)
    add("requests", "IPShareProtocol",
        {"name": "multi", "webapp": {**webapp, "permissions": ["view"]}})
    add("requests", "IPShareProtocol", {"name": "ssh", "ssh": {}})
    add("requests", "IPShareProtocol", {"name": "custom", "custom": {"opaque": 7}})

    for entry in ("webdav", "webapp", "options", "custom"):
        for secret in ("secret", None):
            protocol = deepcopy(request["protocol"])
            protocol.setdefault(entry, {})["sharedSecret"] = secret
            for schema, payload in (
                    ("IPShareProvisioningRequest", {**request, "protocol": protocol}),
                    ("OCMIPClaim", {**claim, "protocol": protocol}),
                    ("IPShareProvisioningResponse", {"protocol": protocol})):
                add("secrets", schema, payload, False,
                    f"{entry} secret {secret!r} in {schema}")
    secret_claim = deepcopy(claim)
    secret_claim["protocol"]["webdav"]["sharedSecret"] = "secret"
    for schema in ("IPSelfContainedTokenClaims", "IPIntrospectionResponse"):
        add("secrets", schema, {**examples[schema], "ocm_ip": secret_claim}, False,
            f"credential rejection through {schema}")

    for payload in ({}, {"status": "arbitrary"}, {"protocol": {}},
                    {"protocol": {"webdav": {"uri": "allocated"}}},
                    {"protocol": {"webapp": {"uri": "https://apps.example.org/open"}}},
                    {"protocol": {"custom": {"allocation": 1}}},
                    {"protocol": {"options": {"opaque": True}}},
                    {"protocol": {"webdav": {"permissions": ["write"]}}}):
        add("responses", "IPShareProvisioningResponse", payload)
    add("responses", "IPShareProvisioningResponse", {"status": 3}, False)
    add("responses", "IPShareProvisioningResponse", {"protocol": {"name": 3}}, False)
    for payload in ({}, {"status": "already-gone"}):
        add("responses", "IPShareRevocationResponse", payload)
    for entry in ("webdav", "webapp", "options", "custom"):
        add("responses", "IPTokenPreparationResponse",
            {"protocol": {entry: {"sharedSecret": "minted"}}})

    header = examples["IPAccessTokenHeader"]
    missing("tokens", "IPAccessTokenHeader", header, ("typ", "kid", "alg"))
    for change in ({"typ": "JWT"}, {"alg": "none"}, {"alg": 3}):
        add("tokens", "IPAccessTokenHeader", {**header, **change}, False)
    add("tokens", "IPAccessTokenHeader", {**header, "alg": "future-algorithm"})
    for schema in ("IPProvisionedTokenClaims", "IPSelfContainedTokenClaims"):
        claims = examples[schema]
        missing("tokens", schema, claims,
                ("iss", "sub", "aud", "iat", "exp", "jti", "client_id"))
        for change in ({"iat": 1.5}, {"exp": "1781190060"}, {"sub": 3}):
            add("tokens", schema, {**claims, **change}, False)
        add("tokens", schema, {**claims, "sub": "opaque local/id",
                               "client_id": "opaque provider/id", "iat": -1,
                               "exp": 0, "extension": {"future": True}})
    add("tokens", "IPProvisionedTokenClaims",
        {**examples["IPProvisionedTokenClaims"], "ocm_ip": claim}, False)
    add("tokens", "IPProvisionedTokenClaims",
        {**examples["IPProvisionedTokenClaims"], "ocm_ip": None}, False)
    missing("tokens", "IPSelfContainedTokenClaims",
            examples["IPSelfContainedTokenClaims"], ("ocm_ip",))

    active = examples["IPIntrospectionResponse"]
    provisioned_active = {k: v for k, v in active.items() if k != "ocm_ip"}
    provisioned_active["client_id"] = "opaque provider/id"
    for payload in (active, provisioned_active):
        add("introspection", "IPIntrospectionResponse", payload)
        add("introspection", "IPIntrospectionResponse", {**payload, "future": 7})
        missing("introspection", "IPIntrospectionResponse", payload,
                ("active", "iss", "sub", "aud", "exp"))
        for flag in (False, "true", 1, None):
            add("introspection", "IPIntrospectionResponse", {**payload, "active": flag}, False)
    add("introspection", "IPIntrospectionResponse", {"active": False})
    for field in ("iss", "sub", "aud", "exp", "client_id", "ocm_ip", "future"):
        add("introspection", "IPIntrospectionResponse",
            {"active": False, field: active.get(field, "leak")}, False)
    add("introspection", "IPIntrospectionResponse",
        {**active, "client_id": "both modes"}, False)
    add("introspection", "IPIntrospectionResponse",
        {k: v for k, v in active.items() if k != "ocm_ip"}, False)
    add("introspection", "IPIntrospectionResponse", {**active, "exp": 1.5}, False)
    return cases


class ExtensionSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_spec()
        cls.cases = boundary_cases()

    def check_group(self, group):
        for case in self.cases:
            if case["group"] != group:
                continue
            with self.subTest(schema=case["schema"], label=case["label"]):
                validator = Draft4Validator({
                    "$ref": f"#/components/schemas/{case['schema']}",
                    "components": self.spec["components"],
                })
                self.assertEqual(validator.is_valid(case["instance"]), case["expected"])

    def test_draft_examples(self):
        self.check_group("examples")

    def test_request_boundaries(self):
        self.check_group("requests")

    def test_no_protocol_credentials(self):
        self.check_group("secrets")

    def test_partial_and_delegated_responses(self):
        self.check_group("responses")

    def test_token_modes(self):
        self.check_group("tokens")

    def test_introspection_modes(self):
        self.check_group("introspection")

    def test_catalogue_examples(self):
        for name, schema in self.spec["components"]["schemas"].items():
            if name.startswith("IP") and "example" in schema:
                with self.subTest(schema=name):
                    Draft4Validator({
                        "$ref": f"#/components/schemas/{name}",
                        "components": self.spec["components"],
                    }).validate(schema["example"])

    def test_provisioning_body_headers(self):
        http, body, _ = draft_examples()
        encoded = body.encode("utf-8")
        length = int(re.search(r"Content-Length: (\d+)", http).group(1))
        digest = re.search(r"Content-Digest: sha-256=:(.*):", http).group(1)
        self.assertEqual(length, len(encoded))
        self.assertEqual(digest, base64.b64encode(hashlib.sha256(encoded).digest()).decode())

    def test_duplicate_yaml_keys(self):
        with self.assertRaisesRegex(yaml.constructor.ConstructorError, "duplicate YAML key"):
            yaml.load("schemas:\n  duplicate: {}\n  duplicate: {}\n", Loader=UniqueKeyLoader)


if __name__ == "__main__":
    unittest.main()
