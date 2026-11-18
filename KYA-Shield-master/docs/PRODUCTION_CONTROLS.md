# Production-style controls

The prototype now has explicit seams for a safer deployment:

- `kya.security.TrustedKeyRegistry`: maps mandate `key_id` values to Ed25519 public keys and supports revocation.
- `KYA_API_KEY`: when set, `POST /score` requires the matching `X-API-Key` header.
- `KYA_AUDIT_LOG`: append-only JSONL audit destination; defaults to `audit/events.jsonl`.
- `KYA_SHADOW_MODE=true`: keeps the scored recommendation in `recommended_action` while returning `action=allow`.

The in-memory registry and environment API key are demo controls, not production key custody.
Production should use a KMS/HSM, secret manager, rotation, mTLS/service identity, durable
tamper-evident audit storage, and a formal revocation service.

Shadow mode is the required first integration stage: observe recommendations without blocking or
intervening in real payments, compare against existing controls, and obtain fraud-analyst signoff.
