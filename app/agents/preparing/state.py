

# app/agents/prepare/state.py
from typing import TypedDict, List, Dict, Any, Optional,Annotated
from app.supervisor.state import update_dict

class PrepareState(TypedDict):
    """
    Local state for the Prepare Agent - Refactored for dynamic stages.
    """
    #---INPUTS---

    # Add: Service_info
    service_info: Optional[Dict[str,Any]]
    # The MINIMAL Stage 1 plan steps from the supervisor
    # 🔥 FIXED KEY NAME (consistent underscore)
    action_plan_stage_1_steps: List[Dict[str, Any]]

    # Accumulated answers from the user across ALL stages
    # 🔥 FIX: Use Annotated to merge answers across multiple resume calls
    user_answers: Annotated[Optional[Dict[str, Any]], update_dict]

    #---INTERNAL TRACKING----
    # Track if Stage 1 questions have been asked/answered
    stage_1_complete: bool

    # NEW: This will hold the result from our new node
    content_classification: Optional[Dict[str,Any]]  # e.g, {"type":"Hiring Ad","category":"Business"}

    #---OUTPUTS---
    # Questions generated for the CURRENT stage (Stage 1 or Stage 2)
    questions_for_user: Optional[List[Dict]]

    # The final payload for the processing agent
    generation_payload: Optional[Dict[str, Any]]

    #Flag to signal completion
    prepare_complete: bool=False

    