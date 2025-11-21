from typing import TypedDict, List,Dict,Any,Optional


class ProcessingState(TypedDict):
    """
    Local state for the Processing Agent.
    """
    #---Input----
    #The final, merged answers from the prepare_agent
    generation_payload: Dict[str,Any]

    #Pass he service_info
    service_info: Dict[str,Any]

    #---Output----
    #A list of 3 generated prompt variations
    image_prompts: Optional[List[str]]


    # The single generated caption
    draft_caption:Optional[str]

    #For the blog generator
    blog_draft: Optional[str]
    cover_image_prompt: Optional[str]

     # --- 🔥 NEW: FOR VALIDATION LOOP ---
    # The supervisor will pass the critique and failed draft back in
    critique: Optional[str]
    # We also need to accept interaction_is_required from the supervisor
    interaction_is_required: bool
    