# from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.memory import MemorySaver
# from .state import PrepareState
# from .nodes import (
#     generate_stage_1_questions_node,
#     # 🔥 --- IMPORT OUR NEW NODE --- 🔥
#     classify_content_type_node,
#     generate_stage_2_questions_node,
#     format_payload_node
# )

# prepare_memory = MemorySaver()

# # --- Router 1: After Stage 1 (Unchanged logic, just routes to new node) ---
# def router_after_stage_1(state: PrepareState) -> str:
#     """
#     Decides where to go after Stage 1 node.
#     """
#     print("---PREPARE ROUTER: After Stage 1---")
    
#     questions = state.get("questions_for_user")
#     user_answers = state.get("user_answers")
    
#     # Check for errors first
#     if questions and questions[0].get("id") == "error":
#         print("---PREPARE ROUTER: Error generating Stage 1 questions, ending.---")
#         return END
    
#     # If questions exist, pause
#     if questions:
#         print("---PREPARE ROUTER: Pausing for Stage 1 questions.---")
#         return END  # Pause for user to answer
    
#     # If no questions AND we have answers, proceed to classify
#     if user_answers:
#         print("---PREPARE ROUTER: Stage 1 complete, proceeding to Classify Content---")
#         # 🔥 --- ROUTE TO NEW NODE --- 🔥
#         return "classify_content_type"
    
#     # Fallback
#     print("---PREPARE ROUTER: Stage 1 no questions/no answers, ending.---")
#     return END
    
# # --- 🔥 NEW: Router 2: After Classification --- 🔥
# def router_after_classification(state: PrepareState) -> str:
#     """
#     Checks classification and routes to Stage 2 questions.
#     """
#     print("---PREPARE ROUTER: After Classification---")
#     classification = state.get("content_classification")
    
#     if not classification or classification.get("type") == "Error":
#         print("---PREPARE ROUTER: Error during classification, ending.---")
#         return END
        
#     print(f"---PREPARE ROUTER: Classified as '{classification.get('type')}', proceeding to Stage 2 Questions.---")
#     return "generate_stage_2_questions"

# # --- Router 3: After Stage 2 (This was your old Router 2) ---
# def router_after_stage_2(state: PrepareState) -> str:
#     """
#     Decides where to go after Stage 2 node.
#     """
#     print("---PREPARE ROUTER: After Stage 2---")
    
#     questions = state.get("questions_for_user")
    
#     # Check for errors
#     if questions and questions[0].get("id") == "error":
#         print("---PREPARE ROUTER: Error generating Stage 2 questions, ending.---")
#         return END
    
#     # If questions exist, pause
#     if questions:
#         print("---PREPARE ROUTER: Pausing for Stage 2 questions.---")
#         return END  # Pause for user to answer
    
#     # No questions = Stage 2 complete, format payload
#     print("---PREPARE ROUTER: Stage 2 completed, proceeding to format payload---")
#     return "format_payload"

# # --- Define the graph ---
# workflow = StateGraph(PrepareState)

# # Add all the nodes, including the new one
# workflow.add_node("generate_stage_1_questions", generate_stage_1_questions_node)
# # 🔥 --- ADD NEW NODE --- 🔥
# workflow.add_node("classify_content_type", classify_content_type_node)
# workflow.add_node("generate_stage_2_questions", generate_stage_2_questions_node)
# workflow.add_node("format_payload", format_payload_node)

# # --- Define the edges ---
# workflow.set_entry_point("generate_stage_1_questions")

# # 1. After Stage 1, route to our new node or end
# workflow.add_conditional_edges("generate_stage_1_questions", router_after_stage_1, {
#     # 🔥 --- UPDATED EDGE --- 🔥
#     "classify_content_type": "classify_content_type",
#     END: END
# })

# # 2. 🔥 --- NEW EDGES for Classification --- 🔥
# workflow.add_conditional_edges("classify_content_type", router_after_classification, {
#     "generate_stage_2_questions": "generate_stage_2_questions",
#     END: END
# })

# # 3. After Stage 2, route to format payload or end
# workflow.add_conditional_edges("generate_stage_2_questions", router_after_stage_2, {
#     "format_payload": "format_payload",
#     END: END
# })

# # 4. Final step
# workflow.add_edge("format_payload", END)

# # Compile the graph
# prepare_agent_app = workflow.compile(checkpointer=prepare_memory)
# print("✅ Prepare Agent graph compiled with NEW CLASSIFICATION logic.")

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import PrepareState
from .nodes import (
    generate_stage_1_questions_node,
    # 🔥 --- IMPORT ALL OUR NODES --- 🔥
    classify_content_type_node,
    generate_confirmation_question_node,
    generate_stage_2_questions_node,
    format_payload_node
)

prepare_memory = MemorySaver()

# --- Router 1: After Stage 1 (Answers) ---
def router_after_stage_1(state: PrepareState) -> str:
    """
    Decides where to go after Stage 1 node.
    - If it generated questions, PAUSE.
    - If user submitted answers, check the service_id:
        - "blog_generator" -> SKIPS classification, goes to final questions
        - "social_media_post" (or default) -> proceeds to classification
    """
    print("---PREPARE ROUTER: After Stage 1---")
    
    questions = state.get("questions_for_user")
    user_answers = state.get("user_answers")
    
    # Check for errors first
    if questions and questions[0].get("id") == "error":
        print("---PREPARE ROUTER: Error generating Stage 1 questions, ending.---")
        return END
    
    # If questions were generated, pause for user to answer
    if questions:
        print("---PREPARE ROUTER: Pausing for Stage 1 questions.---")
        return END
    
    # If user submitted answers (no questions)
    if user_answers:
        # --- 🔥 THIS IS THE FIX --- 🔥
        service_id = state.get("service_info", {}).get("id")
        
        if service_id == "blog_generator":
            print(f"---PREPARE ROUTER: Service '{service_id}' detected. SKIPPING classification.")
            # Skip directly to the final question generation
            return "generate_stage_2_questions"
        else:
            # Default to the social media flow
            print(f"---PREPARE ROUTER: Service '{service_id}' detected. Proceeding to Classify Category---")
            return "classify_content_type"
        # --- 🔥 END OF FIX --- 🔥
    
    # Fallback in case something unexpected happens
    print("---PREPARE ROUTER: Stage 1 no questions/no answers, ending.---")
    return END
    
# --- Router 2: After Classification ---
def router_after_classification(state: PrepareState) -> str:
    """
    Checks classification and routes to build the "Golden Question".
    """
    print("---PREPARE ROUTER: After Classification---")
    classification = state.get("content_classification")
    
    if not classification or classification.get("category") == "Error":
        print("---PREPARE ROUTER: Error during classification, ending.---")
        return END
        
    print(f"---PREPARE ROUTER: Classified as '{classification.get('category')}', proceeding to build Golden Question.---")
    return "generate_confirmation_question" # <-- Go to new "golden question" node

# --- 🔥 NEW: Router 3: After Golden Question is GENERATED ---
def router_after_confirmation_gen(state: PrepareState) -> str:
    """
    Checks if the "Golden Question" was generated and pauses for the user.
    """
    print("---PREPARE ROUTER: After Golden Question Gen---")
    
    questions = state.get("questions_for_user")
    
    if questions and questions[0].get("id") == "error":
        print("---PREPARE ROUTER: Error building golden question, ending.---")
        return END
    
    # This is the whole point: pause for the user to answer the golden question
    if questions:
        print("---PREPARE ROUTER: Pausing for user to answer Golden Question.---")
        return END 
    
    # This should not happen, but good to have a fallback
    print("---PREPARE ROUTER: No golden question built, proceeding to final questions.---")
    return "generate_stage_2_questions"

# --- Router 4: After Stage 2 (Final Questions) ---
def router_after_stage_2(state: PrepareState) -> str:
    """
    Decides where to go after the FINAL questions node.
    - If it generated questions, PAUSE.
    - If no questions, proceed to FORMAT PAYLOAD.
    """
    print("---PREPARE ROUTER: After Final Questions (Stage 2)---")
    
    questions = state.get("questions_for_user")
    
    if questions and questions[0].get("id") == "error":
        print("---PREPARE ROUTER: Error generating Stage 2 questions, ending.---")
        return END
    
    if questions:
        print("---PREPARE ROUTER: Pausing for Stage 2 (final) questions.---")
        return END  # Pause for user to answer
    
    print("---PREPARE ROUTER: Stage 2 complete, proceeding to format payload---")
    return "format_payload"

# --- Define the graph ---
workflow = StateGraph(PrepareState)

# Add all the nodes in order
workflow.add_node("generate_stage_1_questions", generate_stage_1_questions_node)
workflow.add_node("classify_content_type", classify_content_type_node)
workflow.add_node("generate_confirmation_question", generate_confirmation_question_node)
workflow.add_node("generate_stage_2_questions", generate_stage_2_questions_node)
workflow.add_node("format_payload", format_payload_node)

# --- Define the edges (The new flow) ---
workflow.set_entry_point("generate_stage_1_questions")

# 1. After Stage 1 (questions or answers)
workflow.add_conditional_edges("generate_stage_1_questions", router_after_stage_1, {
    "classify_content_type": "classify_content_type",         # Path for Social Media
    "generate_stage_2_questions": "generate_stage_2_questions", # 🔥 Path for Blog
    END: END                                                # Path for pausing
})

# 2. After Classification
workflow.add_conditional_edges("classify_content_type", router_after_classification, {
    "generate_confirmation_question": "generate_confirmation_question",
    END: END
})

# 3. After Golden Question is GENERATED (this node *creates* questions)
workflow.add_conditional_edges("generate_confirmation_question", router_after_confirmation_gen, {
    "generate_stage_2_questions": "generate_stage_2_questions",
    END: END # <-- This is the main pause
})

# 4. After Final Questions are GENERATED (this node also *creates* questions)
workflow.add_conditional_edges("generate_stage_2_questions", router_after_stage_2, {
    "format_payload": "format_payload",
    END: END # <-- This is the second main pause
})

# 5. Final step
workflow.add_edge("format_payload", END)

# Compile the graph
prepare_agent_app = workflow.compile(checkpointer=prepare_memory)
print("✅ Prepare Agent graph compiled with NEW 3-STEP (HITL) CLASSIFICATION logic.")