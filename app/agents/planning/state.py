

# agents/planning/state.py
from typing import TypedDict, Dict, Any, Optional

class PlanningState(TypedDict):
    """
    The local state for the Planning Agent's internal workflow.
    It now focuses solely on generating the master action plan.
    """
    
    # 🔥 CHANGE: This now receives the FULL service_info object
    # This object contains 'plan_mode', 'plan_path', and 'planning_guidelines'
    service_info: Dict[str, Any]
    
    # OUTPUT: The detailed, structured plan for all other agents.
    action_plan: Optional[Dict[str, Any]]