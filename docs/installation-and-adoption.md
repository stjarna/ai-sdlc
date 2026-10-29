# External installation and existing-project adoption

The local POSIX PoC installs a pinned runtime outside the application and registers a
thin user-scoped Codex loader. It does not install application dependencies, edit project
instructions, initialize Git, restructure source/tests, or stage/commit/push anything.
Codex CLI and the IDE extension use the same user-scoped `.agents/skills` registration.
The complete runtime resource layout is preserved: scripts, shared guidance, current and
historical domain packages, templates and supporting docs. Application examples and the
orchestrator's development test suite are not runtime dependencies and are not bundled.

## Install an approved committed revision

Use a permanent source checkout and a permanent Python environment. Python 3.10+,
pinned PyYAML 6.0.3, Git and local POSIX filesystem/process semantics are required.
No external AI API or remote registry is used by installation or preflight.

```sh
orchestrator_source=/absolute/path/to/AI-SDLC
app_repo=/absolute/path/to/existing-application
runtime_venv="$HOME/.local/share/ai-sdlc/venv"
python3 -m venv "$runtime_venv"
"$runtime_venv/bin/python" -m pip install -r "$orchestrator_source/orchestrator/requirements.txt"

# Supply the explicitly selected, approved full Git commit SHA, not a moving branch.
revision=APPROVED_COMMIT_SHA
"$runtime_venv/bin/python" -B "$orchestrator_source/orchestrator/scripts/install.py" install \
  --source "$orchestrator_source" --revision "$revision" --project "$app_repo" \
  --python "$runtime_venv/bin/python"
```

Dependency setup above is explicit; the installer does not invoke pip or modify the
chosen environment. By default, runtime files live under
`~/.local/share/ai-sdlc/runtimes/<revision-prefix>-<installation-digest-prefix>/` and the
loader under `~/.agents/skills/sdlc/`. Overrides `--runtime-root` and `--skill-root` support
isolated testing. Arbitrary skill roots are not automatically discovered: for normal use,
retain the standard user location. No global Codex config is edited.

The default install reads exact committed Git bytes, regardless of unrelated working-tree
changes. The selected revision must include this installation increment. Before that
increment is committed, an explicitly requested `--preview-working-tree` installation is
available for review: its base must be HEAD, `preview: true` is recorded, and exact selected
working-tree bytes plus interpreter path are content-pinned. It is never labelled a
committed release. Do not use a preview as evidence of a subsequently committed release.

The installation manifest records base Git revision, preview status, every payload file
hash, interpreter path and full installation digest. Environment validation checks the
Python/PyYAML version, all domain/template catalog pins and referenced skill resources.
Git newline conversion cannot change packaged resource bytes. Pins are local integrity
checks, not signatures, authenticated identity or protection from an unrestricted editor.
The selected Python environment must remain available separately from the runtime.

An existing skill is never replaced, including a differently named folder declaring
`name: sdlc`. An identical existing installation/loader can be verified and replayed.
Upgrading or removing a registration is a deliberate operator action after inspection;
there is no automatic overwrite, migration, uninstaller or current-release pointer.
Installation is staged then renamed. A handled preparation failure removes staging
folders; interruption before registration may leave a complete unregistered runtime,
which an exact retry verifies and reuses. A corrupt installation or abandoned lock needs
operator inspection; no automatic lock deletion or baseline repair occurs.

## Verify and discover

Use the absolute runtime path and digest returned by installation:

```sh
runtime=/absolute/path/returned/by/install
"$runtime_venv/bin/python" -B "$runtime/orchestrator/scripts/install.py" verify \
  --runtime "$runtime" --expected-digest EXACT_INSTALLATION_DIGEST \
  --skill-root "$HOME/.agents/skills"
```

Open the **application** repository in Codex CLI or the IDE. Inspect `/skills` or type
`$sdlc status`; confirm the selected entry is the installed user loader. Restart if
new discovery is not visible. The loader checks runtime integrity before loading the
shared workflow and keeps the application as the explicit target. It does not treat
skill invocation as business approval or advance the lifecycle automatically.

Host permissions must allow reading the external runtime and writing the selected
application when later operations are authorized. Disabled skills, other system/plugin
registrations and host policy can still affect discovery. Static registration checks
are not proof of UI discovery; record a real host check. Official references:
[Codex skills](https://learn.chatgpt.com/docs/build-skills) and
[local app-server skills/list](https://learn.chatgpt.com/docs/app-server).
A local `skills/list` query needs no model turn or external AI API. CLI and IDE both
use app-server skill discovery; an app-server probe alone is not a claimed visual IDE test.

## Read-only adoption preflight

```sh
"$runtime_venv/bin/python" -B "$runtime/orchestrator/scripts/adoption.py" \
  --project "$app_repo" --runtime "$runtime" --skill-root "$HOME/.agents/skills"

# Equivalent default-location routing through the existing CLI:
"$runtime_venv/bin/python" -B "$runtime/orchestrator/scripts/sdlc.py" \
  --project "$app_repo" adoption-preflight
```

Output is JSON with `ok`, `ready`, `baseline_ready`, diagnostic code/file/message,
Git revision/status, discovered instructions/registrations and environment/pin details.
Nonzero exit indicates structural blockers. Warnings require review; even `ready: true`
is not approval, proof that tests pass, or permission to start another stage.
`baseline_ready` additionally requires a clean working tree. Dirty work is reported,
never cleaned, stashed or staged. Git reads disable optional index-refresh writes and bypass repository fsmonitor hooks.

Preflight checks:

- Existing Git repository root and initial commit; no Git initialization.
- Fixed `requirements/` and `qa/` namespace conflicts. Existing Epic records are validated
  through the unchanged validators. Existing QA requires retained managed automation
  history; unrelated QA is not silently claimed even when a Discovery request exists.
- Source symlinks and nonregular inputs under the unchanged source-scanning rules.
- Common existing generated-output directories/files and advisory `.gitignore` patterns.
  These are hazards, **not new exclusions**. Absent paths configured elsewhere may need
  manual inspection. Existing build/test runners must preserve fingerprinted inputs;
  place new execution evidence under the Epic's `requirements/` tree or outside the app
  according to the explicitly reviewed command. Do not move existing outputs silently.
- Existing root/nested project instructions and user/admin/project SDLC registrations.
  Host enable/disable settings and plugin/system discovery still require the host check.
- Runtime integrity, required resources and interpreter compatibility.

Do not copy the implementation checkout's `AGENTS.md` into the application. Retain its
existing instructions and existing tests. No project config, extra source exclusion,
workflow stage or approval framework is introduced. An incompatible namespace/layout
requires an explicit follow-up decision, not automatic relocation.

## Initialize the first request

After reviewing preflight, use the normal SDLC conversation and existing `new` operation.
The assistant reuses the declared local identity profile or guides explicit setup if
missing; it never derives approval identity from Git. `new` creates only the initial
Discovery request under `requirements/` and leaves existing application files untouched.
There is no separate init/checkpoint mechanism and no implicit approval of existing code.
Existing `new` remains compatible with non-Git projects; the Git/baseline check belongs
to the explicit existing-project adoption preflight.

See [the demonstration evidence runbook](existing-project-demo.md) for before/after capture.
