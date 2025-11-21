from langgraph.graph import StateGraph,END,START
from langgraph.checkpoint.memory import MemorySaver
from .state import ProcessingState
from .nodes import run_creative_generation_node,run_blog_package_node

#Set up its own memory
processing_memory=MemorySaver()


#---NEW : The Router Function ----
def service_router(state: ProcessingState) -> str:
    """
    Reads the service_info and routes to the correct node.
    """
    service_id= state.get("service_info",{}).get("id")
    print(f"---PROCESS ROUTER: Routing based on service_id: {service_id}---")

    if service_id=="blog_generator":
        return "run_blog_package_node"
    
    #Default to social media post
    return "run_creative_generation_node"

#Define the graph
workflow=StateGraph(ProcessingState)

#Add our two brain nodes
workflow.add_node("run_creative_generation_node",run_creative_generation_node)
workflow.add_node("run_blog_package_node",run_blog_package_node)

#The graph entry point now is a conditonal router
workflow.add_conditional_edges(
    START,
    service_router,
    {
        "run_creative_generation_node":"run_creative_generation_node",
        "run_blog_package_node":"run_blog_package_node"
    }
)

#All brain nodes just go to the end
workflow.add_edge("run_creative_generation_node",END)
workflow.add_edge("run_blog_package_node",END)


#Complie the app
processing_agent_app=workflow.compile(checkpointer=processing_memory)

print("Processing Agent Graph complied with SERVICE ROUTER logic.")