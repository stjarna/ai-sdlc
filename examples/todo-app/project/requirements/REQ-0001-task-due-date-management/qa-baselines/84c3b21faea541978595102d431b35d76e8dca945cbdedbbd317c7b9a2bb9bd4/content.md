# QA Test Scenarios — Task Due Date Management

Status: proposed; all cases below are unexecuted. Testing 1.1.0 instruction pin is
recorded by the orchestrator. Functional oracle: approved immutable Analysis baseline
0e0144aa03e9ef1e1db88debcbf1152a0f2443e81bfb68b26706ef5c92136598. Technical Design and the old combined plan are
not the source of these expected outcomes.

## TC-001 — Specified

References: FR-002, AC-002.

Given: An existing task has no assigned due date.

When: Leave the due date unspecified for that task and observe its resulting state.

Then: The task remains without any assigned date value; this is a permitted state and a due date is not required. No clearing of an existing date is involved.

Execution: not run; no automation is prepared.

## TC-002 — Specified

References: FR-001, AC-001.

Given: An existing task has no assigned date; the user selects a known future calendar date.

When: Assign the selected future date to the identified task using the available user-facing operation.

Then: That task has the assigned date, with day, month and year exactly matching the user selection, rather than remaining undated. Parameterize applicable future calendar boundaries without imposing a business date range.

Execution: not run; no automation is prepared.

## TC-003 — Specified

References: FR-001, FR-002, AC-001, AC-002.

Given: Two identifiable existing tasks are undated, and a known future date is selected for the first task only.

When: Assign the selected future date to the first task; leave the second task unspecified.

Then: The identified first task records the exact selected calendar date. The second task remains without an assigned date, combining the two approved outcomes without requiring creation or date clearing.

Execution: not run; no automation is prepared.

## TC-004 — Blocked

References: FR-003.

Given: A task and a valid past calendar date are available; U-001/AQ-001 remain deferred.

When: Document the past-date scenario as blocked; do not execute it as a product pass/fail acceptance assertion.

Then: No approved expected product outcome exists. Neither acceptance nor rejection may be asserted until the deferred business decision and renewed authority are supplied.

Execution: not run; no automation is prepared.

## TC-005 — Blocked

References: FR-001, FR-002.

Given: A task already has an assigned due date; AQ-002 remains open.

When: Document changing or clearing the assigned date as undefined; do not automate either as an accepted functional capability.

Then: No approved outcome for changing or clearing exists. Do not infer either capability or its prohibition; keep this case blocked pending explicit upstream definition and approval.

Execution: not run; no automation is prepared.

## Coverage and unresolved decisions

TC-001/TC-002/TC-003 provide planned, reviewable coverage of AC-001 and AC-002. Calendar
boundary values in TC-002 are examples for future date preservation, not extra business
rules or a timezone requirement. Test data should remain clearly future under a controlled
fixture reference. Initial absence is distinct from clearing an assigned date.

TC-004 keeps FR-003/U-001/AQ-001 blocked/deferred. TC-005 records AQ-002 without asserting
a change/clear result. Neither blocked case may be assigned an automatic pass. A demo's
not-implemented response is not validation of an unspecified product rule.

Later automation must explicitly link every specified case to named integration/UI
checks, inspect actual approved interfaces and preserve these functional expectations.
There is no assumed API, selector, runtime or transport in this functional case artifact.
Automation has a separate review and execution gate. Approval of these scenarios accepts
only their reviewed expectations and acknowledged uncertainty; it does not approve
Engineering work, supply missing business decisions, advance QA or run tests.
