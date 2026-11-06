# Port compatibility V1

Ports declare identity, version, direction, schema, semantics, required/default
behavior and compatibility policy. Implementation hashes are Variant identities,
not Port versions. Input substitution is contravariant; output substitution is
covariant. Semantics and defaults cannot silently change.

`compare_ports` yields IDENTICAL, COMPATIBLE, ADAPTABLE or BREAKING. Supported
structural inference covers object fields, requiredness, additional properties,
arrays, scalar types, enums and numeric bounds. Unknown keywords are opaque;
unequal unsupported schemas fail closed. This is not a complete JSON Schema engine.
Effect guarantees currently require exact equality; changed external writes,
persistence, ordering, concurrency or idempotency are BREAKING.

The deterministic adapter supports explicit field rename and optional declared
defaults. Rename mappings require explicit semantic authorization; matching
Python types alone is insufficient. Missing required information, collisions,
unknown fields and invalid values yield AUTO_ADAPTER_DENIED. Enum maps and
wrapper/split/merge adapters are not yet implemented. Adapter verification is
still mandatory even when the transform is mechanically provable.

The host owns consumer/usage counts. Zero consumers yields an archive/removal
recommendation, not deletion of history. No automatic adapter chains are built.
