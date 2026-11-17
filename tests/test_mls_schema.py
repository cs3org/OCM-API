"""Structural MLS payload checks derived from IETF-OCM-MLS.md."""

from copy import deepcopy
import json
import re
import shlex
import unittest

from jsonschema import Draft4Validator

from test_extension_schemas import ROOT, load_spec


EXAMPLE_SCHEMAS = {
    "mls-discovery-example": "Discovery",
    "mls-key-package-response-example": "KeyPackageResponse",
    "mls-server-key-package-response-example": "KeyPackageResponse",
    "mls-ratchet-tree-response-example": "RatchetTreeResponse",
    "mls-commits-response-example": "CommitsResponse",
    "mls-server-welcome-example": "MLSWelcomeNotification",
    "mls-welcome-example": "MLSWelcomeNotification",
    "mls-proposal-example": "MLSProposalNotification",
    "mls-commit-example": "MLSCommitNotification",
    "mls-application-example": "MLSApplicationNotification",
    "mls-rejoin-example": "MLSRejoinNotification",
    "mls-wrapped-keys-example": "MLSApplicationData",
    "mls-credentials-example": "MLSApplicationData",
    "mls-encrypted-share-example": "MLSEncryptedShare",
}


def draft_examples(draft=None):
    if draft is None:
        draft = (ROOT / "IETF-OCM-MLS.md").read_text(encoding="utf-8")
    examples = {}
    pattern = r'^~~~ json\n(.*?)\n~~~(?:\n\{:([^\n]*)\})?'
    for match in re.finditer(pattern, draft, re.M | re.S):
        for attr in shlex.split(match[2] or "", comments=False):
            ident = attr.removeprefix("#")
            if not attr.startswith("#") or ident not in EXAMPLE_SCHEMAS:
                continue
            if ident in examples:
                raise ValueError(f"duplicate example ID: {ident}")
            examples[ident] = json.loads(match[1])
    missing = EXAMPLE_SCHEMAS.keys() - examples.keys()
    if missing:
        raise ValueError("missing example IDs: " + ", ".join(sorted(missing)))
    return examples


def boundary_cases():
    examples = draft_examples()
    cases = []

    def add(group, schema, value, expected=True, label=""):
        cases.append({"group": group, "schema": schema,
                      "instance": deepcopy(value), "expected": expected,
                      "label": label})

    for kind, fields in (
            ("welcome", {"userId": 7, "content": {}}),
            ("proposal", {"content": {}}),
            ("commit", {"content": {}}),
            ("application", {"content": {"keys": []}}),
            ("rejoin", {"keyPackages": {}})):
        event = examples[f"mls-{kind}-example"]
        add("envelopes", "MLSNotification", event, label=kind)
        add("envelopes", "NewNotification", event, label=f"core {kind}")
        for field, wrong in {"mlsGroupId": 7, **fields}.items():
            for label, replace in (("missing", False), ("wrong type", True)):
                invalid = deepcopy(event)
                federation = invalid["notification"]["community"]
                if replace:
                    federation[field] = wrong
                else:
                    del federation[field]
                add("envelopes", "MLSNotification", invalid, False,
                    f"{kind}: {label} {field}")

    proposal = examples["mls-proposal-example"]
    for field, wrong in (("notificationType", 7), ("senderDomain", 7),
                         ("shareType", "user"), ("notification", [])):
        for label, replace in (("missing", False), ("wrong value", True)):
            invalid = deepcopy(proposal)
            if replace:
                invalid[field] = wrong
            else:
                del invalid[field]
            add("envelopes", "MLSNotification", invalid, False, f"{label} {field}")
    for notification in ({}, {"federation": None}, {"federation": []}):
        add("envelopes", "MLSNotification", {**proposal, "notification": notification},
            False, f"invalid federation: {notification}")
    for field, value in (("resourceType", "file"), ("providerId", "grant/id"),
                         ("resourceType", None), ("providerId", None)):
        add("envelopes", "MLSNotification", {**proposal, field: value}, False,
            f"forbidden top-level {field}={value!r}")
    extended = deepcopy(proposal)
    extended["future"] = 1
    extended["notification"]["community"].update(mlsGroupId="", content="", future=True)
    add("envelopes", "MLSNotification", extended, label="open extensions and opaque strings")
    welcome = deepcopy(examples["mls-welcome-example"])
    welcome["notification"]["community"]["userId"] = "bob@elsewhere.example:8443"
    add("envelopes", "MLSNotification", welcome, label="Welcome user has another home server")

    malformed = deepcopy(proposal)
    del malformed["notification"]["community"]["content"]
    future = {**proposal, "notificationType": "MLS_FUTURE"}
    for label, value in (("known Proposal without content", malformed),
                         ("future MLS type", future)):
        add("boundary", "MLSNotification", value, False, label)
        add("boundary", "NewNotification", value, label=f"core accepts {label}")
    resource = {"notificationType": "SHARE_UNSHARED", "shareType": "community",
                "senderDomain": "cloud.example.org", "resourceType": "file",
                "notification": {"file": {"providerId": "opaque grant/id"}}}
    add("boundary", "NewNotification", resource, label="community resource event")
    add("boundary", "MLSNotification", resource, False, "resource event is not lifecycle")
    del resource["notification"]["file"]["providerId"]
    add("boundary", "NewNotification", resource, False, "resource event still needs grant ID")

    commit = deepcopy(examples["mls-commit-example"])
    for label, proposals in (("empty", []), ("wrong item", [7]), ("wrong type", {})):
        commit["notification"]["community"]["proposals"] = proposals
        add("entries", "MLSCommitNotification", commit, label == "empty", f"proposals {label}")
    del commit["notification"]["community"]["proposals"]
    add("entries", "MLSCommitNotification", commit, label="proposals absent")
    rejoin = examples["mls-rejoin-example"]
    entry = rejoin["notification"]["community"]["keyPackages"][0]
    for field, wrong in (("userId", 7), ("mediaType", "text/plain"),
                         ("encoding", "base64"), ("content", {})):
        for label, replace in (("missing", False), ("wrong value", True)):
            invalid = deepcopy(rejoin)
            key_package = invalid["notification"]["community"]["keyPackages"][0]
            if replace:
                key_package[field] = wrong
            else:
                del key_package[field]
            add("entries", "MLSRejoinNotification", invalid, False, f"{label} {field}")
    for packages in ([], [{**entry, "content": "", "extension": True}]):
        empty = deepcopy(rejoin)
        empty["notification"]["community"]["keyPackages"] = packages
        add("entries", "MLSRejoinNotification", empty, label=f"unbounded package array: {packages}")

    for kind in ("welcome", "proposal", "commit", "application", "rejoin"):
        event = deepcopy(examples[f"mls-{kind}-example"])
        del event["shareType"]
        event["resourceType"] = "federation"
        group = event["notification"].pop("community")
        group["federationId"] = "sciencemesh"
        if kind == "welcome":
            del group["userId"]
            group["serverUrl"] = "https://receiver.example.org:8443"
        if kind == "rejoin":
            for item in group["keyPackages"]:
                del item["userId"]
                item["serverUrl"] = "https://receiver.example.org:8443"
        event["notification"]["federation"] = group
        add("servers", "MLSNotification", event, label=kind)
        add("servers", "NewNotification", event, label=f"core {kind}")
        for field in ("federationId", "mlsGroupId",
                      "keyPackages" if kind == "rejoin" else "content",
                      *(("serverUrl",) if kind == "welcome" else ())):
            invalid = deepcopy(event)
            del invalid["notification"]["federation"][field]
            add("servers", "MLSNotification", invalid, False, f"{kind}: missing {field}")
            invalid = deepcopy(event)
            invalid["notification"]["federation"][field] = 7
            add("servers", "MLSNotification", invalid, False, f"{kind}: wrong {field}")
        for field, value in (("shareType", "community"), ("resourceType", "file")):
            add("servers", "MLSNotification", {**event, field: value}, False,
                f"{kind}: wrong scope {field}")
        invalid = deepcopy(event)
        invalid["notification"]["community"] = deepcopy(group)
        add("servers", "MLSNotification", invalid, False, f"{kind}: both group objects")
        invalid = deepcopy(event)
        invalid["notification"]["federation"]["userId"] = "bob@receiver.example.org"
        add("servers", "MLSNotification", invalid, False, f"{kind}: person in server body")
        if kind in ("welcome", "rejoin"):
            invalid = deepcopy(event)
            target = invalid["notification"]["federation"]
            if kind == "rejoin":
                target = target["keyPackages"][0]
            del target["serverUrl"]
            target["userId"] = "bob@receiver.example.org"
            add("servers", "MLSNotification", invalid, False, f"{kind}: wrong selector")
    for kind in ("welcome", "proposal", "commit", "application", "rejoin"):
        invalid = deepcopy(examples[f"mls-{kind}-example"])
        invalid["notification"]["community"]["serverUrl"] = "https://receiver.example.org"
        add("servers", "MLSNotification", invalid, False, f"{kind}: server in person body")
    rejoin = deepcopy(examples["mls-rejoin-example"])
    entry = rejoin["notification"]["community"]["keyPackages"][0]
    del entry["userId"]
    entry["serverUrl"] = "https://receiver.example.org"
    add("servers", "MLSNotification", rejoin, False, "server in person rejoin list")

    for ident in ("mls-key-package-response-example", "mls-server-key-package-response-example"):
        response = examples[ident]
        selector = "serverId" if "serverId" in response else "userId"
        other = "userId" if selector == "serverId" else "serverId"
        add("retrieval", "KeyPackageResponse", response, label=selector)
        add("retrieval", "KeyPackageResponse", {k:v for k,v in response.items() if k != selector}, False,
            "no selector")
        add("retrieval", "KeyPackageResponse", {**response, other: "opaque"}, False, "both selectors")
        add("retrieval", "KeyPackageResponse", {**response, selector: 7}, False, "non-string selector")
    for ident, schema, fields in (
            ("mls-ratchet-tree-response-example", "RatchetTreeResponse", ("epoch", "ratchetTree")),
            ("mls-commits-response-example", "CommitsResponse", ("commits",))):
        response = examples[ident]
        add("retrieval", schema, response, label=schema)
        for field in ("mlsGroupId", *fields):
            invalid = {k:v for k,v in response.items() if k != field}
            add("retrieval", schema, invalid, False, f"{schema}: missing {field}")
        invalid = deepcopy(response)
        if schema == "RatchetTreeResponse":
            invalid["epoch"] = -1
        else:
            invalid["commits"][0]["proposals"] = [7]
        add("retrieval", schema, invalid, False, f"{schema}: invalid entry")

    keys = examples["mls-wrapped-keys-example"]
    credentials = examples["mls-credentials-example"]
    add("private", "MLSApplicationData", {**keys, **credentials}, label="combined for one server")
    for field, value, required_fields in (
            ("keys", keys["keys"][0], ("resourceId", "groupId", "wrappedKey")),
            ("credentials", credentials["credentials"][0],
             ("providerId", "groupId", "recipient", "sharedSecret"))):
        add("private", "MLSApplicationData", {field: []}, label=f"empty {field}")
        add("private", "MLSApplicationData", {field: {}}, False, f"non-array {field}")
        add("private", "MLSApplicationData", {field: [7]}, False, f"non-object {field} entry")
        for required in required_fields:
            for label, replace in (("missing", False), ("wrong type", True)):
                invalid = dict(value)
                if replace:
                    invalid[required] = 7
                else:
                    del invalid[required]
                add("private", "MLSApplicationData", {field: [invalid]}, False,
                    f"{field}: {label} {required}")
    add("private", "MLSApplicationData", {}, False, "no application arrays")
    for recipient in ("cloud.example.org:8443", "192.0.2.7:8443", "[2001:db8::7]:8443"):
        entry = {**credentials["credentials"][0], "recipient": recipient,
                 "providerId": "opaque grant/id", "extension": True}
        add("private", "MLSApplicationData", {"credentials": [entry]}, label=f"recipient {recipient}")
    key = {**keys["keys"][0], "resourceId": "opaque resource/id", "wrappedKey": ""}
    add("private", "MLSApplicationData", {"keys": [key], "extension": 7}, label="opaque IDs and extensions")

    share = examples["mls-encrypted-share-example"]
    encryption = share["encryption"]
    for cipher in ("AES-128-GCM", "AES-256-GCM", "CHACHA20-POLY1305"):
        add("encryption", "MLSEncryption", {**encryption, "ocm-mls": {"cipher": cipher}}, label=cipher)
    add("encryption", "MLSEncryption", {**encryption, "scheme": "custom"}, False,
        "wrong scheme with MLS parameters")
    for field in ("resourceId", "scheme", "ocm-mls"):
        invalid = {k: v for k, v in encryption.items() if k != field}
        add("encryption", "MLSEncryption", invalid, False, f"missing {field}")
    for selected, label in (({}, "missing cipher"), ({"cipher": "unknown"}, "unknown cipher"),
                            ({"cipher": 7}, "non-string cipher"), ([], "non-object mechanism")):
        add("encryption", "MLSEncryption", {**encryption, "ocm-mls": selected}, False, label)
    add("encryption", "MLSEncryption", {**encryption, "resourceId": "opaque resource/id",
        "future": {"parameter": True}}, label="opaque ID and extra mechanism")
    for label, value in (("unencrypted", {k: v for k, v in share.items() if k != "encryption"}),
                         ("other scheme", {**share, "encryption": {"resourceId": "resource/id",
                           "scheme": "custom", "custom": {"opaque": True}}})):
        add("encryption", "NewShare", value, label=f"core {label}")
        add("encryption", "MLSEncryptedShare", value, False, label)
    add("encryption", "MLSEncryptedShare", {**share, "shareType": "user"}, False, "non-community share")
    return cases


class MLSSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_spec()

    def check(self, schema, value, expected=True):
        self.assertIn(schema, self.spec["components"]["schemas"])
        validator = Draft4Validator({"$ref": f"#/components/schemas/{schema}",
                                     "components": self.spec["components"]})
        self.assertEqual(validator.is_valid(value), expected)

    def check_group(self, group):
        for case in boundary_cases():
            if case["group"] == group:
                with self.subTest(schema=case["schema"], label=case["label"]):
                    self.check(case["schema"], case["instance"], case["expected"])

    def test_source_examples(self):
        draft = (ROOT / "IETF-OCM-MLS.md").read_text(encoding="utf-8")
        examples = draft_examples(draft)
        for ident, schema in EXAMPLE_SCHEMAS.items():
            with self.subTest(example=ident):
                self.check(schema, examples[ident])
        discovery = examples["mls-discovery-example"]
        self.assertIn("http-sig", discovery["capabilities"])
        self.assertIn("notifications", discovery["capabilities"])
        self.assertEqual(discovery["jwksUri"], discovery["endPoint"] + "/jwks")
        self.assertIn("community", discovery["resourceTypes"][0]["shareTypes"])

    def test_example_ownership_ignores_order_and_unrelated_blocks(self):
        draft = (ROOT / "IETF-OCM-MLS.md").read_text(encoding="utf-8")
        expected = draft_examples(draft)
        reordered = '~~~ json\n{"unrelated": true}\n~~~\n' + "\n".join(
            f'~~~ json\n{json.dumps(value)}\n~~~\n{{: title="See #other {{content}} example" #{ident}}}\n'
            for ident, value in reversed(list(expected.items())))
        self.assertEqual(draft_examples(reordered), expected)

    def test_example_ownership_reports_missing_and_duplicate_ids(self):
        draft = (ROOT / "IETF-OCM-MLS.md").read_text(encoding="utf-8")
        ident = "mls-proposal-example"
        with self.assertRaisesRegex(ValueError, "missing example IDs: " + ident):
            draft_examples(draft.replace(f"#{ident}", "#unrelated", 1))
        duplicate = f'\n~~~ json\n{{}}\n~~~\n{{: #{ident}}}\n'
        with self.assertRaisesRegex(ValueError, "duplicate example ID: " + ident):
            draft_examples(draft + duplicate)

    def test_known_envelopes(self):
        self.check_group("envelopes")

    def test_strict_profile_and_core_extensibility(self):
        self.check_group("boundary")

    def test_commit_and_rejoin_entries(self):
        self.check_group("entries")

    def test_server_group_envelopes(self):
        self.check_group("servers")

    def test_retrieval_responses(self):
        self.check_group("retrieval")
        paths = self.spec["paths"]
        self.assertNotIn("/mls-key-packages", paths)
        key_packages = paths["/mls/key-packages"]["get"]
        parameters = {p["name"]: p for p in key_packages["parameters"]}
        self.assertEqual(set(parameters), {"userId", "serverId", "senderDomain"})
        self.assertTrue(parameters["senderDomain"]["required"])
        self.assertFalse(parameters["userId"]["required"])
        self.assertFalse(parameters["serverId"]["required"])
        self.assertIn("exactly one of userId and serverId", key_packages["description"])
        for path, selector in (("/mls/ratchet-tree", "epoch"), ("/mls/commits", "from")):
            operation = paths[path]["get"]
            params = {p["name"]:p for p in operation["parameters"]}
            self.assertTrue(params[selector]["required"])
            self.assertIn("404", operation["responses"])
            for header in ("Content-Digest", "Signature-Input", "Signature"):
                self.assertTrue(operation["responses"]["200"]["headers"][header]["required"])

    def test_private_application_data(self):
        self.check_group("private")

    def test_selected_encryption(self):
        self.check_group("encryption")

    def test_catalogue_examples_and_shared_contracts(self):
        schemas = self.spec["components"]["schemas"]
        self.assertIn("MLSNotification", schemas)
        body = self.spec["paths"]["/notifications"]["post"]["requestBody"]
        media = body["content"]["application/json"]
        self.assertEqual(media["schema"], {"$ref": "#/components/schemas/NewNotification"})
        operation_names = {"mlsWelcome", "mlsProposal", "mlsCommit", "mlsApplication", "mlsRejoin"}
        self.assertEqual({name for name in media["examples"] if name.startswith("mls")},
                         operation_names)
        for name in sorted(operation_names):
            with self.subTest(operation_example=name):
                self.check("MLSNotification", media["examples"][name]["value"])
        for name in ("MLSApplicationData", "MLSEncryptedShare"):
            with self.subTest(component_example=name):
                self.check(name, schemas[name]["example"])


if __name__ == "__main__":
    unittest.main()
