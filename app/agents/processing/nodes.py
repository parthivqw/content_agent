

from .state import ProcessingState
from app.tools.llm_tools import(
    generate_image_prompt_tool,
    generate_caption_tool,
    generate_blog_package_tool,
    # --- 🔥 IMPORT THE REFINE TOOL ---
    refine_blog_package_tool, 
    MODEL_GPT_OSS,
    MODEL_KIMI,
    MODEL_LLAMA_3_1
)

#This is our 3-model stack
MODEL_1=MODEL_GPT_OSS
MODEL_2=MODEL_LLAMA_3_1
MODEL_3=MODEL_KIMI

def run_creative_generation_node(state: ProcessingState):
    """
    Generates 3 prompt variations and 1 caption by calling the tools.
    This is a SYNC node,just like your planning node.
    """
    print("---PROCESS AGENT: Running Creative Generation---")
    payload=state.get("generation_payload")
    if not payload:
        print("PROCESS AGENT:No generation payload found.")
        return{
            "image_prompts":["Error:No payload provided"],
            "draft_caption":"Error: No payload."
        }
    
    #---1. Generated 3 Prompt Variations---
    # we run thease one by one since the tools are sync
    print(f"---PROCESS AGENT: Generating Prompt 1 ({MODEL_1})...---")
    prompt_1_result=generate_image_prompt_tool(payload,MODEL_1)

    print(f"---PROCESS AGENT: Generating Prompt 2 ({MODEL_2})...---")
    prompt_2_result = generate_image_prompt_tool(payload, MODEL_2)
    
    print(f"---PROCESS AGENT: Generating Prompt 3 ({MODEL_3})...---")
    prompt_3_result = generate_image_prompt_tool(payload, MODEL_3)

    all_prompts=[
        prompt_1_result.get("prompt","Error generating prompt 1"),
        prompt_2_result.get("prompt","Error generating prompt 2"),
        prompt_3_result.get("prompt","Error generating prompt 3")
    ]

    print(f"---PROCESS AGENT: Generated {len(all_prompts)} prompts.---")

    #---2. Generate 1 Caption---
    #well use the llama 3.3 for the caption
    print(f"---PROCESS AGENT: Generating caption ({MODEL_2})...---")
    caption_result=generate_caption_tool(payload,MODEL_2)
    draft_caption=caption_result.get("caption","Error generating  caption.")

    print("---PROCESS AGENT: Creative generation complete.---")

    # 🔥 We must also set interaction_is_required to pause for UI
    return {
        "image_prompts":all_prompts,
        "draft_caption":draft_caption,
        "interaction_is_required": True,
        "critique": None # Ensure critique is cleared
    }


# --- 🔥 MODIFIED: This node is now a "Generate or Refine" router ---
def run_blog_package_node(state: ProcessingState):
    """
    Generates OR refines the blog package.
    Checks if there's a critique - if yes, refine. If no, generate fresh.
    """
    print("---PROCESS AGENT: Running Blog Package Node---")
    
    payload=state.get("generation_payload")
    if not payload:
        return {"blog_draft":"Error: No payload."}
    
    # 🔥 CHECK IF THIS IS A REFINEMENT REQUEST
    critique = state.get("critique")  # This comes from the supervisor
    
    if critique:
        # ✅ REFINEMENT PATH (Loop iteration)
        print("---PROCESS AGENT: REFINEMENT MODE - Fixing failed draft.---")
        
        # Get the failed draft from state
        failed_draft = state.get("blog_draft")
        failed_caption = state.get("draft_caption")
        failed_prompt = state.get("cover_image_prompt")
        
        # Call the new refinement tool
        result = refine_blog_package_tool(
            generation_payload=payload,
            failed_blog_draft=failed_draft,
            failed_teaser_caption=failed_caption,
            failed_cover_image_prompt=failed_prompt,
            critique=critique,
            model_name=MODEL_KIMI # Use Kimi for refinement
        )
        
        print("---PROCESS AGENT: Blog package refinement complete.---")
        # 🔥 BUG FIX: Return the result but set interaction_is_required to FALSE
        # This tells the supervisor router to loop back to execution, not pause.
        return {
            "blog_draft":result.get("blog_draft"),
            "draft_caption":result.get("teaser_caption"),
            "cover_image_prompt":result.get("cover_image_prompt"),
            "critique": None, # Clear the critique
            "interaction_is_required": False # <-- THIS IS THE FIX
        }

    else:
        # ✅ GENERATION PATH (First run)
        # 🔥 BUG FIX: This code is now correctly indented in the ELSE block
        print("---PROCESS AGENT: GENERATION MODE - Creating fresh draft.---")
        
        #We'll use the best model for this
        model_to_use=MODEL_KIMI
        
        #Call our original tool
        result=generate_blog_package_tool(payload,model_to_use)

        print("---PROCESS AGENT: Blog package generation complete.---")
        
        # 🔥 The *first* run needs to set interaction_is_required to TRUE
        return {
            "blog_draft":result.get("blog_draft"),
            "draft_caption":result.get("teaser_caption"),
            "cover_image_prompt":result.get("cover_image_prompt"),
            "critique": None,
            "interaction_is_required": True # <-- This pauses for UI review
        }