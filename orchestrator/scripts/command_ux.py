"""Read-only routing for six conversational intents; never execute a decision."""
COMMANDS = ("status", "review", "approve", "changes", "advance", "details", "inbox", "pending assignments", "assign")
STAGES = {
    "discovery": "discovery",
    "ready_for_refinement": "business_refinement",
    "business_refinement": "business_refinement",
    "ready_for_analysis": "functional_analysis",
    "functional_analysis": "functional_analysis",
    "ready_for_technical_design": "analysis_handoff",
    "cancelled": "cancelled",
}


def route(command, status):
    if command not in COMMANDS or status not in STAGES:
        raise ValueError("Unsupported command or lifecycle state.")
    stage = STAGES[status]
    review = "business-review" if stage == "business_refinement" else "analysis-review" if stage in ("functional_analysis", "analysis_handoff") else "open"
    operation, explanation = None, None
    if command == "assign":
        operation = "assign" if status != "cancelled" else None
        if operation is None:
            explanation = "Cancelled requests cannot be assigned."
    elif command == "approve":
        if status in ("business_refinement", "functional_analysis"):
            operation = "business-approve" if status == "business_refinement" else "analysis-approve"
        elif status == "discovery":
            explanation = "Discovery has completion, not approval. Use advance after reviewing the Discovery outcome."
        else:
            explanation = "There is no active approvable draft in this lifecycle state."
    elif command == "changes":
        operation = {"discovery": "discovery-update", "business_refinement": "business-request-changes", "functional_analysis": "analysis-request-changes"}.get(status)
        if operation is None:
            explanation = "Changes require explicit upstream reopening or preparation of the next draft."
    elif command == "advance":
        operation = {"discovery": "discovery-complete", "business_refinement": "business-advance", "functional_analysis": "analysis-advance"}.get(status)
        if operation is None:
            explanation = "The request is already at a handoff or has no available transition. Do not start the next stage automatically."
    return {"command": command, "stage": stage, "review_operation": review,
            "write_operation": operation, "explanation": explanation,
            "read_only": True, "requires_human_decision": operation is not None}
