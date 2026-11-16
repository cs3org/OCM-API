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
                federation = invalid["notification"]["federation"]
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
    extended["notification"]["federation"].update(mlsGroupId="", content="", future=True)
    add("envelopes", "MLSNotification", extended, label="open extensions and opaque strings")
    welcome = deepcopy(examples["mls-welcome-example"])
    welcome["notification"]["federation"]["userId"] = "bob@elsewhere.example:8443"
    add("envelopes", "MLSNotification", welcome, label="Welcome user has another home server")

    malformed = deepcopy(proposal)
    del malformed["notification"]["federation"]["content"]
    future = {**proposal, "notificationType": "MLS_FUTURE"}
    for label, value in (("known Proposal without content", malformed),
                         ("future MLS type", future)):
        add("boundary", "MLSNotification", value, False, label)
        add("boundary", "NewNotification", value, label=f"core accepts {label}")
    resource = {"notificationType": "SHARE_UNSHARED", "shareType": "federation",
                "senderDomain": "cloud.example.org", "resourceType": "file",
                "notification": {"file": {"providerId": "opaque grant/id"}}}
    add("boundary", "NewNotification", resource, label="federation resource event")
    add("boundary", "MLSNotification", resource, False, "resource event is not lifecycle")
    del resource["notification"]["file"]["providerId"]
    add("boundary", "NewNotification", resource, False, "resource event still needs grant ID")

    commit = deepcopy(examples["mls-commit-example"])
    for label, proposals in (("empty", []), ("wrong item", [7]), ("wrong type", {})):
        commit["notification"]["federation"]["proposals"] = proposals
        add("entries", "MLSCommitNotification", commit, label == "empty", f"proposals {label}")
    del commit["notification"]["federation"]["proposals"]
    add("entries", "MLSCommitNotification", commit, label="proposals absent")
    rejoin = examples["mls-rejoin-example"]
    entry = rejoin["notification"]["federation"]["keyPackages"][0]
    for field, wrong in (("userId", 7), ("mediaType", "text/plain"),
                         ("encoding", "base64"), ("content", {})):
        for label, replace in (("missing", False), ("wrong value", True)):
            invalid = deepcopy(rejoin)
            key_package = invalid["notification"]["federation"]["keyPackages"][0]
            if replace:
                key_package[field] = wrong
            else:
                del key_package[field]
            add("entries", "MLSRejoinNotification", invalid, False, f"{label} {field}")
    for packages in ([], [{**entry, "content": "", "extension": True}]):
        empty = deepcopy(rejoin)
        empty["notification"]["federation"]["keyPackages"] = packages
        add("entries", "MLSRejoinNotification", empty, label=f"unbounded package array: {packages}")

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
    add("encryption", "MLSEncryptedShare", {**share, "shareType": "user"}, False, "non-federation share")
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
        self.assertIn("federation", discovery["resourceTypes"][0]["shareTypes"])

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
        for name in ("MLSNotification", "MLSApplicationData", "MLSEncryption", "MLSEncryptedShare"):
            self.assertEqual(schemas[name]["x-tags"], ["MLS"])
        for name in ("MLSApplicationData", "MLSEncryptedShare"):
            with self.subTest(component_example=name):
                self.check(name, schemas[name]["example"])


if __name__ == "__main__":
    unittest.main()
