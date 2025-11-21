# app/supervisor/nodes.py
import json
from pathlib import Path
from typing import List, Dict, Any
from .state import AgentState
from app.agents.planning.graph import planning_agent_app
from app.agents.preparing.graph import prepare_agent_app
from app.agents.processing.graph import processing_agent_app
from app.agents.execution.graph import execution_agent_app
from langgraph.graph import END

# --- determine_service_entrypoint_node (No changes) ---
def determine_service_entrypoint_node(state: AgentState) -> dict:
    print("---SUPERVISOR NODE: Determining Service Entrypoint---")
    user_request=state['initial_request']
    service_id=user_request.get('service_id')
    registry_path=Path(__file__).parents[1] / "core/app_registry.json"
    with open(registry_path,'r') as f:
        registry=json.load(f)
    service_info=next((s for s in registry['services'] if s['id']==service_id),None)
    if not service_info:
        print(f" SUPERVISOR ERROR: Service with ID '{service_id}' not found in registry.")
        return {'service_info':{"error":"Service not found"}}
    print(f"Service '{service_id}' found. Mode :{service_info.get('plan_mode')}")
    return {'service_info':service_info}

# --- run_planning_agent_node (No changes) ---
async def run_planning_agent_node(state:AgentState):
    print("---SUPERVISOR NODE:Invoking Planning Agent(Async)---")
    service_info=state['service_info']
    if "error" in service_info:
        return {"action_plan":{"error":"Failed to proceed, service info is missing."}}
    planning_config={"configurable":{"thread_id":state['thread_id']}}
    planning_input={ "service_info": service_info }
    last_planner_output=None
    async for event in planning_agent_app.astream(planning_input,config=planning_config):
        print(f"SUPERVISOR DEBUG EVENT:{event}")
        if "planner" in event:
            last_planner_output=event['planner']
            print(f"Supervisor captured planner output {last_planner_output}")
    if last_planner_output and "action_plan" in last_planner_output:
        plan=last_planner_output['action_plan']
        if "error" in plan:
            print(f"planner returned an error:{plan['error']}")
            return {'action_plan':plan,'interaction_is_required':False}
        print("Supervisor recevied a valid action plan. Signaling PAUSE to show user.")
        return{
            "action_plan":plan,
            "interaction_is_required":True
        }
    else:
        print("No valid action plan recevied from planner!")
        return {'action_plan':{'error':'Failed to generate a plan.'}}


# # --- 🔥 THE FINAL, CORRECT BRIDGE NODE with MANUAL MERGE ---
async def run_prepare_agent_node(state: AgentState):
    print("---SUPERVISOR NODE: Invoking Prepare Agent (Async)---")
    
    # ... (all the setup logic is the same) ...
    print(f"---NODE DEBUG: Data received from AgentState: {state.get('user_answers')} ---")
    action_plan = state.get("action_plan", {})
    full_prepare_steps = action_plan.get("prepare_agent", [])
    new_user_answers = state.get("user_answers") 

    if not full_prepare_steps:
        print("❌ SUPERVISOR ERROR: No 'prepare_agent' steps found.")
        return {
            "generation_payload": {"error": "No prepare steps in plan."},
            "prepare_complete": True
        }

    prepare_thread_id = f"{state['thread_id']}_prepare"
    prepare_config = {"configurable": {"thread_id": prepare_thread_id}}

    prepare_state = await prepare_agent_app.aget_state(prepare_config)
    
    if prepare_state.values:
        # This is a RESUME call (Stage 2, 3, etc.)
        print(f"---SUPERVISOR NODE: Resuming Prepare Agent---")
        
        # ... (manual merge logic is the same) ...
        old_answers = prepare_state.values.get("user_answers") or {}
        if new_user_answers:
             old_answers.update(new_user_answers)
        merged_answers = old_answers
        
        print(f"---SUPERVISOR BRIDGE: Manually merged answers: {merged_answers}---")

        await prepare_agent_app.aupdate_state(
            prepare_config,
            {
                "user_answers": merged_answers, 
                "questions_for_user": None  # Clear questions to proceed
            }
        )
        
        prepare_input = None
    else:
        # This is the FIRST call (Stage 1)
        print(f"---SUPERVISOR NODE: First call to Prepare Agent, passing Stage 1 steps---")
        stage_1_steps = [step for step in full_prepare_steps if step.get("stage") == 1]
        
        if not stage_1_steps:
            print("❌ SUPERVISOR ERROR: No Stage 1 steps found.")
            return {
                "generation_payload": {"error": "Missing Stage 1 plan steps."},
                "prepare_complete": True
            }
        
        prepare_input = {
            "action_plan_stage_1_steps": stage_1_steps,
            "user_answers": new_user_answers, 
            "service_info":state.get("service_info")
        }
    
    # --- THIS IS THE UPDATED LOOP ---
    
    async for event in prepare_agent_app.astream(prepare_input, config=prepare_config):
        event_str = str(event)
        print(f"🔍 PREPARE SUB-GRAPH EVENT: {event_str[:500]}...")

        # --- Check for Stage 1 or Stage 2 Questions ---
        if "generate_stage_1_questions" in event or "generate_stage_2_questions" in event:
            node_output = event.get("generate_stage_1_questions") or event.get("generate_stage_2_questions")
            
            # (This logic is for both nodes)
            if node_output and node_output.get("questions_for_user") and node_output["questions_for_user"][0].get("id") != "error":
                print("✅ Prepare Agent generated questions. Pausing Supervisor.")
                return {
                    "questions_for_user": node_output["questions_for_user"],
                    "interaction_is_required": True,
                    "prepare_complete": False
                }
            elif node_output and node_output.get("questions_for_user") and node_output["questions_for_user"][0].get("id") == "error":
                print("❌ Prepare Agent failed to generate questions.")
                error_text = node_output["questions_for_user"][0].get("text", "Unknown error")
                return {
                    "generation_payload": {"error": error_text},
                    "interaction_is_required": False,
                    "prepare_complete": True
                }

        # --- 🔥 THIS IS THE MISSING BLOCK OF CODE --- 🔥
        # --- Check for our new "Golden Question" node ---
        if "generate_confirmation_question" in event:
            node_output = event.get("generate_confirmation_question")
            if node_output and node_output.get("questions_for_user"):
                print("✅ Prepare Agent paused to show 'Golden Question'. Pausing Supervisor.")
                return {
                    "questions_for_user": node_output["questions_for_user"],
                    "interaction_is_required": True,
                    "prepare_complete": False # Not done yet
                }
        # --- 🔥 END OF FIX --- 🔥

    # --- (This final state logic is unchanged and correct) ---
    print("🏁 Prepare Agent sub-graph finished. Getting final state.")
    final_prepare_state = await prepare_agent_app.aget_state(prepare_config)
    final_prepare_output = final_prepare_state.values

    if final_prepare_output and final_prepare_output.get("prepare_complete") is True:
        print("✅ Prepare Agent finished successfully. Passing payload.")
        return {
            "generation_payload": final_prepare_output.get("generation_payload"),
            "interaction_is_required": False,
            "questions_for_user": None,
            "prepare_complete": True
        }
    else:
        print(f"⚠️ Prepare Agent finished unexpectedly (post-stream check). Final output: {final_prepare_output}")
        return {
            "generation_payload": {"error": "Prepare agent failed unexpectedly."},
            "interaction_is_required": False,
            "prepare_complete": True
        }

async def run_processing_agent_node(state: AgentState) -> dict:
    """
    Bridge to the Processing Agent.
    It now passes the critique and failed draft it they exist.
    """
    print("---SUPERVISOR NODE:Invoking Processing Agent (Async)---")

    # 🔥 --- THIS IS THE FIX --- 🔥
    # The payload from prepare_agent is {'user_inputs': {...}, 'classification': ...}
    # We need to unwrap the 'user_inputs' for the processing tools.
    nested_payload = state.get("generation_payload")
    
    if not nested_payload or not nested_payload.get("user_inputs"):
        print("SUPERVISOR ERROR:No generation_payload.user_inputs found.")
        return {
            "image_prompts":["Error: No payload provided to processing agent."],
            "draft_caption":"Error:No payload."
        }
        
    # This is the actual data the tools need
    payload_to_pass = nested_payload.get("user_inputs")
    # 🔥 --- END OF FIX --- 🔥
    
    critique = state.get("critique")
    
    #Use a stable thread_id for the sub-graph
    processing_thread_id = f"{state['thread_id']}_processing"
    processing_config = {"configurable": {"thread_id": processing_thread_id}}

    # We use ainvoke (not astream) since it doesn't pause
    processing_input = {
        "generation_payload": payload_to_pass, # <-- Pass the UNWRAPPED payload
        "service_info": state.get('service_info'),
        "critique": critique,
        "blog_draft": state.get("blog_draft"),
        "draft_caption": state.get("draft_caption"),
        "cover_image_prompt": state.get("cover_image_prompt")
    }

    if critique:
        print("---SUPERVISOR BRIDGE: Sending critique to Processing Agent for refinement.---")

    try:
        # We use ainvoke to run the sub-graph start to finish in one go
        final_processing_state = await processing_agent_app.ainvoke(
            processing_input,
            config=processing_config
        )

        # The output of ainvoke is the final state of the sub-graph
        if final_processing_state:
            print("Processing Agent finished successfully.")
            # We also need to grab the classification from the *original* payload
            # so we can save it to the final state
            classification = nested_payload.get("classification")
            
            return {
                "image_prompts": final_processing_state.get("image_prompts"),
                "draft_caption": final_processing_state.get("draft_caption"),
                "blog_draft": final_processing_state.get("blog_draft"),
                "cover_image_prompt": final_processing_state.get("cover_image_prompt"),
                "interaction_is_required": True,
                "critique": None, #clear the critique after retirement
                "classification": classification # <-- Pass this along
            }
        else:
            raise Exception("Processing Agent returned no final state.")
        
    except Exception as e:
        print(f"SUPERVISOR ERROR: Processing Agent failed:{e}")
        return {
            "image_prompts": [f"Error:{e}"],
            "draft_caption": f"Error:{e}",
            "blog_draft": f"Error: {e}" # <-- Make sure to pass the error here too
        }

# --- 🔥 HERE IS THE FIX ---
async def run_execution_agent_node(state: AgentState) -> dict:
    """
    Bridge to the Execution Agent.
    """
    print("---SUPERVISOR NODE: Invoking Execution Agent (Async)---")
    
    # Get the FULL user_answers dict
    user_answers = state.get("user_answers", {})

    # Get all the inputs for the execution agent
    exec_input = {
        "generation_payload":state.get("generation_payload"),
        "service_info":state.get("service_info"), #Pass this for routing

        #Social Media Flow
        "image_prompts":state.get("image_prompts"),
        "selected_prompt":user_answers.get("selected_prompt"),
        "num_images":user_answers.get("num_images"),

        #Blog Flow
        "blog_draft":state.get("blog_draft"),
        "cover_image_prompt":state.get("cover_image_prompt"),
        "draft_caption":user_answers.get("draft_caption"),
    }

    # 🔥 --- LUSH DEBUG STATEMENT (AS REQUESTED) --- 🔥
    print("---SUPERVISOR DEBUG: Input being passed to Execution Agent: ---")
    # Use json.dumps for a clean print of the dict, handling None
    print(json.dumps(
        exec_input, 
        indent=2, 
        default=str  # Handle any non-serializable objects
    ))
    # 🔥 --- END DEBUG --- 🔥
    
    # Use a stable thread_id for the sub-graph
    exec_thread_id = f"{state['thread_id']}_execution"
    exec_config = {"configurable": {"thread_id": exec_thread_id}}

    # We use astream because the execution agent *will pause*
    async for event in execution_agent_app.astream(exec_input, config=exec_config):
        event_str = str(event)
        print(f"🔍 EXEC SUB-GRAPH EVENT: {event_str[:500]}...")


        #Check for the validation node (for blogs)
        if "validation_node" in event:
            node_output=event['validation_node']
            if node_output.get("validation_result")=="no":
                print("Exec Agent Validation FAILED.Ending.")
                #Return the failure, the router will catch this
                return {
                    "validation_result":"no",
                    "critique":node_output.get("critique"),
                    "interaction_is_required": True
                }
        
        if "generate_image_node" in event:
            node_output = event["generate_image_node"]
            if node_output.get("interaction_is_required"):
                print("✅ Exec Agent generated image(s). Pausing Supervisor.")
                return {
                    "current_images_base64": node_output.get("current_images_base64"),
                    "blog_draft":state.get("blog_draft"),
                    "cover_image_prompt":state.get("cover_image_prompt"),
                    "draft_caption":state.get("draft_caption"),
                    
                    "interaction_is_required": True,
                    "validation_result":"yes", # must have passed to get here
                    "current_error": None
                }
            elif node_output.get("current_error"):
                print(f"⚠️ Exec Agent error, will try next model: {node_output.get('current_error')}")
                
    # If the stream finishes, all fallbacks failed.
    print("🏁 Execution Agent sub-graph finished (all fallbacks failed).")
    final_exec_state = await execution_agent_app.aget_state(exec_config)
    return {
        "current_images_base64": None,
        "interaction_is_required": False,
        "validation_result":final_exec_state.values.get("validation_result","no"),
        "critique":final_exec_state.values.get("critique"),
        "current_error": final_exec_state.values.get("current_error", "All fallbacks failed.")
    }

#--- NEW: Handle FAILURE NODE---
def handle_failure_node(state: AgentState)-> dict:
    """
    Manages the retry loop for validation failures.
    Increments the retry count and clears the validation fields.
    """
    print("---SUPERVISOR NODE: Handlint Validation Failure---")

    current_count=state.get("retry_count",0)
    new_count=current_count +1

    print(f"---SUPERVISOR NODE: Retry attempt {new_count}---")

    return {
        "retry_count":new_count,
        #Clear the validation fields so we don't get stuck
        "validation_result":None,
        #let's clear critique from the root state
        # "critique":None
    }