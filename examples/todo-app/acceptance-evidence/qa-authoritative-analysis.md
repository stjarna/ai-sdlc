# Functional Analysis — REQ-0001

Baseline: 124a4eb4597b0fdfa2fbd179ec109e5e16ec15a2127c4b4f7e7bc79de480ed0c
Approval: BD-0002
Handoff: human-business-advance-a77bda61-729f-4de7-8dec-7911fb7a8cb4

## Functional requirements
### FR-001 — Record a future due date
Business sources: B-002
Discovery evidence: D-0001
Status: specified
Questions: -
Statement: A user can assign a future due date to a task, and that task records the supplied date. This specifies an upcoming-commitment scenario; it does not establish a future-only restriction or decide past-date behavior.

### FR-002 — Keep a task without a due date
Business sources: B-002, B-003
Discovery evidence: D-0005, D-0004
Status: specified
Questions: -
Statement: A task can have no due date. Assigning a due date is optional.

### FR-003 — Past-date assignment
Business sources: B-002
Discovery evidence: D-0001
Status: blocked
Questions: AQ-001
Statement: The outcome of attempting to assign a past due date is not specified. Neither acceptance nor rejection is selected by this draft.

## Use cases
### UC-001 — Record an upcoming commitment
Business sources: B-002
Discovery evidence: D-0001
Status: specified
Requirements: FR-001
Questions: -
Actor: A user managing a task
Preconditions: A task is available for due-date assignment.
Trigger: The user wants to record the task's upcoming due date.
Main flow: 1. The user identifies the task and supplies a future due date.
  2. The task records the supplied due date.
Alternative flows: If the task is left without a due date, the optionality scenario applies. A past-date attempt has no specified outcome pending the deferred business decision.
Outcome: The task has the user-supplied future due date.

### UC-002 — Leave a task undated
Business sources: B-002, B-003
Discovery evidence: D-0005, D-0004
Status: specified
Requirements: FR-002
Questions: -
Actor: A user managing a task
Preconditions: The task has no due date.
Trigger: The user chooses not to assign a due date.
Main flow: 1. The user leaves the task without a due date.
  2. The task remains undated; a due date is not required.
Alternative flows: The user may instead assign a future due date using the assignment scenario. Removing an already assigned date is not specified by this use case.
Outcome: The task remains without a due date.

## Business rules
### BR-001 — Due dates are optional
Business sources: B-003
Discovery evidence: D-0005, D-0004
Status: specified
Requirements: FR-002
Questions: -
Statement: A task is not required to have a due date. This rule follows explicit human confirmation of the originating optionality assumption.

## Acceptance criteria
### AC-001 — Record the supplied future date
Business sources: B-002
Discovery evidence: D-0001
Status: specified
Requirements: FR-001
Questions: -
Given: A task with no assigned due date, and a future calendar date selected by the user.
When: The user assigns the selected date as that task's due date.
Then: That task has an assigned due date whose day, month and year match the selected date. Its resulting state is a task with that assigned date, rather than a task without a due date.

### AC-002 — No due date is required
Business sources: B-003
Discovery evidence: D-0005
Status: specified
Requirements: FR-002
Questions: -
Given: A task with no assigned due date.
When: The user leaves the due date unspecified for that task.
Then: That task remains without an assigned due date: there is no assigned date value. This is a permitted task state; assigning a due date is not required.

## Business coverage
- **B-001** [contextual] - | Tracking upcoming commitments provides business value; it does not introduce another functional capability.
- **B-002** [elaborated] FR-001, FR-002 | Covers assignment and optionality. Past-date behavior remains blocked separately. Reminders and notifications remain outside the initial scope.
- **B-003** [elaborated] FR-002, BR-001 | Explicitly confirmed optionality is represented as behavior and a business rule.
- **B-004** [excluded] - | Reminders are outside the initial scope; no reminder feature or artificial requirement is created.

## Inherited unresolved items
- **U-001** [D-0006] Deferred: whether users may choose a date in the past. Decision D-0007 defers this question until consultation with support. No rule allowing or rejecting past dates has been decided.

## Analysis questions
### AQ-001 — May a due date be in the past?
Business sources: B-002
Discovery evidence: D-0006
Status: deferred
Affected items: FR-003
Statement: Whether users may choose a past due date remains deferred pending consultation with support. There is no acceptance criterion choosing acceptance or rejection of such a date.

### AQ-002 — Changing or clearing an existing due date
Business sources: B-002
Discovery evidence: D-0001
Status: open
Affected items: FR-001, FR-002
Statement: The ability to change or clear an already assigned due date has not yet been defined. This remains an open Analysis question, not an implied functional capability. Neither changing nor clearing an assigned due date is specified as a functional requirement or acceptance criterion. Defining either behavior requires upstream business refinement and renewed approval.

## Analysis proposals
None recorded.
