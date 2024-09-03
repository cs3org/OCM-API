To indicate that a new resource is available for a client instance to access,
an AS can send a notification to that client instance.
This notification may include:
* a displayable description of the resource
* instructions for accessing the resource
* a description of the intended end user, through an identifier or an attribute such as a group name.

There may be a response notification, accept/reject.

If the notification is addressed to an unregistered client instance, then the AS MAY dynamically register this client instance
using [GNAP client instance discovery](./gnap-client-instance-discovery.md).
