

# app/supervisor/state.py
from typing import TypedDict, Annotated, List, Dict, Any, Optional

# ---Reducer Function---
# This function is crucial. It tells LangGraph how to merge new data into an
# existing dictionary field in the state, rather than overwriting it.
def update_dict(original_dict, new_updates):
    if original_dict is None:
        original_dict = {}
    original_dict.update(new_updates)
    return original_dict

# ---The Main State Graph---
# This is the shared whiteboard for our entire multi-agent system.
class AgentState(TypedDict):
    # ----Core Inputs---
    initial_request: Dict[str, Any]
    thread_id: str

    # ---Supervisor Outputs---
    service_info: Dict[str, Any]
    action_plan: Optional[Dict[str, Any]]

    # ---Interaction Management----
    interaction_is_required: bool
    
    # 🔥 CHANGE 1: Add a field to hold the questions for the UI
    questions_for_user: Optional[List[Dict]]
    
    # 🔥 CHANGE 2: Add a field to hold the answers from the UI
    # We use Annotated to merge answers, not replace them.
    user_answers: Annotated[Optional[Dict[str, Any]], update_dict]
    
    # 🔥 CHANGE 3: Add a field for the PREPARE_AGENT's final output
    # This is the payload it will pass to the PROCESSING_AGENT
    generation_payload: Optional[Dict[str, Any]]

    # 🔥 NEW: Track prepare agent completion
    prepare_complete: bool

    # --- 🔥 NEW: Processing Agent Outputs ---
    image_prompts: Optional[List[str]]
    draft_caption: Optional[str]

    # 🔥 --- ADD THESE TWO LINES --- 🔥
    blog_draft: Optional[str]
    cover_image_prompt: Optional[str]

    #---NEW: Execution Agent Inputs (from UI)---
    selected_prompt: Optional[str]
    num_images: Optional[int]

    #---NEW: Execution Agent Outputs (to UI)---
    current_images_base64: Optional[List[str]]
    current_error: Optional[str]

    #---ADD THESE TWO LINES---
    validation_result: Optional[str]
    critique: Optional[str]

    #---VALIDATION LOOP---
    retry_count: int

    # Placeholder for the final result
    final_result: Optional[Any]