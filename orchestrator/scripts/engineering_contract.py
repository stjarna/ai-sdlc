"""Fixed engineering sequence; shared constants, not a workflow policy registry."""
STAGES = ('technical_design', 'ready_for_implementation_planning', 'implementation_planning',
          'ready_for_development', 'development', 'verification', 'security_review',
          'final_verification', 'verified')
DOWNSTREAM = ('ready_for_technical_design', *STAGES)
TRANSITIONS = {
    'ready_for_technical_design': ('technical_design',),
    'technical_design': ('ready_for_implementation_planning',),
    'ready_for_implementation_planning': ('implementation_planning',),
    'implementation_planning': ('ready_for_development',),
    'ready_for_development': ('development',),
    'development': ('verification',),
    'verification': ('security_review', 'development'),
    'security_review': ('final_verification', 'development'),
    'final_verification': ('verified', 'development'),
    'verified': (),
}
ROLES = {
    'technical_design': ('technical_design', 'Engineering Lead / Architect'),
    'ready_for_implementation_planning': ('implementation_planning', 'Engineering Lead'),
    'implementation_planning': ('implementation_planning', 'Engineering Lead'),
    'ready_for_development': ('development', 'Developer'),
    'development': ('development', 'Developer'),
    'verification': ('verification', 'QA / Quality Engineering'),
    'security_review': ('security_review', 'Application Security'),
    'final_verification': ('final_verification', 'QA / Quality Engineering'),
    'verified': ('verified', 'Requester / Product Owner'),
}
