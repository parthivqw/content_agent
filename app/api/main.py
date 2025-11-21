
# import uuid
# import json 
# import copy # Import copy
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.supervisor.state import update_dict 
# from .models import GenerateRequest, ContinueRequest, ApiResponse
# from app.supervisor.graph import supervisor_app

# app = FastAPI(title="Content Creation Agentic System")
# app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
#                    allow_methods=["*"], allow_headers=["*"])

# # --- 🔥 NEW: Log Cleaner ---
# def clean_log_event(event_dict):
#     """Cleans up the event for logging by truncating base64 strings."""
#     if not isinstance(event_dict, dict):
#         return str(event_dict)

#     # Create a deep copy to avoid modifying the original event
#     log_event = copy.deepcopy(event_dict) 
    
#     try:
#         # Check all nodes in the event
#         for node_name, node_output in log_event.items():
#             if isinstance(node_output, dict):
#                 # Check for the base64 key
#                 if "current_images_base64" in node_output and node_output["current_images_base64"]:
#                     # Truncate the log output
#                     count = len(node_output["current_images_base64"])
#                     node_output["current_images_base64"] = f"[TRUNCATED: {count} base64 image(s)]"
                
#                 # Check for blog draft
#                 if "blog_draft" in node_output and node_output["blog_draft"]:
#                     draft = node_output["blog_draft"]
#                     if isinstance(draft, str):
#                         node_output["blog_draft"] = f"[TRUNCATED: Blog draft, {len(draft)} chars]"

#         return json.dumps(log_event, indent=2)
#     except Exception as e:
#         # Fallback in case of any error
#         return f"[Error cleaning log: {e}] | Original: {str(log_event)[:500]}..."
# # --- END Log Cleaner ---

# @app.get("/")
# def read_root():
#     return {"status": "ok"}

# @app.post("/generate", response_model=ApiResponse)
# async def generate(request: GenerateRequest):
#     thread_id = str(uuid.uuid4())
#     config = {"configurable": {"thread_id": thread_id}}
#     print(f"---API: New session started. Thread ID: {thread_id}---")
    
#     initial_input = {
#         "initial_request": {"service_id": request.service_id},
#         "thread_id": thread_id,
#          # 🔥 NEW: Initialize retry count
#         "retry_count": 0
#     }
    
#     # This loop handles the FIRST pause (plan or initial questions)
#     async for event in supervisor_app.astream(initial_input, config=config):
        
#         # Use the new log cleaner
#         print(f"📡 Stream event:\n{clean_log_event(event)}")
        
#         if "planning_agent" in event:
#             node_output = event["planning_agent"]
#             print(f"🔍 DEBUG: planning_agent output: {node_output}")
            
#             if node_output.get("interaction_is_required") and node_output.get("action_plan"):
#                 print(f"⏸️ Graph paused to show action plan. Thread ID: {thread_id}")
#                 return ApiResponse(
#                     status="requires_input",
#                     thread_id=thread_id,
#                     data={"action_plan": node_output.get("action_plan")}
#                 )

#         if "prepare_agent" in event:
#             node_output = event["prepare_agent"]
#             print(f"🔍 DEBUG: prepare_agent output: {node_output}")

#             if node_output.get("interaction_is_required") and node_output.get("questions_for_user"):
#                 print(f"⏸️ Graph paused to ask questions. Thread ID: {thread_id}")
#                 return ApiResponse(
#                     status="requires_input",
#                     thread_id=thread_id,
#                     data={"questions_for_user": node_output.get("questions_for_user")}
#                 )

#     # This should only be hit if the graph runs all the way through without pausing
#     final_state = await supervisor_app.aget_state(config)
#     print(f"✅ Workflow finished unexpectedly in /generate. Final state: {final_state.values}")
#     return ApiResponse(status="success", thread_id=thread_id, data=final_state.values)


# @app.post("/continue", response_model=ApiResponse)
# async def continue_workflow(request: ContinueRequest):
#     thread_id = request.thread_id
#     config = {"configurable": {"thread_id": thread_id}}
#     print(f"---API: Continuing session for Thread ID: {thread_id}---")
#     print(f"---API: Continue type: {request.continue_type}---")
    
#     # --- 1. UPDATE STATE BASED ON CONTINUE TYPE ---
    
#     if request.continue_type == "plan_approval":
#         print("---API: Plan approved by user---")
#         await supervisor_app.aupdate_state(
#             config,
#             {"interaction_is_required": False}
#         )
        
#     elif request.continue_type == "answer":
#         print(f"---API: User submitted answers---")
#         if not request.user_answers:
#             return ApiResponse(status="error", thread_id=thread_id, data={"error": "user_answers required for type 'answer'"})
        
#         print(f"---API DEBUG: DATA RECEIVED FROM FRONTEND ---")
#         print(f"---API DEBUG: request.user_answers: {request.user_answers} ---")
        
#         # We update the state here, and the reducer in AgentState merges the dicts
#         await supervisor_app.aupdate_state(
#             config,
#             {
#                 "user_answers": request.user_answers,
#                 "interaction_is_required": False
#             }
#         )
        
#     elif request.continue_type == "execution":
#         print(f"---API: User submitted prompt for execution (Social Media)---")

#          # 🔥 --- LUSH DEBUG STATEMENT --- 🔥
#         print(f"---API DEBUG: PAYLOAD RECEIVED FOR EXECUTION ---")
#         print(f"---API DEBUG: request.user_answers: {request.user_answers} ---")

#         if not request.user_answers or not request.user_answers.get("selected_prompt"):
#              return ApiResponse(status="error", thread_id=thread_id, data={"error": "selected_prompt is required"})
        
#         # Merge the new 'selected_prompt' and 'num_images'
#         await supervisor_app.aupdate_state(
#             config,
#             {
#                 "user_answers": request.user_answers, # This will merge the new keys
#                 "selected_prompt":request.user_answers.get("selected_prompt"), # Hoist to the top level
#                 "num_images":request.user_answers.get("num_images"), # Hoist to top level 
#                 "interaction_is_required": False
#             }
#         )
    
#     elif request.continue_type == "blog_approval":
#         print(f"---API: Blog package approved by user---")
        
#         # Get the full state to pass the failed draft info
#         full_state = await supervisor_app.aget_state(config)

#         # We just need to un-pause the supervisor.
#         # The state already has all the info from the processing agent.
#         await supervisor_app.aupdate_state(
#             config,
#             {
#                 "interaction_is_required": False,
#                 # 🔥 Pass the critique back in for the refinement loop
#                 # This check is for when the *user* rejects it (future)
#                 "critique": request.user_answers.get("critique") if request.user_answers else None,
#                 # Pass the *current* drafts
#                 "blog_draft": full_state.values.get("blog_draft"),
#                 "draft_caption": full_state.values.get("draft_caption"),
#                 "cover_image_prompt": full_state.values.get("cover_image_prompt"),
#             }
#         )
        
#     else:
#          return ApiResponse(status="error", thread_id=thread_id, data={"error": f"Invalid continue_type: {request.continue_type}"})
    
    
#     # --- 2. RUN THE GRAPH STREAM TO GET THE *NEXT* PAUSE ---
    
#     # 🔥 --- BUG 2 FIX: Add a flag to skip only the FIRST stale event ---
#     has_skipped_stale_event = False
    
#     async for event in supervisor_app.astream(None, config=config):
        
#         # Use the new log cleaner
#         print(f"📡 Stream event:\n{clean_log_event(event)}")

#         # Pause for more questions from prepare_agent
#         if "prepare_agent" in event:
#             node_output = event["prepare_agent"]
#             if node_output.get("interaction_is_required") and node_output.get("questions_for_user"):
#                 print(f"⏸️ Graph paused to ask questions. Thread ID: {thread_id}")
#                 return ApiResponse(
#                     status="requires_input",
#                     thread_id=thread_id,
#                     data={"questions_for_user": node_output.get("questions_for_user")}
#                 )
        
#         if "processing_agent" in event:
#             # --- 🔥 BUG 2 FIX: Use the flag ---
#             # Check if we are resuming FROM this pause. If so, ignore this *one* stale event.
#             if request.continue_type in ["execution", "blog_approval"] and not has_skipped_stale_event:
#                 print(f"---API: Ignoring stale 'processing_agent' event on resume (Type: {request.continue_type}). Waiting for next node...---")
#                 has_skipped_stale_event = True # Flip the flag
#                 continue # <-- This skips the rest of the loop and waits for the next event
#             # --- 🔥 END OF FIX ---
            
#             # If we are NOT resuming, or if this is a *new* event from the loop, we process it.
#             node_output = event["processing_agent"]
            
#             # --- FLOW 1: SOCIAL MEDIA POST ---
#             if node_output.get("interaction_is_required") and node_output.get("image_prompts"):
#                 print(f"⏸️ Graph paused to show prompt selection. Thread ID: {thread_id}")
#                 return ApiResponse(
#                     status="success", 
#                     thread_id=thread_id,
#                     data=node_output
#                 )
            
#             # --- FLOW 2: BLOG GENERATOR (or Refinement) ---
#             elif node_output.get("interaction_is_required") and node_output.get("blog_draft"):
#                 print(f"⏸️ Graph paused to show blog package review. Thread ID: {thread_id}")
#                 return ApiResponse(
#                     status="success", # 'success' because the "mid-output" is ready
#                     thread_id=thread_id,
#                     data=node_output # Send the whole node_output
#                 )
        
#         if "execution_agent" in event:
#             node_output = event["execution_agent"]
            
#             # We REMOVED the `validation_result == "no"` check here.
#             # We let the graph handle that internally.
            
#             # We ONLY stop if the agent pauses to show the *final* content.
#             if node_output.get("interaction_is_required") and node_output.get("current_images_base64"):
#                 print(f"⏸️ Graph paused to show final generated content. Thread ID: {thread_id}")
                
#                 full_state = await supervisor_app.aget_state(config)
#                 final_data = {**full_state.values, **node_output}

#                 return ApiResponse(
#                     status="success", 
#                     thread_id=thread_id,
#                     data=final_data 
#                 )
            
#             # Handle the final "blog_draft" from the validation loop
#             elif node_output.get("interaction_is_required") and node_output.get("blog_draft"):
#                 print(f"⏸️ Graph paused to show final *validated* blog content. Thread ID: {thread_id}")
                
#                 full_state = await supervisor_app.aget_state(config)
#                 final_data = {**full_state.values, **node_output}

#                 return ApiResponse(
#                     status="success", 
#                     thread_id=thread_id,
#                     data=final_data 
#                 )

#     # If the stream finishes with no pauses, it's the true end
#     final_state = await supervisor_app.aget_state(config)
#     print(f"✅ Workflow finished. Final state: {final_state.values}")
    
#     # 🔥 FINAL CHECK: If the workflow finished, but the last validation failed, send a failure response
#     if final_state.values.get("validation_result") == "no":
#         print("❌ Workflow finished because max retries were reached.")
#         return ApiResponse(
#             status="requires_input", # Send a failure to the UI
#             thread_id=thread_id,
#             data={
#                 "error": "Validation Failed",
#                 "critique": final_state.values.get("critique", "Max retries reached, but no critique found."),
#                 "retry_count": final_state.values.get("retry_count")
#             }
#         )
    
#     # Otherwise, it's a true success
#     return ApiResponse(status="success", thread_id=thread_id, data=final_state.values)

import uuid
import json 
import copy
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse # 🔥 For Server-Sent Events
from fastapi.middleware.cors import CORSMiddleware
from app.supervisor.state import update_dict 
from .models import GenerateRequest, ContinueRequest, ApiResponse
from app.supervisor.graph import supervisor_app

app = FastAPI(title="Content Creation Agentic System")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
                   allow_methods=["*"], allow_headers=["*"])

# (Your clean_log_event function is perfect, no changes)
def clean_log_event(event_dict):
    if not isinstance(event_dict, dict):
        return str(event_dict)
    log_event = copy.deepcopy(event_dict) 
    try:
        for node_name, node_output in log_event.items():
            if isinstance(node_output, dict):
                if "current_images_base64" in node_output and node_output["current_images_base64"]:
                    count = len(node_output["current_images_base64"])
                    node_output["current_images_base64"] = f"[TRUNCATED: {count} base64 image(s)]"
                if "blog_draft" in node_output and node_output["blog_draft"]:
                    draft = node_output["blog_draft"]
                    if isinstance(draft, str):
                        node_output["blog_draft"] = f"[TRUNCATED: Blog draft, {len(draft)} chars]"
        return json.dumps(log_event, indent=2)
    except Exception as e:
        return f"[Error cleaning log: {e}] | Original: {str(log_event)[:500]}..."

@app.get("/")
def read_root():
    return {"status": "ok"}

# --- 🔥 REFACTORED: /generate ---
# This endpoint now *only* creates the thread and returns its ID.
# It does NOT run the stream.
# app/api/main.py

@app.post("/generate", response_model=ApiResponse)
async def generate(request: GenerateRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    print(f"---API: New session initiated. Thread ID: {thread_id}---")
    
    initial_input = {
        "initial_request": {"service_id": request.service_id},
        "thread_id": thread_id,
        "retry_count": 0
    }
    
    try:
        # We "seed" the graph with the initial input
        # This just sets the starting state. It does NOT run the graph.
        await supervisor_app.aupdate_state(config, initial_input)
        print(f"---API: Seeded graph for {thread_id}---")
        
        # We return the thread_id so the frontend can connect to the stream
        return ApiResponse(
            status="streaming", # <-- NEW STATUS
            thread_id=thread_id,
            data={"message": "Thread created. Connect to stream."}
        )
    except Exception as e:
        print(f"---API: Error during /generate: {e}---")
        return ApiResponse(status="error", thread_id=None, data={"error": str(e)})

# --- 🔥 REFACTORED: /continue ---
# This endpoint now *only* updates the state and returns.
# It does NOT run the stream.
@app.post("/continue", response_model=ApiResponse)
async def continue_workflow(request: ContinueRequest):
    thread_id = request.thread_id
    config = {"configurable": {"thread_id": thread_id}}
    print(f"---API: Receiving update for Thread ID: {thread_id}---")
    print(f"---API: Continue type: {request.continue_type}---")
    
    try:
        # 1. Get the data to update the state with
        state_update = {"interaction_is_required": False} # Always unpause
        
        if request.continue_type == "plan_approval":
            print("---API: Plan approved by user---")
            
        elif request.continue_type == "answer":
            print(f"---API: User submitted answers---")
            if not request.user_answers:
                return ApiResponse(status="error", thread_id=thread_id, data={"error": "user_answers required"})
            state_update["user_answers"] = request.user_answers
        
        elif request.continue_type == "execution":
            print(f"---API: User submitted prompt (Social Media)---")
            if not request.user_answers or not request.user_answers.get("selected_prompt"):
                 return ApiResponse(status="error", thread_id=thread_id, data={"error": "selected_prompt is required"})
            state_update["user_answers"] = request.user_answers
            state_update["selected_prompt"] = request.user_answers.get("selected_prompt")
            state_update["num_images"] = request.user_answers.get("num_images")

        elif request.continue_type == "blog_approval":
            print(f"---API: Blog package update (approval or user critique)---")
            full_state = await supervisor_app.aget_state(config)

            critique = request.user_answers.get("critique") if request.user_answers else None
            state_update["critique"] = request.user_answers.get("critique") if request.user_answers else None
            state_update["critique"] = critique
            state_update["blog_draft"] = full_state.values.get("blog_draft")
            state_update["draft_caption"] = full_state.values.get("draft_caption")
            state_update["cover_image_prompt"] = full_state.values.get("cover_image_prompt")

        
        # 🔥 ADD THIS NEW CASE:
        elif request.continue_type == "final_approval":
            print(f"---API: Final approval (image and complete package)---")
            # User is happy with everything, just unpause
            # # No need to preserve anything, the state already has everything
            pass  # state_update already has interaction_is_required=False
        
        
        else:
             return ApiResponse(status="error", thread_id=thread_id, data={"error": f"Invalid continue_type: {request.continue_type}"})

        # 2. Update the state
        print(f"---API: Updating state for {thread_id}---")
        await supervisor_app.aupdate_state(config, state_update)
        
        # 3. Return a simple "ok"
        # The frontend's /stream endpoint will automatically resume.
        return ApiResponse(status="streaming", thread_id=thread_id, data={"message": "State updated, stream processing."})

    except Exception as e:
        print(f"---API: Error during /continue: {e}---")
        return ApiResponse(status="error", thread_id=thread_id, data={"error": str(e)})


# --- 🔥 NEW: /stream endpoint ---
# This is the new endpoint your EventSource will connect to.
@app.get("/stream/{thread_id}")
async def stream_events(thread_id: str, request: Request):
    config = {"configurable": {"thread_id": thread_id}}
    
    async def event_generator(thread_id: str, config: dict):
        try:
            print(f"---STREAM: Client connected for thread {thread_id}---")
            
            # Outer loop: Continue until the workflow is truly done
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    print(f"---STREAM: Client disconnected for thread {thread_id}---")
                    break
                
                # Run the graph from the current checkpoint
                async for event in supervisor_app.astream(None, config=config):
                    if await request.is_disconnected():
                        break

                    print(f"📡 Stream event:\n{clean_log_event(event)}")
                    
                    node_name = list(event.keys())[0]
                    node_data = event[node_name]

                    sse_event = {
                        "event": "log",
                        "agent": "unknown",
                        "node": node_name,
                        "data": node_data
                    }

                    # Identify the agent
                    if node_name == "planning_agent":
                        sse_event["agent"] = "planner"
                    elif node_name == "prepare_agent":
                        sse_event["agent"] = "prepare_agent"
                    elif node_name == "processing_agent":
                        sse_event["agent"] = "processing_agent"
                    elif node_name == "execution_agent":
                        sse_event["agent"] = "execution_agent"
                    elif node_name == "handle_failure_node":
                        sse_event["agent"] = "supervisor"
                    elif node_name == "service_lookup":
                        sse_event["agent"] = "supervisor"
                    
                    # Check for pauses
                    if isinstance(node_data, dict) and node_data.get("interaction_is_required"):
                        print(f"⏸️ Graph paused. Sending pause event to client.")
                        pause_data = {
                            "event": "pause",
                            "data": {
                                "status": "requires_input",
                                "thread_id": thread_id,
                                "data": node_data
                            }
                        }
                        yield f"data: {json.dumps(pause_data)}\n\n"
                    else:
                        yield f"data: {json.dumps(sse_event)}\n\n"
                
                # 🔥 KEY FIX: After astream finishes, check the state
                current_state = await supervisor_app.aget_state(config)
                
                # 🔥 CRITICAL: Check if we're paused first (interaction_is_required)
                if current_state.values.get("interaction_is_required", False):
                    print(f"⏸️ Graph is paused (interaction_is_required=True). Waiting for /continue...")
                    
                    # Poll until the state changes
                    while True:
                        if await request.is_disconnected():
                            break
                        
                        # Send heartbeat to keep connection alive
                        yield ": heartbeat\n\n"
                        
                        await asyncio.sleep(1.0)  # Poll every second
                        
                        updated_state = await supervisor_app.aget_state(config)
                        
                        # Check if /continue was called (interaction_is_required set to False)
                        if not updated_state.values.get("interaction_is_required", False):
                            print(f"▶️ State updated! Resuming graph for thread {thread_id}...")
                            break  # Exit polling loop, restart astream
                    
                    # Continue the outer while loop to call astream again
                    continue
                
                # 🔥 NOW check if workflow is truly finished
                # If next is empty AND interaction_is_required is False, we're done
                if current_state.next == ():
                    print(f"✅ Workflow finished for thread {thread_id}.")
                    
                    # Check for failure
                    if current_state.values.get("validation_result") == "no":
                        print("❌ Workflow finished on max retries.")
                        end_event = {
                            "event": "end",
                            "data": {
                                "status": "requires_input", 
                                "thread_id": thread_id,
                                "data": {
                                    "error": "Validation Failed",
                                    "validation_result": "no",
                                    "critique": current_state.values.get("critique", "Max retries reached."),
                                    "retry_count": current_state.values.get("retry_count")
                                }
                            }
                        }
                    else:
                        print("✅ Workflow finished successfully.")
                        end_event = {
                            "event": "end",
                            "data": {
                                "status": "success",
                                "thread_id": thread_id,
                                "data": current_state.values
                            }
                        }
                    
                    yield f"data: {json.dumps(end_event)}\n\n"
                    break  # Exit the outer while loop
                
                # If we're here, something unexpected happened
                # (This shouldn't occur, but just in case)
                print(f"⚠️ Unexpected state: next={current_state.next}, interaction_is_required={current_state.values.get('interaction_is_required')}")
                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            print(f"---STREAM: Connection cancelled for thread {thread_id}---")
        except Exception as e:
            print(f"---STREAM: Error in stream for {thread_id}: {e}---")
            error_event = {"event": "error", "data": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(event_generator(thread_id, config), media_type="text/event-stream")