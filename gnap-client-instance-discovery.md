For an RO to dynamically register a client instance, they can:
* provide its FQDN
* the AS will retrieve the .well-known
* if this fails, it can do an SRV lookup
* the AS takes a decision whether to dynamically add the client instance or not
