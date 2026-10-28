# Discovery operation contract

`sdlc.py` is a deterministic Python 3.10+ CLI. It operates on an explicitly selected
existing project directory, independently of that project's application stack.
The conversational entrypoint is [SKILL.md](../skill/SKILL.md).

From the orchestrator repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r orchestrator/requirements.txt
.venv/bin/python orchestrator/scripts/sdlc.py --project /absolute/project new --title "Customer notifications" --idea "Customers need to know when their request changes."
.venv/bin/python orchestrator/scripts/sdlc.py --project /absolute/project open REQ-0001
.venv/bin/python orchestrator/scripts/sdlc.py --project /absolute/project validate REQ-0001
.venv/bin/python orchestrator/scripts/sdlc.py --project /absolute/project validate
```

These are tool-facing arguments. The skill derives a title and passes the user's
description; users need not specify IDs or paths when presenting a business idea.
`--version` reports the orchestrator version independently of the schema version.

## Schema 0.1

`new` creates `requirements/REQ-0001-<derived-slug>/metadata.yaml` and `idea.md`:

```yaml
schema_version: '0.1'
id: REQ-0001
title: Customer notifications
status: discovery
artifacts:
  idea: idea.md
```

All five fields are required; unknown fields, duplicate YAML keys (including nested
keys), aliases, merge keys, non-string mapping keys, unsafe YAML tags, and malformed YAML
are rejected. The title must be nonempty single-line text. IDs are canonical ASCII
`REQ-0001` through `REQ-9999`; exhaustion fails explicitly rather than wrapping.
The only supported record statuses are `discovery` and `cancelled`: the latter is
read-only compatibility for retained cancelled records so their IDs remain reserved.
There is no cancellation operation or transition to any other lifecycle state.

Every immediate subdirectory of `requirements/` is treated as an Epic record.
Each must have a regular, nonsymlink `metadata.yaml`. Ordinary top-level files such
as a README are ignored, but a `REQ-*` file is an invalid Epic entry. Epic-directory
and requirements-directory symlinks are rejected. The metadata ID, not the folder
name, is authoritative: directory renames preserve identity and lookup still works.
No second directory index or ID counter is stored.

`artifacts.idea` must reference an existing UTF-8 file inside its own Epic directory.
Absolute paths, parent traversal, symlink escapes, and references to metadata itself
are rejected. Business content is stored only in the referenced Markdown file.
The template covers Problem, Users, Expected value, Initial scope, Success criteria,
Assumptions, and Open questions. Empty or absent level-two sections produce warnings;
this is a mechanical completeness check, not semantic analysis or a readiness gate.
Nonempty placeholders such as `TBD` and contradictory business statements are not
evaluated. Successful structural validation, even with no warnings, does not establish
business correctness or readiness for approval or implementation.

## Behavior and diagnostics

- `new`: validate the existing records, allocate highest existing numeric ID + 1
  (including cancelled records), derive a safe slug, and exclusively create the
  two files. Existing content is never overwritten. Handled failures remove files
  and the Epic directory created by that invocation. Empty input is allowed for
  business content, with warnings. A title is required.
- `open ID`: scan and validate the repository, find the unique metadata ID, and return
  its metadata, actual directory, content, and warnings without changing anything.
- `validate [ID]`: report structural validity for the requested record or all records.
  Repository-wide structural errors are always reported, including duplicate IDs.
  A repository with no Epic records is structurally valid. Missing business information
  is a warning; missing `idea.md` is a structural error.

All output is JSON on stdout. `ok` describes structural success only, accompanied
by `operation`, `diagnostics`, and either `epic` (new/open) or `validated_ids`
(validate). Each diagnostic has `severity`, `code`, `file`, `message`, and optional
YAML `line`. Exit status is 0 for success (including warnings), 1 for operational or
validation failure, and 2 for argparse usage errors (which use stderr).

| Code | Meaning |
|---|---|
| `E_PROJECT`, `E_REQUIREMENTS`, `E_EPIC_DIRECTORY` | Invalid project or repository layout |
| `E_METADATA_FILE`, `E_READ`, `E_IO` | Missing/unreadable file or filesystem failure |
| `E_YAML`, `E_METADATA` | Invalid YAML, duplicate keys, or incorrect metadata fields |
| `E_SCHEMA_VERSION` | Unsupported or incorrectly typed schema version; no migration |
| `E_EPIC_ID`, `E_DUPLICATE_ID`, `E_EPIC_NOT_FOUND`, `E_ID_EXHAUSTED` | Invalid, ambiguous, missing, or exhausted identity |
| `E_TITLE`, `E_STATUS`, `E_ARTIFACTS` | Invalid field value or structure |
| `E_ARTIFACT_PATH`, `E_ARTIFACT_FILE` | Unsafe reference or missing artifact |
| `E_PROJECT_BUSY` | Transient local creation lock already exists |
| `W_DISCOVERY_INCOMPLETE` | Missing/empty business section; not a structural error |

Creation uses a transient `.sdlc-discovery.lock/` directory at the project root;
cooperating concurrent local writers fail closed. The lock is removed after normal
completion or a handled exception and is not a context checkpoint. Independent-clone
coordination, hard process termination/power-loss recovery, and hostile concurrent
filesystem mutation are not covered. A stale lock requires inspection before manual
removal. Retain cancelled records: physically deleted records cannot reserve IDs
because this increment reads existing files only and never consults Git history.

The CLI never invokes Git or changes approval/readiness states. Unsupported schemas
and inconsistent existing records block creation/opening rather than being repaired.
