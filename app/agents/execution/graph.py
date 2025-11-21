# app/agents/execution/graph.py
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from .state import ExecutionState
from .nodes import get_model_ranking_node, generate_image_node,validation_node # <-- Import our 3 nodes

execution_memory = MemorySaver()


#---ROUTER 1: AT THE START---
def execution_service_router(state: ExecutionState) -> str:
    """
    Checks the Service ID and routes to the correct starting node.
    """
    service_id=state.get("service_info",{}).get("id")
    print(f"---EXEC AGENT: Routing based on service_id:{service_id}---")

    if service_id=="blog_generator":
        return "validation_node" #Start with validation
    
    return "get_model_ranking_node" #Default to social media flow

#---ROUTER 2: AFTER VALIDATION (FOR BLOGS)---
def after_validation_router(state: ExecutionState) -> str:
    """
    Checks the 'validation_result'.
    -'yes' -> Proceed to generate image
    -'no' -> END(and loop back in supervisor)
    """
    print("---EXEC ROUTER: After Validation---")
    validation_result=state.get("validation_result")

    if validation_result=="yes":
        return "get_model_ranking_node"
    
    else:
        print("---EXEC ROUTER: Validation FAILED. Ending subgraph to loop---")
        return END # This ends the sub graph

#---ROUTER 3: AFTER GENERATION(SHARED)---
def after_generation_router(state: ExecutionState) -> str:
    """
    Checks if generation was successful, If not, loop.
    If successful, pause to show user.
    """
    print("---EXEC ROUTER: After Generation---")

    if state.get("interaction_is_required"):
        print("---EXEC ROUTER: Pausing to show user.---")
        return END
    model_list=state.get("model_ranking",[])
    model_index=state.get("current_model_index",0)

    if model_index>=len(model_list):
        print("---EXEC ROUTER: All dynamic fallbacks failed. Ending---")
        return END
    else:
        print("---EXEC ROUTER: Generation failed, trying next model---")
        return "generate_image_node"


#---DEFINE the new graph---
workflow=StateGraph(ExecutionState)

#Add all our nodes
workflow.add_node("validation_node",validation_node)
workflow.add_node("get_model_ranking_node",get_model_ranking_node)
workflow.add_node("generate_image_node",generate_image_node)

#---Wire the graph---

#1. Entry point is a router
workflow.add_conditional_edges(
    START,
    execution_service_router,
    {
        "validation_node":"validation_node",
        "get_model_ranking_node":"get_model_ranking_node"
    }


)


#2. Blog FLow: After validation, use the validation router
workflow.add_conditional_edges(
    "validation_node",
    after_validation_router,
    {
        "get_model_ranking_node":"get_model_ranking_node",
        END:END
    }
)


#3. Social Media Flow: After ranking, go to generation
# Blog flow also joins here after validation

workflow.add_edge("get_model_ranking_node","generate_image_node")


#4.Shared flow :After generation use the generation router
workflow.add_conditional_edges(
    "generate_image_node",
    after_generation_router,
    {
        "generate_image_node":"generate_image_node", # Loop on failure
        END:END    # Pause on success or total failure
    }
)

#Complie the app
execution_agent_app=workflow.compile(checkpointer=execution_memory)

print("Execution Agent graph complied with VALIDATION LOOP logic.")