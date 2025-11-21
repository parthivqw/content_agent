from .state import ExecutionState
from typing import Dict,Any
from app.tools.llm_tools import generate_image_from_a4f_tool,get_model_ranking_tool,validate_content_tool

#Our fallback model list
MODEL_FALLBACK_LIST=[
    "provider-4/imagen-4",
    "provider-4/phoenix",
    "provider-4/imagen-3",
    "provider-4/sdxl-lite",
    "provider-4/flux-schnell"


]



#---NEW: NODE 1 (FOR BLOGS)---
def validation_node(state: ExecutionState)-> Dict[str,Any]:
    """
    Runs the "Checker" tool on the blog draft.
    """
    print("---EXEC AGENT: Running Validation Node---")
    payload=state.get("generation_payload")
    blog_draft=state.get("blog_draft")

    if not payload or not blog_draft:
        return {
            "validation_result":"no",
            "critique":"Error: Missing payload or blog draft to validate."
        }
    validation_data=validate_content_tool(payload,blog_draft)

    return validation_data


#---NODE 2(SHARED)---
def get_model_ranking_node(state: ExecutionState) -> Dict[str,Any]:
    """
    Calls the tool to get the dynamically ranked list of models.
    This is used nby BOTH services.
    """
    print("---EXEC AGEMT: Getting dynamic model ranking...---")
    payload=state.get("generation_payload")

    if not payload:
        return {"model_ranking":[],"current_error":"No generation_payload."}
    
    result=get_model_ranking_tool(payload)
    return {
        "model_ranking":result.get("model_ranking"),
        "current_model_index":0,
        "current_error":result.get("error")

    }


#---NODE 3(SHARED)----
def generate_image_node(state: ExecutionState):
    """
    Generates the image.
    -For Social Media: uses 'selected_prompt'
    -For Blog: uses 'cover_image_prompt'
    """
    print("---EXEC AGENT: Running Image Generation Node---")

    model_ranking=state.get("model_ranking")
    model_index=state.get("current_model_index")

    #---SMART PROMPT SELECTION---
    service_id=state.get("service_info",{}).get("id")
    if service_id=="blog_generator":
        prompt_to_use=state.get("cover_image_prompt")
        num_images=1 # Always 1 for blog covers
    
    else:
        prompt_to_use=state.get("selected_prompt")
        num_images=state.get("num_images")

    if not model_ranking:
        return {"current_error":"No model ranking was generated.","current_model_index": model_index + 1 }
    
    if not prompt_to_use:
        return {"current_error":"No prompt was selected or generated.","current_model_index": model_index + 1}
    
    if model_index>=len(model_ranking):
        return {
            "current_images_base64":[],
            "current_error":"All 5 image models failed for this creative."
        }
    
    model_name=model_ranking[model_index]
    print(f"---EXEC AGENT: Attempt {model_index+1} / {len(model_ranking)} with model: {model_name}---")

    result=generate_image_from_a4f_tool(
        prompt=prompt_to_use,
        model_name=model_name,
        num_images=num_images
    )

    if result.get("error") or not result.get("images_base64"):
        print(f"EXEC AGENT: Tool failed for {model_name}.Error:{result.get('error')}")

        return {
            "current_images_base64":[],
            "current_error":result.get("error","Image generation failed."),
            "current_model_index":model_index + 1

        }
    print(f"EXEC AGENT: Successfully generated {len(result['images_base64'])} image(s).---")

    return {
        "current_images_base64":result['images_base64'],
        "current_error":None,
        "interaction_is_required":True
        
    }
