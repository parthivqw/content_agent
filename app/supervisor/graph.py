# app/supervisor/graph.py

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState
from .nodes import (
    determine_service_entrypoint_node,
    run_planning_agent_node,
    run_prepare_agent_node,
    run_processing_agent_node,
    run_execution_agent_node,
    handle_failure_node
)
from app.agents.execution.graph import execution_agent_app

supervisor_memory = MemorySaver()

# --- Router 1: After Planning (Unchanged) ---
def after_planning_router(state: AgentState) -> str:
    print("---SUPERVISOR ROUTER: After Planning---")
    if state.get("interaction_is_required"):
        print("---SUPERVISOR ROUTER: Pausing for user to review plan.---")
        return END
    else:
        if state.get("action_plan", {}).get("error"):
             print("---SUPERVISOR ROUTER: Error in plan generation, ending workflow.---")
             return END
        print("---SUPERVISOR ROUTER: Plan approved/no approval needed, proceeding to Prepare Agent.---")
        return "prepare_agent"

# --- 🔥 FINAL REVISED Router 2: After Prepare ---
def after_prepare_router(state: AgentState) -> str:
    """
    Checks state after the prepare_agent bridge node using explicit completion flag.
    - If pausing for questions -> END (Pause Supervisor)
    - If prepare_complete is True and payload valid -> processing_agent
    - If prepare_complete is True and payload error -> END
    - If prepare_complete is False (and not pausing) -> prepare_agent (Loop back)
    """
    print("---SUPERVISOR ROUTER: After Prepare---")

    # Get flags and data from the state
    interaction_required = state.get("interaction_is_required")
    prepare_complete = state.get("prepare_complete") # Check the NEW flag
    generation_payload = state.get("generation_payload")

    # Case 1: Pausing for questions? (Highest priority)
    if interaction_required and state.get("questions_for_user"):
        print("---SUPERVISOR ROUTER: Pausing for user to answer questions.---")
        return END # Pause supervisor

    # Case 2: Prepare agent explicitly signaled completion?
    if prepare_complete is True:
        if generation_payload and not generation_payload.get("error"):
            # Completed successfully!
            print("---SUPERVISOR ROUTER: Prepare complete, payload ready. Proceeding to Processing Agent.---")
            return "processing_agent"
        else:
            # Completed with an error
            error_msg = generation_payload.get("error", "Unknown error") if generation_payload else "Missing payload"
            print(f"---SUPERVISOR ROUTER: Prepare complete but with error ({error_msg}). Ending.---")
            return END # Stop on error

    # Case 3: Not pausing and not complete? Must need to loop back.
    print("---SUPERVISOR ROUTER: Prepare not complete, looping back to Prepare Agent.---")
    # We might need to ensure questions_for_user is cleared before looping
    # but the bridge node now handles clearing it when returning payload.
    return "prepare_agent" # Loop back

# --- 🔥 REPLACE YOUR OLD ROUTER WITH THIS ---
def after_processing_router(state: AgentState) -> str:
    """
    Handles routing after the creative content is generated.
    Checks for errors in *either* flow (social or blog).
    """
    print("---SUPERVISOR ROUTER: After Processing---")
    
    # 🔥 CRITICAL DEBUG: Let's see what's actually in the state
    print(f"🔍 DEBUG: interaction_is_required = {state.get('interaction_is_required')}")
    print(f"🔍 DEBUG: blog_draft exists = {state.get('blog_draft') is not None}")
    print(f"🔍 DEBUG: blog_draft value = {str(state.get('blog_draft'))[:100]}...")
    print(f"🔍 DEBUG: draft_caption = {state.get('draft_caption')}")
    print(f"🔍 DEBUG: cover_image_prompt exists = {state.get('cover_image_prompt') is not None}")
    
    # Get the service ID to know which error to check
    service_id = state.get("service_info", {}).get("id")

    # 🔥 FIX: Check for pause FIRST, before error checking
    if state.get("interaction_is_required"):
        print("---SUPERVISOR ROUTER: Pausing for user to review creative.---")
        return END

    # --- NOW check for service-specific errors ---
    if service_id == "blog_generator":
        blog_draft = state.get("blog_draft")
        if not blog_draft or (isinstance(blog_draft, str) and blog_draft.startswith("Error:")):
            print("---SUPERVISOR ROUTER: Error in blog_generator. Ending ---")
            return END
    else:
        # Default to social media post check
        if not state.get("image_prompts") or "Error" in state.get("image_prompts", [""])[0]:
            print("---SUPERVISOR ROUTER: Error in social_media_post. Ending ---")
            return END
        
    # If no pause and no errors, proceed to execution
    print("---SUPERVISOR ROUTER: User approved creative, proceeding to Execution.---")
    return "execution_agent"

def after_execution_router(state: AgentState) -> str:
    """
    Checks state after the execution agent
    -If validation_result is "no" -> "handle_failure_node"
    -If interaction_is_required (success) -> END(pause)
    -Otherwise -> END
    """
    print("---SUPERVISOR ROUTER: After Execution---")

    validation_result=state.get("validation_result")
    

    #This is our "not kool" path
    #As you said FOR NOW, we just END
    if validation_result=="no":
        print(f"---SUPERVISOR ROUTER: Validation Failed. Routing to failure handler.---")
        return "handle_failure_node" # Route to retry manager
    

    if state.get("interaction_is_required"):
        print("---SUPERVISOR ROUTER:Pausing to show generated image(s).---")
        return END
    print("---SUPERVISOR ROUTER:Execution complete or failed. Ending ---")
    return END

#---NEW: Router 5: After Failure Handler---
def after_failure_router(state: AgentState)-> str:
    """
    Checks the retry_count and decides whether to loop or end.
    
    """
    print("---SUPERVISOR ROUTER: After Failure Handler---")

    #Define our retry limit
    MAX_RETRIES=2

    current_count=state.get("retry_count",0)

    if current_count>=MAX_RETRIES:
        print(f"---SUEPRVISOR ROUTER: Max retries ({MAX_RETRIES}) reached .Ending Workflow.---")
        return END
    else:
        print(f"---SUPERVISOR ROUTER: Retry attempt {current_count}. Looping back to Processing Agent.--- ")
        return "processing_agent" # We've already implemented the count, so now we just loop back

    

# --- Graph Definition (Unchanged from last version) ---
workflow = StateGraph(AgentState)

workflow.add_node("service_lookup", determine_service_entrypoint_node)
# ... (add other nodes: planning_agent, prepare_agent, processing_agent) ...
workflow.add_node("planning_agent", run_planning_agent_node)
workflow.add_node("prepare_agent", run_prepare_agent_node)
workflow.add_node("processing_agent", run_processing_agent_node)
workflow.add_node("execution_agent",run_execution_agent_node)
workflow.add_node("handle_failure_node",handle_failure_node)


# --- Define edges (Unchanged from last version) ---
workflow.set_entry_point("service_lookup")
workflow.add_edge("service_lookup", "planning_agent")

workflow.add_conditional_edges("planning_agent", after_planning_router, {
    "prepare_agent": "prepare_agent",
    END: END
})

# Edges after prepare agent now use the final revised router
workflow.add_conditional_edges("prepare_agent", after_prepare_router, {
    "processing_agent": "processing_agent",
    "prepare_agent": "prepare_agent", # Loop back edge
    END: END
})

workflow.add_conditional_edges("processing_agent",after_processing_router,{
    "execution_agent":"execution_agent",
    END:END
})

#----NEW: Add execution agent edge---
#For now, the execution agent just pauses or ends.
#In the future, this router could loop back to "prepare_agent"
workflow.add_conditional_edges("execution_agent",after_execution_router,{
    "handle_failure_node":"handle_failure_node",
    END:END

    
})

#---NEW: Add failure loop edges---
workflow.add_conditional_edges("handle_failure_node",after_failure_router,{
    "processing_agent":"processing_agent",
    END:END # Give up
})
# Compile
supervisor_app = workflow.compile(checkpointer=supervisor_memory)
print("✅ Supervisor graph compiled with EXPLICIT Prepare Agent completion logic.")