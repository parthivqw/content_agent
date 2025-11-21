
import re
from typing import List,Dict,Any, Optional
from .state import PrepareState
from app.tools.llm_tools import generate_dynamic_questions_tool,generate_follow_up_questions_tool,classify_content_type_tool,MASTER_CONTENT_TYPE_LIST

#---Node 1: Generate Stage 1 questions---
def generate_stage_1_questions_node(state:PrepareState)-> dict:
    """
    Generates the initial context-gathering questions based on Stage 1 plan steps.
    """
    print("---PREPARE AGENT:Generating Stage 1 Questions Node---")
    
    #Only run if no answers exist yet (prevent re-running if looping back unexpectedly)
    if state.get("user_answers"):
        print("---PREPARE AGENT:Stage 1 answers already exists, skipping Stage 1 question generation.---")
        #Returning empty dict allows the router to check user_answers and proceed
        return {"questions_for_user":None,"stage_1_complete":True}
    #Get Stage 1 steps from input
    plan_steps=state.get("action_plan_stage_1_steps",[])
    if not plan_steps:
        print("---PREPARE AGENT:ERROR -No Stage 1 plan steps provided.---")
        return {"questions_for_user":[{"id":"error","text":"Missing Stage 1 plan.","ui_element":"text"}]}
    
    print(f"---PREPARE AGENT:Stage 1 Requirements: {[s['step_description'] for s in plan_steps]}---")

    #Call the exisiting tool to generate questions based on Stage 1 steps
    # We pass the steps themselves so the tool can extract keys needed
    question_json=generate_dynamic_questions_tool(
        plan_steps_for_stage=plan_steps,
        data_requirements=[step['step_description'] for step in plan_steps],
        previous_answers=None # No context on the first run
    )
    questions=question_json.get("questions")

    if not questions or questions[0].get("id")=="error":
        error_text=questions[0].get("text") if questions else "Failed to generated Stage 1 questions."
        print(f"---PREPARE AGENT:ERROR -{error_text}---")
        return {"questions_for_user":[{"id":"error","text":error_text,"ui_element":"text"}]}
    print(f"---PREPARE AGENT:Generated {len(questions)} Stage 1 questions.---")

    #Return questions to ask the usetr
    return{
        "questions_for_user":questions,
        "stage_1_complete":False #Mark stage 1 as not yet complete

    }


#---NEW:  Node 2: Classify content type---
def classify_content_type_node(state: PrepareState) -> dict:
    """
    Calls the "classifier" tool to analyze Stage 1 anaswers and determine
    the specifiv content type the user wants to build.

    """
    print("---PREPARE AGENT: Classifying Content Type Node---")
    user_answers=state.get("user_answers")

    if not user_answers:
        print("---PREPARE AGENT: ERROR- No answers found to classify.---")
        return {
            "content_classification":{
                "type":"Error",
                "category":"Error",
                "reasoning":"Missing user_answers in state."
            }
        }
    
    #Calls our new brain tool
    # We pass the full service_info so the tool can find the rules
    classification_data=classify_content_type_tool(
        context=user_answers
    )

    print(f"----PREPARE AGENT: Classification result:{classification_data.get('classification')}---")

    #Save the classification data to the state
    return {
        "content_classification":classification_data.get("classification")
    }

#---NEW: Helper function to parse the master list---
def _parse_options_for_category(category: str) -> List[str]:
    """
    Parses the MASTER_CONTENT_TYPE_LIST string to find the
    sub-items for a given category.
    """
    print(f"---HELPER:Parsing options for category:{category}")
    try:
        #Escape the category string for regex and find it
        pattern=re.escape(category) + r'\s*\n(.*?)(?=\n[A-H]\.|\Z)'
        match=re.search(pattern,MASTER_CONTENT_TYPE_LIST,re.DOTALL | re.MULTILINE)

        if not match:
            print(f"---HELPER: No match found for {category}")
        
        # Extract the block of text under the category
        items_block = match.group(1)
        
        # Find all lines starting with " - "
        options = re.findall(r'^\s*-\s*(.*?)\s*$', items_block, re.MULTILINE)
        
        if not options:
            print("---HELPER: No sub-items found, returning Other")
            return ["Other"]
            
        print(f"---HELPER: Found options: {options}")
        return options
        
    except Exception as e:
        print(f"---HELPER: Error parsing list: {e}")
        return ["Other"] # Fallback

# ---NEW Node 3: generate confirmation question---
def generate_confirmation_question_node(state: PrepareState) -> dict:
    """
    NON-LLM
    Reads the classified category and generates the golden question
    for the user to confirm the specific content type.
    """
    print("---PREPARE AGENT: Generating Confirmation Question Node---")
    classification=state.get("content_classification")

    if not classification or classification.get("category")=="Error":
        print("---PREPARE AGENT: ERROR -No category found, cannot build question.")
        #This is a  fallback in case of error
        return {
            "questions_for_user":[{
                "id":"error",
                "type":"textarea",
                "label":"Error:Could not classify content.Please describe what you want to build."
            }],
            "interaction_is_required":True,
            "stage_1_complete":True #Mark as complete to move on
        }
    category_name=classification.get("category")

    #Use our helper to get the list of options
    options=_parse_options_for_category(category_name)

    #Add Other if it's already there
    if "Other" not in options:
        options.append("Other")

    # Build the golden question
    golden_question={
        "id":"confirmed_content_type", # This is the key we'll look for
        "type":"radio",
        "label":f"It looks like you're making  a '{category_name.split('. ')[1]}'.Which specific type are you building.",
        "options":options
    }

    print("---PREPARE AGENT: Pausing for user to confirm content type.")

    #Return the question to pause the graph
    return {
        "questions_for_user":[golden_question],
        "interaction_is_required":True, #Signals the supervisor to stop
        "stage_1_complete": True # we are done with stage 1 
    }

        
        

# --- 🔥 REPLACED: Node 4: Generate Stage 2 Questions (Final Version) ---
# def generate_stage_2_questions_node(state: PrepareState) -> dict:
#     """
#     Generates the FINAL follow-up questions based on the user's
#     *CONFIRMED* content type.
#     """
#     print("---PREPARE AGENT: Generating FINAL Stage 2 Questions Node---")

#     # Get the user's final answer to our "golden question"
#     user_answers = state.get("user_answers", {})
#     confirmed_type = user_answers.get("confirmed_content_type")

#     # Get other state items
#     service_info = state.get("service_info")

#     if not confirmed_type:
#         print("---PREPARE AGENT: ERROR - User's confirmed_content_type not found.")
#         return {"questions_for_user": [{"id": "error", "text": "Missing context for Stage 2.", "ui_element": "text"}]}

#     print(f"---PREPARE AGENT: User confirmed type: {confirmed_type}---")

#     # Call the LLM tool. Its prompt will now be super-focused.
#     # We pass the *confirmed_type* as the new classification.
#     question_json = generate_follow_up_questions_tool(
#         context=user_answers,
#         service_info=service_info,
#         # 🔥 --- THE KEY CHANGE --- 🔥
#         # We pass the *confirmed* type, not the *guessed* category
#         classification={"type": confirmed_type, "category": "User Confirmed"}
#     )

#     questions = question_json.get("questions")

#     if not questions or questions[0].get("id") == "error":
#         error_text = questions[0].get("text") if questions else "Failed to generate Stage 2 questions."
#         print(f"---PREPARE AGENT: ERROR - {error_text} ---")
#         return {"questions_for_user": [{"id": "error", "text": error_text, "ui_element": "text"}]}

#     # Check if the LLM decided no more questions are needed
#     if not questions:
#          print(f"---PREPARE AGENT: LLM determined no Stage 2 questions needed for {confirmed_type}.---")
#          return {"questions_for_user": None} # Signal completion

#     print(f"---PREPARE AGENT: Generated {len(questions)} final questions.---")
    
#     # We return a dict, not just update a var, to set the state
#     return {"questions_for_user": questions}

# --- 🔥 REPLACED: Node 4: Generate Stage 2 Questions (SERVICE AWARE) ---
def generate_stage_2_questions_node(state: PrepareState) -> dict:
    """
    Generates the FINAL follow-up questions.
    - For 'social_media_post', it uses the 'confirmed_content_type'.
    - For 'blog_generator', it uses a generic 'Blog Post' type.
    """
    print("---PREPARE AGENT: Generating FINAL Stage 2 Questions Node---")

    user_answers = state.get("user_answers", {})
    service_info = state.get("service_info")
    service_id = service_info.get("id") if service_info else None
    
    classification_to_pass = None

    # --- 🔥 THIS IS THE NEW LOGIC --- 🔥
    if service_id == "blog_generator":
        print("---PREPARE AGENT: Blog flow. Using 'Blog Post' classification.")
        # We manually create the classification the tool is expecting
        classification_to_pass = {"type": "Blog Post", "category": "Blog"}
    
    elif service_id == "social_media_post":
        confirmed_type = user_answers.get("confirmed_content_type")
        if not confirmed_type:
            print("---PREPARE AGENT: ERROR - Social media flow missing 'confirmed_content_type'.")
            return {"questions_for_user": [{"id": "error", "text": "Missing content type confirmation.", "ui_element": "text"}]}
        
        print(f"---PREPARE AGENT: Social media flow. User confirmed type: {confirmed_type}---")
        classification_to_pass = {"type": confirmed_type, "category": "User Confirmed"}
    
    else:
        # Fallback for unknown services
        print(f"---PREPARE AGENT: ERROR - Unknown service_id: {service_id}")
        return {"questions_for_user": [{"id": "error", "text": f"Unknown service: {service_id}", "ui_element": "text"}]}
    # --- 🔥 END OF NEW LOGIC --- 🔥


    # Call the LLM tool with the correct classification
    question_json = generate_follow_up_questions_tool(
        context=user_answers,
        service_info=service_info,
        classification=classification_to_pass # Pass the correct classification
    )

    questions = question_json.get("questions")

    if not questions or questions[0].get("id") == "error":
        error_text = questions[0].get("text") if questions else "Failed to generate Stage 2 questions."
        print(f"---PREPARE AGENT: ERROR - {error_text} ---")
        return {"questions_for_user": [{"id": "error", "text": error_text, "ui_element": "text"}]}

    if not questions:
         print(f"---PREPARE AGENT: LLM determined no Stage 2 questions needed for {classification_to_pass.get('type')}.---")
         return {"questions_for_user": None} # Signal completion

    print(f"---PREPARE AGENT: Generated {len(questions)} final questions.---")
    
    return {"questions_for_user": questions}



# --- Node 5: Format Final Payload (Unchanged) ---
def format_payload_node(state: PrepareState) -> dict:
    """
    Takes the final user_answers and formats them as the generation_payload
    """
    print("---PREPARE AGENT: Formatting Final Payload---")
    final_answers=state.get("user_answers",{})
    print(f"---PREPARE AGENT: Final combined answers: {final_answers}---")

    #---FUTURE PROOFING---
    final_payload={
        "user_inputs":final_answers,
        "classification":state.get("content_classification")
    }

    return {"generation_payload":final_payload,"prepare_complete":True}