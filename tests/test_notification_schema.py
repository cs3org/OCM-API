"""Regression checks for the notification shapes defined in IETF-OCM.md."""

from copy import deepcopy
from pathlib import Path
import unittest

from jsonschema import Draft4Validator
import yaml


SHARE_EVENTS = (
    "SHARE_ACCEPTED", "SHARE_DECLINED", "SHARE_UNSHARED",
    "SHARE_CHANGE_PERMISSION",
)


def envelope(event, **fields):
    return {"notificationType": event, "senderDomain": "sender.example.org", **fields}


# Fixtures follow Share Acceptance and Updating, Resharing, and Recipient Removal.
PAYLOADS = {
    event: envelope(event, resourceType="file",
                    notification={"file": {"providerId": "share-123"}})
    for event in SHARE_EVENTS
}
PAYLOADS.update({
    "REQUEST_RESHARE": envelope(
        "REQUEST_RESHARE", resourceType="file",
        notification={"file": {"providerId": "share-123",
                               "shareWith": "bob@receiver.example.org"}}),
    "REQUEST_SHARE": envelope(
        "REQUEST_SHARE", resourceType="file",
        notification={"file": {"owner": "alice@sender.example.org",
                               "shareWith": "bob@receiver.example.org",
                               "shareId": "resource-456", "permissions": ["read"]}}),
    "USER_REMOVED": envelope(
        "USER_REMOVED", shareType="user",
        notification={"user": {"userId": "alice@sender.example.org"}}),
    "GROUP_REMOVED": envelope(
        "GROUP_REMOVED", shareType="group",
        notification={"group": {"groupId": "team-789"}}),
    "CONTACT_REMOVED": envelope(
        "CONTACT_REMOVED", shareType="user",
        notification={"user": {"userId": "alice@sender.example.org",
                               "targetUserId": "bob@receiver.example.org"}}),
})


class NotificationSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec_path = Path(__file__).resolve().parents[1] / "spec.yaml"
        cls.spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        # Keep local OpenAPI references available to the Draft4 validator.
        cls.validator = Draft4Validator({
            "$ref": "#/components/schemas/NewNotification",
            "components": cls.spec["components"],
        })

    def test_builtin_payloads(self):
        for event, payload in PAYLOADS.items():
            with self.subTest(event=event):
                self.validator.validate(payload)
                missing = deepcopy(payload)
                del missing["notification"]
                self.assertFalse(self.validator.is_valid(missing))
                empty = deepcopy(payload)
                empty["notification"] = {}
                self.assertFalse(self.validator.is_valid(empty))
        contact = deepcopy(PAYLOADS["CONTACT_REMOVED"])
        del contact["notification"]["user"]["targetUserId"]
        self.assertFalse(self.validator.is_valid(contact))

    def test_forbidden_fields_and_share_types(self):
        for event in ("USER_REMOVED", "GROUP_REMOVED", "CONTACT_REMOVED"):
            wrong_share_type = "user" if event == "GROUP_REMOVED" else "group"
            for field, value in (("resourceType", "file"),
                                 ("shareType", wrong_share_type)):
                with self.subTest(event=event, field=field):
                    invalid = deepcopy(PAYLOADS[event])
                    invalid[field] = value
                    self.assertFalse(self.validator.is_valid(invalid))
        request = deepcopy(PAYLOADS["REQUEST_SHARE"])
        request["shareType"] = "user"
        self.assertFalse(self.validator.is_valid(request))
        removed = deepcopy(PAYLOADS["USER_REMOVED"])
        removed["notification"]["user"]["targetUserId"] = "bob@receiver.example.org"
        self.assertFalse(self.validator.is_valid(removed))

    def test_deprecated_id_cannot_replace_nested_share_id(self):
        for event in SHARE_EVENTS:
            with self.subTest(event=event):
                payload = deepcopy(PAYLOADS[event])
                payload["providerId"] = payload["notification"]["file"].pop("providerId")
                self.assertFalse(self.validator.is_valid(payload))

    def test_unknown_type(self):
        self.validator.validate(envelope("EXAMPLE_CUSTOM_EVENT", resourceType="file"))

    def test_fallback_excludes_exactly_the_builtin_types(self):
        schemas = self.spec["components"]["schemas"]
        branches = schemas["NewNotification"]["allOf"][1]["anyOf"]
        builtin_types = set()
        for branch in branches:
            name = branch["$ref"].rsplit("/", 1)[1]
            if name != "NotificationOfOtherType":
                builtin_types.update(schemas[name]["properties"]["notificationType"]["enum"])
        fallback_type = schemas["NotificationOfOtherType"]["properties"]["notificationType"]
        exclusions = fallback_type["not"]["enum"]
        self.assertEqual(set(exclusions), builtin_types)
        self.assertEqual(set(PAYLOADS), builtin_types)

    def test_published_operation_examples(self):
        operation = self.spec["paths"]["/notifications"]["post"]
        examples = operation["requestBody"]["content"]["application/json"]["examples"]
        self.assertTrue(examples)
        for name, example in examples.items():
            with self.subTest(example=name):
                self.validator.validate(example["value"])


if __name__ == "__main__":
    unittest.main()
