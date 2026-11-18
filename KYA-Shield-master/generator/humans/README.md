# Consented human session collector

This folder contains the collection boundary for real human sessions. Do not mark synthetic
rows as real humans. Recruit volunteers only after written consent using the template in
`docs/05_DATASET_SPEC.md`.

The collector must:

1. Run only against the local mock bank.
2. Record timing and interaction metadata, never password values or raw personal data.
3. Store a pseudonymous volunteer ID separately from consent forms.
4. Allow deletion before submission.
5. Mark collected rows with `augmented=false` and a collection provenance field.

The current dataset's 120 human rows remain synthetic placeholders until this process is used.

## Local collection command

After a volunteer completes a session in the local mock bank, confirm consent and export only
that session:

```powershell
D:\anaconda\python.exe -m generator.humans.collector `
  --session-id human-session-001 `
  --volunteer-reference volunteer-001 `
  --confirm-consent
```

Records are written separately under `data\human_sessions\`. The volunteer reference is never
stored; only a salted pseudonymous ID is retained. To honor deletion before submission:

```powershell
D:\anaconda\python.exe -m generator.humans.collector `
  --delete-volunteer human-<pseudonymous-id>
```

The collector rejects password, token, credential, contact, and unbounded text fields. Do not
copy `data\human_sessions` into the synthetic `data\sessions.jsonl` until the collection has
been reviewed and the consent record is stored separately.
