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
        "REQUEST_SHARE", resourceType="collection", shareType="user",
        senderDomain="alice.example.org", collectionId="research-data-123",
        notification={"collection": {"owner": "bob@bob.example.org",
                                     "shareWith": "alice@alice.example.org",
                                     "permissions": ["read"]}}),
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

SERVER_EVENTS = ("OCM_SERVER_ADDED", "OCM_SERVER_REMOVED")
PAYLOADS.update({
    event: envelope(event, resourceType="federation", notification={
        "federation": {"federationId": "sciencemesh",
                       "url": ("https://sender.example.org"
                               if event == "OCM_SERVER_REMOVED"
                               else "https://receiver.example.org")}})
    for event in SERVER_EVENTS
})


COLLECTION_DECLINE = envelope(
    "SHARE_DECLINED", resourceType="collection", collectionId="research-data-123",
    notification={"collection": {"shareWith": "alice@alice.example.org"}})


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
        cls.resource_validator = Draft4Validator({
            "$ref": "#/components/schemas/ShareStateNotification",
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
        removed = deepcopy(PAYLOADS["USER_REMOVED"])
        removed["notification"]["user"]["targetUserId"] = "bob@receiver.example.org"
        self.assertFalse(self.validator.is_valid(removed))

    def test_collection_request_required_fields(self):
        for field in ("resourceType", "collectionId", "shareType", "notification"):
            with self.subTest(field=field):
                request = deepcopy(PAYLOADS["REQUEST_SHARE"])
                del request[field]
                self.assertFalse(self.validator.is_valid(request))
        for field in ("owner", "shareWith", "permissions"):
            with self.subTest(collection_field=field):
                request = deepcopy(PAYLOADS["REQUEST_SHARE"])
                del request["notification"]["collection"][field]
                self.assertFalse(self.validator.is_valid(request))

    def test_collection_request_extensions(self):
        request = deepcopy(PAYLOADS["REQUEST_SHARE"])
        request["notification"]["collection"]["permissions"] = []
        self.validator.validate(request)
        request["shareType"] = "EXAMPLE_CUSTOM_RECIPIENT"
        request["collectionId"] = "opaque @collection/id?#"
        request["notification"]["file"] = {"opaque": "extension"}
        self.validator.validate(request)
        request["collectionId"] = ""
        self.validator.validate(request)
        request["collectionId"] = None
        self.assertFalse(self.validator.is_valid(request))

    def test_collection_request_forbids_collection_size(self):
        for value in (1, None, "", []):
            with self.subTest(value=value):
                request = deepcopy(PAYLOADS["REQUEST_SHARE"])
                request["collectionSize"] = value
                self.assertFalse(self.validator.is_valid(request))

    def test_retired_request_cannot_use_fallback(self):
        request = envelope(
            "REQUEST_SHARE", resourceType="file",
            notification={"file": {"owner": "alice@sender.example.org",
                                   "shareWith": "bob@receiver.example.org",
                                   "shareId": "resource-456", "permissions": ["read"]}})
        self.assertFalse(self.validator.is_valid(request))

    def test_collection_decline(self):
        self.validator.validate(COLLECTION_DECLINE)
        decline = deepcopy(COLLECTION_DECLINE)
        decline["shareType"] = "EXAMPLE_CUSTOM_RECIPIENT"
        self.validator.validate(decline)
        for field in ("collectionId", "notification"):
            with self.subTest(field=field):
                missing = deepcopy(COLLECTION_DECLINE)
                del missing[field]
                self.assertFalse(self.validator.is_valid(missing))
        missing = deepcopy(COLLECTION_DECLINE)
        del missing["notification"]["collection"]["shareWith"]
        self.assertFalse(self.validator.is_valid(missing))

    def test_collection_decline_cannot_match_resource_state(self):
        decline = deepcopy(COLLECTION_DECLINE)
        decline["notification"]["file"] = {"providerId": "incidental-grant-id"}
        self.validator.validate(decline)
        self.assertFalse(self.resource_validator.is_valid(decline))
        del decline["collectionId"]
        self.assertFalse(self.validator.is_valid(decline))

    def test_resource_events_exclude_reserved_types(self):
        for event in (*SHARE_EVENTS, "REQUEST_RESHARE"):
            with self.subTest(event=event):
                payload = deepcopy(PAYLOADS[event])
                for resource in ("collection", "federation"):
                    payload["resourceType"] = resource
                    self.assertFalse(self.validator.is_valid(payload), resource)
                payload["resourceType"] = "EXAMPLE_CUSTOM_RESOURCE"
                self.validator.validate(payload)
        folder = deepcopy(PAYLOADS["SHARE_DECLINED"])
        folder["resourceType"] = "folder"
        self.validator.validate(folder)

    def test_deprecated_id_cannot_replace_nested_share_id(self):
        for event in SHARE_EVENTS:
            with self.subTest(event=event):
                payload = deepcopy(PAYLOADS[event])
                payload["providerId"] = payload["notification"]["file"].pop("providerId")
                self.assertFalse(self.validator.is_valid(payload))

    def test_server_membership_payloads(self):
        for event in SERVER_EVENTS:
            payload = PAYLOADS[event]
            for field in ("federationId", "url"):
                for remove in (True, False):
                    invalid = deepcopy(payload)
                    if remove:
                        del invalid["notification"]["federation"][field]
                    else:
                        invalid["notification"]["federation"][field] = 7
                    with self.subTest(event=event, field=field, remove=remove):
                        self.assertFalse(self.validator.is_valid(invalid))
            for change in ({"shareType": "user"}, {"shareType": None},
                           {"resourceType": "file"}):
                with self.subTest(event=event, change=change):
                    self.assertFalse(self.validator.is_valid({**payload, **change}))
            extended = deepcopy(payload)
            extended["notification"]["federation"].update(
                name="ScienceMesh", mlsGroupId="opaque", future={"value": 1})
            self.validator.validate(extended)

    def test_notification_permissions(self):
        contexts = (("SHARE_CHANGE_PERMISSION", "file"),
                    ("REQUEST_RESHARE", "file"), ("REQUEST_SHARE", "collection"))
        permissions = ("read", "create", "update", "delete", "write", "share", "view")
        for event, key in contexts:
            for permission in (*permissions, "admin", 7, None):
                payload = deepcopy(PAYLOADS[event])
                payload["notification"][key]["permissions"] = [permission]
                with self.subTest(event=event, permission=permission):
                    self.assertEqual(self.validator.is_valid(payload),
                                     permission in permissions)

    def test_share_protocol_view_permission(self):
        protocol = self.spec["components"]["schemas"]["NewShare"]["properties"]["protocol"]
        validator = Draft4Validator({
            "$ref": "#/components/schemas/NewShare/properties/protocol",
            "components": self.spec["components"],
        })
        for name, accepted in (("webdav", False), ("webapp", True)):
            payload = deepcopy(protocol["example"]["multipleProtocols"])
            payload[name]["permissions"] = ["view"]
            with self.subTest(protocol=name):
                self.assertEqual(validator.is_valid(payload), accepted)

    def test_unknown_type(self):
        self.validator.validate(envelope("EXAMPLE_CUSTOM_EVENT", resourceType="file"))
        self.validator.validate(envelope("EXAMPLE_COLLECTION_EVENT", resourceType="collection"))
        self.validator.validate(envelope("EXAMPLE_FEDERATION_EVENT", resourceType="federation"))

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
        self.assertEqual(len(exclusions), 11)
        self.assertEqual(set(exclusions), builtin_types)
        self.assertEqual(set(PAYLOADS), builtin_types)

    def test_published_operation_examples(self):
        operation = self.spec["paths"]["/notifications"]["post"]
        examples = operation["requestBody"]["content"]["application/json"]["examples"]
        self.assertTrue(examples)
        self.assertIn("requestShare", examples)
        self.assertEqual(examples["requestShare"]["value"], PAYLOADS["REQUEST_SHARE"])
        for name, example in examples.items():
            with self.subTest(example=name):
                self.validator.validate(example["value"])


if __name__ == "__main__":
    unittest.main()
