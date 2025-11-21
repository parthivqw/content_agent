from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import PlanningState
from .nodes import planning_conversation_node

# Each sub-graph gets its own memory for state persistence
planning_memory = MemorySaver()

# Define the state machine for the planning agent
workflow = StateGraph(PlanningState)

# The planner has only one job: to run the planning node.
workflow.add_node("planner", planning_conversation_node)

# The workflow starts and ends with the planner node.
workflow.set_entry_point("planner")
workflow.add_edge("planner", END)

# Compile the graph into a runnable application, with memory
planning_agent_app = workflow.compile(checkpointer=planning_memory)

print("✅ Planning Agent graph compiled with checkpointing.")