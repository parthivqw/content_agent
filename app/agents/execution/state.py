


from typing import TypedDict,List,Dict,Any,Optional

class ExecutionState(TypedDict):
    """
    Local state for the Execution Agent.
    Handles both social media and blog generation flows.

    """
    #---Shared Inputs (from Supervisor)---
    generation_payload: Dict[str,Any]
    service_info: Dict[str,Any] # We now need this for routing

    #---Social Media Flow Inputs ---
    image_prompts: Optional[List[str]]
    selected_prompt: Optional[str]
    num_images: Optional[int]

    #---Blog FLow Inputs---
    blog_draft: Optional[str]
    cover_image_prompt: Optional[str]
    draft_caption: Optional[str]

    #---NEW:Validation State---
    validation_result: Optional[str] # "yes " or "no "
    critique: Optional[str] # The feedback for the processing_agent

    #---Internal State(for Image Gen)---
    model_ranking: List[str]
    current_model_index: str


    #---Output(to supervisor/UI)---
    current_images_base64: Optional[List[str]]
    current_error: Optional[str]
    interaction_is_required: bool