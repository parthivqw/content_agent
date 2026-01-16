


# app/tools/llm_tools.py
import json
from openai import OpenAI
from typing import List, Dict, Any, Optional
import requests
import base64

from app.core.config import settings

# 🔥 GROQ CLIENT (OpenAI SDK)
client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# 🔥 A4F CONFIGURATION (Raw requests)
A4F_BASE_URL = "https://api.a4f.co/v1"
A4F_API_KEY = settings.A4F_API_KEY
A4F_HEADERS = {
    "Authorization": f"Bearer {A4F_API_KEY}",
    "Content-Type": "application/json"
}

# --- 🔥 YOUR CHOSEN MODELS ---
MODEL_GPT_OSS = 'openai/gpt-oss-120b'
MODEL_GPT_4O_MINI = 'provider-2/gpt-oss-120b'  # A4F chat model
MODEL_LLAMA_3_1 = 'llama-3.3-70b-versatile'
MODEL_KIMI = 'moonshotai/kimi-k2-instruct-0905'

# --- 🔥 A4F Model List ---
MODEL_IMAGEN_4 = "provider-4/imagen-4"
MODEL_PHOENIX = "provider-4/phoenix"
MODEL_IMAGEN_3 = "provider-4/imagen-3.5"
MODEL_IMAGEN4_LITE = "provider-5/imagen-4-fast"
MODEL_FLUX = "provider-4/flux-schnell"
MODEL_QWEN="provider-4/qwen-image"

# --- Predefined Options ---
PREDEFINED_OPTIONS = {
    "platform": ["Instagram", "LinkedIn", "Facebook", "Twitter/X", "Website", "Other"],
    "content_purpose": ["Personal Post", "Business Promotion", "Hiring Ad", "Event Ad", "Product Launch", "Artwork/Illustration", "Other"],
    "emotion_vibe": ["Fun", "Calm", "Bold", "Professional", "Energetic", "Elegant", "Minimalist", "Other"],
    "visual_style": ["Photo-realistic", "3D Render", "Vector Illustration", "Flat Design", "Hand-drawn", "Minimalist", "Abstract", "Other"],
    "include_text_message": ["Yes (Text/Logo/Message)", "No (Visuals Only)"],
    "desired_tone": ["Friendly", "Professional", "Humorous", "Inspirational", "Informative", "Urgent", "Casual", "Formal", "Other"]
}
MASTER_CONTENT_TYPE_LIST = """
A. Social Media Creatives
 - Social Media Post
 - Story (Instagram, Facebook)
 - Reel/Short Video Thumbnail
 - Carousel Slide
 - Profile Picture
 - Cover Photo / Banner

B. Promotional / Marketing Graphics
 - Poster
 - Flyer
 - Banner (horizontal or vertical)
 - Advertisement (Generic Ad)
 - Promotional Graphic
 - Sales / Discount Creative
 - Product Launch Creative
 - Product Showcase Image
 - Teaser Graphic

C. Business / Professional Creatives
 - Hiring Ad
 - Company Announcement
 - Corporate Banner
 - Event Invitation
 - Webinar Poster
 - Conference Poster
 - Business Presentation Slide
 - Testimonial Graphic

D. Personal / Portrait / Branding
 - Portrait
 - Personal Branding Post
 - Lifestyle Photo Creative
 - Aesthetic Moodboard
 - Before/After Graphic
 - Personal Announcement
 - Birthday Post

E. Art / Illustration / Concept
 - Artwork
 - Illustration
 - 3D Render
 - Abstract Design
 - Character Concept
 - Fan Art
 - Digital Painting
 - Comic Panel
 - Anime-style Portrait
 - Album Cover Art

F. Website / App / UI Assets
 - Website Hero Image
 - App Screenshot Mockup
 - UI Component Graphic
 - Dashboard Illustration
 - Landing Page Banner

G. Informational / Educational
 - Infographic
 - Quote Post
 - Step-by-step Graphic
 - Instructional Poster
 - Fact Sheet Creative

H. Special Purpose Content
 - Certificate
 - Menu Card
 - Brochure
 - Magazine Cover
 - Book Cover
 - Thumbnail (YouTube)
 - Podcast Cover
 - Greeting Card
 - Invitation Card (Wedding/Birthday/Party)
 - Meme Template
"""

# 🔥 NEW: A4F CHAT COMPLETION HELPER
def a4f_chat_completion(model: str, messages: List[Dict], temperature: float = 0.35, max_tokens: int = 500) -> str:
    """
    Calls A4F chat completion API using raw requests (not OpenAI SDK).
    Returns the content string.
    """
    url = f"{A4F_BASE_URL}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(url, headers=A4F_HEADERS, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ A4F Chat API Error: {e}")
        raise

# --- PROMPT GENERATION SYSTEM PROMPT ---
PROMPT_GENERATION_SYSTEM_PROMPT = """
You are a world-class Director of Photography (DP) and AI Prompt Engineer. 
Your task is to synthesize a user's creative brief into a single, masterpiece-level image generation prompt.

User Payload:
{payload}

### 🧠 YOUR CORE INSTRUCTIONS (DO NOT COPY-PASTE EXAMPLES)

1. **Analyze the Subject Matter:** - If the subject is a *Landscape/Cityscape*, use wide-angle terminology (e.g., "24mm wide angle", "panoramic", "infinite depth of field").
   - If the subject is a *Portrait*, use portrait terminology (e.g., "85mm portrait lens", "bokeh", "shallow depth of field", "focus on eyes").
   - If the subject is *Macro/Product*, use macro terminology (e.g., "100mm macro", "extreme close-up", "texture focus").
   - **DO NOT** default to "50mm f/1.8" unless it specifically fits the scene composition. Choose the lens that fits the shot.

2. **Lighting & Atmosphere (The "Vibe"):**
   - Don't just list colors. Describe *how light behaves*.
   - Use terms like: "volumetric fog," "subsurface scattering" (for skin), "god rays," "chiaroscuro," "bioluminescent glow," or "hard studio lighting" based on the `{emotion_vibe}`.

3. **Text Integration (Crucial):**
   - If `{include_text_message}` is "Yes": Clearly describe the text's physical presence (e.g., "a neon sign reading 'HELLO'", "embossed gold lettering on a card", "holographic data display showing...").
   - If `{include_text_message}` is "No": You MUST append this negative constraint naturally: "clean composition, no text, no watermarks, no typography."

4. **The "Flux/Imagen" Style:**
   - These models prefer natural language over "tag soup". Write a cohesive paragraph describing the scene as if you are explaining a movie frame to a CGI artist.

### 🚫 NEGATIVE CONSTRAINTS
- DO NOT blindly copy generic camera settings.
- DO NOT use the word "parameter" or "settings".
- DO NOT start with "Here is the prompt". Just output the prompt.

### OUTPUT FORMAT
Return **ONLY** the raw prompt string. No quotes, no labels.
"""
# --- GOLDEN EXAMPLE PLAN ---
GOLDEN_PLAN_EXAMPLE = """
{
  "prepare_agent": [
    {
      "stage": 1,
      "step_description": "Ask the user what kind of image or post they want to create (e.g., social post, promo, artwork, etc.) — this defines the general purpose.",
      "output_keys": ["content_purpose"]
    },
    {
      "stage": 1,
      "step_description": "Ask the user to select or confirm the platform or destination (Instagram, LinkedIn, website, etc.).",
      "output_keys": ["platform"]
    },
    {
      "stage": 1,
      "step_description": "Ask the user to pick the vibe or emotion they want the design to express (e.g., fun, calm, bold, professional).",
      "output_keys": ["emotion_vibe"]
    },
    {
      "stage": 1,
      "step_description": "Ask whether the user wants to include text, logo, or message in the design.",
      "output_keys": ["include_text_message"]
    },
    {
      "stage": 1,
      "step_description": "Ask the user to select a visual style preference (photo-realistic, 3D render, vector illustration, etc.).",
      "output_keys": ["visual_style"]
    }
  ],
  "processing_agent": [
    {
      "step_description": "Synthesize all user inputs into a single structured payload for downstream generation.",
      "output_keys": ["generation_payload"]
    },
    {
      "step_description": "Create a detailed image generation prompt using the structured payload.",
      "output_keys": ["image_prompt"]
    },
    {
      "step_description": "Draft a compelling caption that aligns with the desired tone and platform.",
      "output_keys": ["draft_caption"]
    }
  ],
  "execution_agent": [
    {
      "step_description": "Validate the 'image_prompt' and 'draft_caption' for quality and alignment.",
      "output_keys": ["validation_report"]
    },
    {
      "step_description": "Assemble the final deliverable package.",
      "output_keys": ["final_package"]
    }
  ]
}
"""

# --- ACTION PLAN GENERATION ---
def generate_action_plan_tool(service_info: Dict[str, Any]) -> dict:
    print("---TOOL: 🧠 Generating ACTION PLAN---")
    
    guidelines = service_info.get("planning_guidelines")
    service_name = service_info.get("name")
    service_desc = service_info.get("description")
    predefined_keys_list = ", ".join([f'"{k}"' for k in PREDEFINED_OPTIONS.keys()])

    system_prompt = f"""
You are a methodical and expert AI workflow architect. Your SOLE purpose is to convert high-level guidelines into a
detailed, step-by-step JSON action plan.

You are NOT a creative assistant. You are a system architect.
DO NOT invent steps. DO NOT add your own ideas. Your job is to OBEY.

You MUST follow the user's guidelines precisely.
You MUST output JSON in the exact structure as the "GOLDEN PLAN EXAMPLE" provided.

---
HERE IS THE "GOLDEN PLAN EXAMPLE" FOR A "Social Media Post Generator":
This is the level of detail and structure you must replicate.
{GOLDEN_PLAN_EXAMPLE}
---

**🔥 CRITICAL KEY-MATCHING RULE:**
Your `prepare_agent` steps will be used to generate questions.
IF you want to generate a "radio button" question for a common topic (like tone, vibe, platform, etc.),
you **MUST** use the exact `output_key` from this list:
[ {predefined_keys_list} ]

If you use any other key (like "topic" or "audience"), it will become a `textarea`.
**DO NOT** use "tone" (use "desired_tone"). **DO NOT** use "vibe" (use "emotion_vibe").

Now, you must generate a NEW plan.

SERVICE TO PLAN FOR:
- Service Name: "{service_name}"
- Service Description: "{service_desc}"

THESE ARE THE GUIDELINES YOU MUST FOLLOW:
"{guidelines}"

Generate the complete JSON action plan for the "{service_name}" service based *only* on its guidelines,
following the exact structure and key-matching rules.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_GPT_OSS,
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        result_text = response.choices[0].message.content
        print(f"DEBUG TOOL (Action Plan): Raw LLM Output: {result_text[:200]}...")
        result = json.loads(result_text)
        print(f"✅ LLM generated a valid action plan.")
        return result
    except Exception as e:
        print(f"❌ ERROR generating or validating action plan: {e}")
        return {"error": f"Failed to generate a valid action plan: {str(e)}"}

# 🔥 REFACTORED: STAGE 1 QUESTIONS (A4F via requests)
def generate_dynamic_questions_tool(
    plan_steps_for_stage: List[Dict[str, Any]],
    data_requirements: List[str],
    previous_answers: Optional[Dict[str, Any]] = None
) -> dict:
    """
    Generates Stage 1 questions using A4F's GPT-4o-mini via raw requests.
    """
    print(f"---TOOL (Stage 1): 🧠 Generating questions for {len(data_requirements)} plan steps---")
    
    if previous_answers:
        context_summary = {k: v for k, v in previous_answers.items() if isinstance(v, (str, int, float, bool, list))}
        print(f"---TOOL (Stage 1): Context -> Previous Answers (Summary): {context_summary} ---")
    else:
        previous_answers = {}

    requirements_str = "\n- ".join(data_requirements)
    keys_needed_this_stage = list(set([key for step in plan_steps_for_stage for key in step.get("output_keys", [])]))
    relevant_options = {k: v for k, v in PREDEFINED_OPTIONS.items() if k in keys_needed_this_stage}
    options_str = json.dumps(relevant_options, indent=2) if relevant_options else "None applicable for this stage."

    platform = previous_answers.get("platform", "")
    if platform == "LinkedIn":
        tone_hint = "Use a confident, professional tone — polite and composed."
    elif platform == "Instagram":
        tone_hint = "Use a warm, natural, and creative tone — friendly but not slangy."
    else:
        tone_hint = "Use a balanced, conversational tone — approachable and calm."

    system_prompt = f"""
You are a skilled creative consultant helping a user plan a visual post.

TONE RULES:
- {tone_hint}
- Sound human, not corporate or teenage.
- Each question should flow naturally, like gentle guidance.
- Stay concise and polite.

STRUCTURE RULES:
- Return JSON: {{ "questions": [ ... ] }}
- Each question MUST have: "id", "type", "label"
- "type" can be "radio" or "textarea"
- Include "options" array only for "radio" type questions
- The "id" must match one of the required output keys
- Do not add chatter outside the JSON.

PREDEFINED OPTIONS (use these for radio questions):
{options_str}

DATA REQUIREMENTS (what we need to ask about):
{requirements_str}

REQUIRED OUTPUT KEYS: {', '.join(keys_needed_this_stage)}

Generate the Stage 1 questions now.
"""

    try:
        # 🔥 Using A4F via raw requests
        messages = [{"role": "system", "content": system_prompt}]
        result_text = a4f_chat_completion(MODEL_GPT_4O_MINI, messages, temperature=0.35, max_tokens=500)
        
        print(f"DEBUG TOOL (Stage 1): Raw LLM Output: {result_text[:500]}...")
        result = json.loads(result_text)

        if "questions" not in result or not isinstance(result["questions"], list):
            raise ValueError("LLM response missing 'questions' list.")

        print(f"✅ LLM generated {len(result.get('questions', []))} Stage 1 questions.")
        return result
        
    except Exception as e:
        print(f"❌ ERROR generating Stage 1 questions: {e}")
        return {
            "questions": [{
                "id": "error",
                "label": f"Sorry, could not generate Stage 1 questions. Error: {str(e)}",
                "type": "textarea"
            }]
        }




CLASSIFY_CONTENT_SYSTEM_PROMPT = """
You are an expert-level **Content Classification Agent**.
Your SOLE purpose is to analyze the user's <context> and map it to **ONE SINGLE** category from the <master_list>.

<master_list>
{master_list}
</master_list>

---
Here is your 5-point reasoning guide. You MUST follow this:

<reasoning_guide>
1.  **Post Type → Core Intent:**
    * 'Business Promotion', 'Hiring Ad', 'Event Ad', 'Product Launch' strongly imply categories B or C.
    * 'Personal Post' implies category D.
    * 'Artwork/Illustration' implies category E.

2.  **Platform → Format:**
    * 'LinkedIn' suggests C.
    * 'Website' suggests F.
    * 'Instagram' suggests A or D.

3.  **Text/Logo Included? → Type Confirmation:**
    * **'Yes'** is a very strong signal for categories B, C, G, or H.
    * **'No'** strongly implies categories D or E.

4.  **Visual Style → Final Refinement:**
    * 'Photo-realistic' points to D or B.
    * 'Vector Illustration' or 'Flat Design' strongly suggests B, C, or G.
</reasoning_guide>

---
Here is the user's context, based on their Stage 1 answers:

<context>
{context}
</context>

---
RULES:
1.  You MUST follow the <reasoning_guide> to analyze the <context>.
2.  You MUST select the *most relevant category* from the <master_list> (e.g., "C. Business / Professional Creatives").
3.  You MUST return a valid JSON object with this exact structure:
    {{
      "classification": {{
        "category": "<The chosen category heading, e.g., 'C. Business / Professional Creatives'>"
      }},
      "reasoning": "<A brief, 1-2 sentence explanation of why you chose this category>"
    }}
4.  🔥 **CRITICAL:** Your response MUST be **ONLY** the valid JSON object. Do not include `json` markdown fences, or any text before or after the JSON object. Start your response *immediately* with `{{` and end *immediately* with `}}`.
---

Analyze the <context> and provide your JSON classification now.
"""


# --- 🔥 REPLACED: CONTENT CLASSIFICATION TOOL (NOW CATEGORY-ONLY) ---
def classify_content_type_tool(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls a "Classifier" LLM to map user answers to a specific content CATEGORY
    from the master list.
    """
    print("---TOOL: 🧠 Classifying Content CATEGORY---") # <-- Updated log

    model_to_use = MODEL_GPT_OSS 
    
    system_prompt_content = CLASSIFY_CONTENT_SYSTEM_PROMPT.format(
        master_list=MASTER_CONTENT_TYPE_LIST,
        context=json.dumps(context, indent=2)
    )

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt_content},
                {"role": "user", "content": "Generate the JSON classification now."}
            ],
            model=model_to_use,
            temperature=0.0,
            response_format={"type": "json_object"} # <-- Your typo fix is good
        )

        result_text = response.choices[0].message.content
        print(f"DEBUG TOOL (Category Classifier): Raw LLM Output: {result_text}")

        result_json = json.loads(result_text)

        # 🔥 --- UPDATED CHECK --- 🔥
        if 'classification' not in result_json or 'category' not in result_json.get('classification', {}):
            raise ValueError("LLM output missing 'classification.category' key.")
        
        print(f"✅ LLM Category Classification: {result_json.get('classification', {}).get('category')}")
        
        # Return the whole JSON { "classification": {...}, "reasoning": "..." }
        return result_json 
    
    except Exception as e:
        print(f"❌ ERROR in classify_content_tool: {e}")
        return {
            "classification": {"category": "Error"}, # <-- Updated error
            "reasoning": f"Failed to classify content category: {e}"
        }
    



# --- 🔥 REPLACED *AGAIN*: The FINAL Stage 2 Prompt (Hybrid) ---
SYSTEM_PROMPT_STAGE_2 = """
You are an expert-level creative assistant. Your SOLE job is to generate a list of
follow-up questions based on the user's <context> and their desired <classification>.

<context>
{context}
</context>

<classification>
- Type: {content_type}
- Category: {content_category}
</classification>

---
### 🔥 1. YOUR CORE RESPONSIBILITIES
Your goal is to gather the *final details* needed to build the **{content_type}**.
This means you MUST ask for two types of details (if applicable):

1.  **VISUAL DETAILS:** You MUST ask for visual details (like `subject_details`)
    *ONLY IF* the <classification> (`type`) is for a visual post (e.g., 'Hiring Ad', 'Portrait', 'Product Showcase Image').
    * **DO NOT** ask for visual details if the type is **'Blog Post'** or **'Quote Post'**. The visual for a blog is generated *later* by a different agent based on the text.

2.  **TEXT DETAILS:** You MUST ask for specific text details (like `headline`, `cta`, etc.) 
    *IF* the <context> (`include_text_message`) is 'Yes (Text/Logo/Message)' OR the <classification> (`type`) is text-based like **'Blog Post'** or **'Quote Post'**.
---

### 🧠 2. YOUR TASK: Generate Questions
Based on the **{content_type}** classification, generate the *specific* follow-up
questions for both VISUALS and TEXT.

EXAMPLES (Follow this logic):
- If the type is 'Blog Post':
    - Ask for 'topic' (the main subject)
    - Ask for 'audience' (who is this for?)
    - Ask for 'key_points_to_cover' (textarea for bullet points)
    - Ask for 'specific_cta' (what should the reader do next?)

- If the type is 'Hiring Ad' AND `include_text_message` is 'Yes':
    - Ask for 'job_title' (text)
    - Ask for 'location' (text)
    - Ask for 'call_to_action' (text, e.g., "Apply at...")
    - Ask for 'subject_details' (visuals, e.g., "Describe the main visual theme or any objects/people")
    - Ask for 'background_details' (visuals, e.g., "Describe the desired background/setting")

- If the type is 'Portrait' (which implies `include_text_message` was 'No'):
    - Ask for 'subject_details' (visuals, e.g., "Describe the person or character")
    - Ask for 'background_details' (visuals, e.g., "Describe the environment")

- If the type is 'Quote Post' (which implies text-only):
    - Ask for 'the_quote' (text)
    - Ask for 'the_author' (text)

---
### 🤖 3. UI & JSON RULES
1.  **JSON OUTPUT:** You MUST return *only* a valid JSON object: {{"questions": [ ... ]}}
2.  **QUESTION FORMAT:** Each question object MUST have: "id" (string, snake_case), "type", and "label".
3.  **UI TYPES:** You MUST use one of these three string values for the "type":
    * `"textarea"`: For open-ended text (like 'job_description', 'subject_details').
    * `"radio"`: For **single-choice** options (like 'Layout Format', 'Vibe').
    * `"checkbox"`: For **multi-select** options (like 'Key Features', 'Color Palette').
4.  **SMART UI CHOICE:**
    * Use `"checkbox"` for "Select all that apply" questions.
    * Use `"radio"` for "Choose one" questions.
    * Always add `"Other"` as the last option for `"radio"` and `"checkbox"` types.
5.  **NO QUESTIONS?** If all info is present in the <context>, return: {{"questions": []}}

---
### ✅ 4. FINAL VALIDATION CHECKLIST (Think before you output)
1.  Did I follow the task for **{content_type}**?
2.  Did I check <context> and add questions for **both VISUALS and TEXT** as needed?
3.  Did I avoid asking for info I already have (like 'platform' or 'visual_style')?
4.  Is every question's "type" *exactly* "textarea", "radio", or "checkbox"?
5.  Is my final output *only* the valid JSON?
---

Generate the specific follow-up questions for a **{content_type}** now.
"""


#---STAGE 2: QUESTIONS TOOL---
def generate_follow_up_questions_tool(
        context: Dict[str,Any],
        service_info: Optional[Dict[str,Any]],
        classification: Optional[Dict[str,Any]]
) -> dict:
    """
    Generates Stage 2 follow-up questions based on the CLASSIFIED content type.
    """
    print(f"---TOOL (Stage 2): Generating adpative follow-up questions---")

    if not classification or classification.get("type")=="Error":
        print("---TOOL (Stage 2):ERROR -No valid classification provided.---")
        return {"questions":[{"id":"error","label":"No classification found.","type":"textarea"}]}
    
    #Extract classification details
    content_type= classification.get("type","Unknown")
    content_category=classification.get("category","Unknown")

    print(f"---TOOL (Stage 2):Classified  as :{content_type}---")

    system_prompt_content=SYSTEM_PROMPT_STAGE_2.format(
        context=json.dumps(context,indent=2),
        content_type=content_type,
        content_category=content_category,
        service_name=service_info.get("name","Unknown Service"),
        service_desc=service_info.get("description","No description")


    )

    try:
        #We can still use a mini model here, because the task
        #is no longer "reason" but follow specific instructions
        messages=[{"role":"system","content":system_prompt_content}]
        result_text=a4f_chat_completion(
            MODEL_GPT_4O_MINI,
            messages,
            temperature=0.3,
            max_tokens=1024
        )

        print(f"DEBUG TOOL (Stage 2): Raw LLM output :{result_text[:500]}...")
        result_json=json.loads(result_text)

        if "questions" not in result_json or not isinstance(result_json["questions"],list):
            raise ValueError("LLM response missing 'questions' list.")
        
        #---Post processing Logic---
        print("---TOOL (Stage 2): Running post-processing rules...---")
        processed_questions=[]

        for q in result_json.get("questions",[]):
            if not all(k in q for k in ["id","label","type"]):
                print(f"Post-processor:Skipping malformed question:{q}")
                continue

            #Check if we already have this answer from Stage 1
            if q['id'] in context:
                print(f"Post-processor: SKIPPING REPETITIVE question '{q['id']}' ")
                continue
            #(you can add more rules here if you want)
            processed_questions.append(q)
        
        result_json['questions']=processed_questions
        #---(End of post-processing)---
        print(f"LLM generated and processed {len(result_json.get("questions",[]))} adaptive Stage 2 questions.")
        return result_json
    
    except Exception as e:
        print(f"ERROR generating follow-up questions: {e}")
        return {
            "questions":[{
                "id":"error",
                "label":f"Sorry, could not generate follow-up questions.",
                "type":"textarea"
            }]
        }


# --- IMAGE PROMPT GENERATION (GROQ) ---
def generate_image_prompt_tool(payload: Dict[str, Any], model_name: str):
    """
    Generates a single, cinematic image prompt from a payload using a specific Groq Model.
    """
    print(f"---TOOL: Generating prompt with {model_name}---")
    try:
        # 🔥 FIX: Extract the missing variables needed by the prompt string
        emotion_vibe = payload.get("emotion_vibe", "professional")
        include_text = payload.get("include_text_message", "No")

        # 🔥 FIX: Pass them into .format()
        system_prompt_content = PROMPT_GENERATION_SYSTEM_PROMPT.format(
            payload=json.dumps(payload, indent=2),
            emotion_vibe=emotion_vibe,           # <--- Added this
            include_text_message=include_text    # <--- Added this
        )

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt_content},
                {"role": "user", "content": "Generate the prompt now."}
            ],
            model=model_name,
            temperature=0.7,
            max_tokens=2048
        )

        generated_prompt = response.choices[0].message.content.strip()

        if generated_prompt.startswith('"') and generated_prompt.endswith('"'):
            generated_prompt = generated_prompt[1:-1]

        print(f"---TOOL: Generated prompt (model:{model_name}): {generated_prompt[:70]}...")
        return {"prompt": generated_prompt}
    
    except Exception as e:
        print(f"TOOL ERROR (generate_image_prompt_tool) with {model_name}: {e}")
        return {"prompt": f"Error generating prompt with {model_name}: {e}"}

# --- CAPTION GENERATION (GROQ) ---
CAPTION_GENERATION_SYSTEM_PROMPT = """
You are a world-class social media copywriter. Your job is to take a JSON object
of user preferences for an image and write a single, compelling caption.

The user's preferences are:
{payload}

RULES:
- The caption must perfectly match the 'emotion_vibe' (e.g., 'Bold', 'Fun', 'Calm').
- It must be optimized for the 'platform' (e.g., Instagram captions can be a bit longer and use 3-5 relevant hashtags).
- It must be directly relevant to the 'subject_details' and 'background_details'.
- The output MUST be a single, raw string containing ONLY the caption. No preamble.
"""

def generate_caption_tool(payload: Dict[str, Any], model_name: str) -> Dict[str, Any]:
    """
    Generates a single, creative caption from a payload using a specific Groq Model.
    """
    print(f"--TOOL: Generating caption with {model_name}---")
    try:
        user_prompt = CAPTION_GENERATION_SYSTEM_PROMPT.format(payload=json.dumps(payload, indent=2))

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert copywriter. Output only the final caption and nothing else."},
                {"role": "user", "content": user_prompt}
            ],
            model=model_name,
            temperature=0.7,
            max_tokens=1024,
        )

        generated_caption = response.choices[0].message.content.strip()

        if generated_caption.startswith('"') and generated_caption.endswith('"'):
            generated_caption = generated_caption[1:-1]
        
        print(f"---TOOL: Generated caption: {generated_caption[:70]}...")
        return {"caption": generated_caption}
    
    except Exception as e:
        print(f"TOOL ERROR (generate_caption_tool): {e}")
        return {"caption": f"Error generating caption: {e}"}

# 🔥 IMAGE GENERATION FROM A4F (Using OpenAI SDK for images - this still works)
a4f_client = OpenAI(
    base_url="https://api.a4f.co/v1",
    api_key=A4F_API_KEY,
)

def generate_image_from_a4f_tool(prompt: str, model_name: str, num_images: int = 1) -> Dict[str, Any]:
    """
    Calls the A4F API to generate an image and returns a list of base64 strings.
    """ 
    print(f"---TOOL: Generating {num_images} image(s) with {model_name}---")
    try:
        response = a4f_client.images.generate(
            model=model_name,
            prompt=prompt,
            n=num_images,
            size="1024x1024"
        )

        if not response.data:
            raise Exception("API returned no image data.")
        
        base64_images = []
        for image_data in response.data:
            image_url = image_data.url
            print(f"---TOOL: Downloading image from {image_url}---")

            image_response = requests.get(image_url)
            image_response.raise_for_status()

            image_bytes = image_response.content
            base64_string = base64.b64encode(image_bytes).decode("utf-8")
            base64_images.append(base64_string)
        
        print(f"---TOOL: Successfully generated and encoded {len(base64_images)} image(s).---")
        return {"images_base64": base64_images}
    
    except Exception as e:
        print(f"TOOL ERROR (generate_image_from_a4f_tool): {e}")
        return {"images_base64": [], "error": str(e)}

# --- MODEL RANKING (GROQ) ---
def get_model_ranking_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls an LLM to dynamically rank the 5 available image models
    based on the user's generation payload.
    """
    print("---TOOL: Getting dynamic model ranking...---")
    model_to_use = MODEL_GPT_OSS

    try:
        system_content = """You are an AI Model Routing Specialist. Your job is to rank image generation models based on the user's specific requirements.

 THE MODEL ARSENAL (Know your tools)

1. **"provider-4/imagen-4" (TIER S - THE KING)**
   - **STRENGTHS:** Unbeatable text rendering (spelling), hyper-realism, complex prompt adherence.
   - **USE WHEN:** User asks for text/logos, "photorealistic" portraits, or complex "Business" content.
   - **WEAKNESS:** Slower than "fast" models.

2. **"provider-4/phoenix" (TIER A - THE ARTIST)**
   - **STRENGTHS:** Incredible lighting, cinematic composition, "vibes", artistic styles (oil painting, cyberpunk).
   - **USE WHEN:** "Cinematic", "Artistic", "Fantasy", or "Atmospheric" is requested.
   - **WEAKNESS:** Good at text, but Imagen 4 is better.

3. **"provider-5/imagen-4-fast" (TIER A - THE SPEEDSTER)**
   - **STRENGTHS:** High quality but optimized for speed.
   - **USE WHEN:** User wants "Social Media" content where speed matters, but quality must remain high.

4. **"provider-4/imagen-3.5" (TIER B - THE VETERAN)**
   - **STRENGTHS:** Very reliable, good all-rounder.
   - **USE WHEN:** A safe fallback if others fail.

5. **"provider-4/flux-schnell" (TIER B - THE SPECIALIST)**
   - **STRENGTHS:** 3D Renders, Abstract Art, Surrealism. Very fast.
   - **USE WHEN:** "3D Render", "Abstract", "Minimalist" styles are requested.

6. **"provider-4/qwen-image" (TIER C - THE WILDCARD)**
   - **STRENGTHS:** Good general understanding.
   - **USE WHEN:** Complex logic is needed, or as a deep fallback.

---

### 🧠 ROUTING LOGIC (Follow this strictly)

**SCENARIO 1: TEXT IS CRITICAL**
If `include_text_message` is "Yes" or the prompt mentions "sign", "headline", "logo":
-> **MUST RANK #1:** "provider-4/imagen-4"
-> **Rank #2:** "provider-4/phoenix"

**SCENARIO 2: PHOTOREALISM / PORTRAITS**
If `visual_style` is "Photo-realistic":
-> **MUST RANK #1:** "provider-4/imagen-4"
-> **Rank #2:** "provider-5/imagen-4-fast"

**SCENARIO 3: 3D / ABSTRACT / ART**
If `visual_style` is "3D Render", "Illustration", or "Abstract":
-> **MUST RANK #1:** "provider-4/flux-schnell" or "provider-4/phoenix"

**SCENARIO 4: BLOG COVERS (High Quality Required)**
If the request is for a "Blog Post" or "Article":
-> **NEVER** rank low-quality models first. Prioritize Imagen 4 or Phoenix.

---

### OUTPUT FORMAT
Return ONLY valid JSON:
{
  "model_ranking": ["model_id_1", "model_id_2", "model_id_3", "model_id_4", "model_id_5"]
}
"""

        user_content = f"""Rank these models for this request:

{json.dumps(payload, indent=2)}

Return the ranking as JSON."""

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            model=model_to_use,
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content.strip()
        result_json = json.loads(result_text)
        ranking = result_json.get("model_ranking")

        if not ranking or len(ranking) != 5:
            raise ValueError("LLM did not return a valid 5-model ranking.")
        
        print(f"---TOOL: Model ranking received: {ranking}---")
        return {"model_ranking": ranking}
        
    except json.JSONDecodeError as je:
        print(f"TOOL ERROR (JSON decode): {je}")
        return {
            "model_ranking": [MODEL_IMAGEN_4, MODEL_PHOENIX, MODEL_IMAGEN_3, MODEL_FLUX, MODEL_IMAGEN4_LITE],
            "error": f"JSON decode failed: {str(je)}"
        }
    except Exception as e:
        print(f"TOOL ERROR (get_model_ranking_tool): {e}")
        return {
            "model_ranking": [MODEL_IMAGEN_4, MODEL_PHOENIX, MODEL_IMAGEN_3, MODEL_FLUX, MODEL_IMAGEN4_LITE],
            "error": str(e)
        }

# --- BLOG PACKAGE GENERATION (GROQ) ---
BLOG_PACKAGE_SYSTEM_PROMPT = """
You are an expert-level content marketer, ghostwriter, and social media strategist.
Your task is to take the user's creative brief and generate a complete blog campaign package
in a single JSON object.

<CREATIVE_BRIEF>
{payload}
</CREATIVE_BRIEF>

You MUST return a valid JSON object with exactly these three keys:
1. `blog_draft`
2. `teaser_caption`
3. `cover_image_prompt`

---

### ⚠️ QUALITY ASSURANCE WARNING
Your output will be validated by another AI agent.
- Your work will be **REJECTED** if you fail to address **all** topics in `key_points_to_cover`.
- Your work will be **REJECTED** if you **copy-paste** the `specific_cta` text instead of
  creatively interpreting it into a new conclusion.

---

### 🧩 CONTENT GENERATION INSTRUCTIONS

**For `blog_draft`:**
- Produce a cinematic, SEO-optimized blog post (500–700 words) built around the topic: **{topic}**.
- The blog must be written in the **{desired_tone}** tone, appealing to **{audience}**, and evoke an **{emotion_vibe}** mood.
- **You must address ALL points** from `{key_points_to_cover}`.
- Follow this structure strictly:
  - **Title**
  - **Introduction** (hook + context)
  - **3–5 body sections** (use `##` markdown headers)
  - **Conclusion** that **creatively re-writes and fulfills** the user's CTA instruction: `{specific_cta}`.

---

### ✍️ For `teaser_caption`
- Write a 2–3 sentence teaser that feels elegant and emotionally engaging.
- Reflect the `{emotion_vibe}` and invite readers to click.
- This will be used for social media promotion.

---

### 🎨 For `cover_image_prompt`
- Write a vivid, cinematic, photo-realistic prompt describing the perfect featured image for this blog.
- Capture the essence of `{topic}` and `{emotion_vibe}`.
- Include details like lighting, composition, setting, and mood.
- Avoid faces, text, or logos unless crucial.

---

### ⚙️ OUTPUT RULES
- Output only a **valid JSON object** with the three keys listed above.
- Ensure all string values are properly escaped.
- Do **not** include commentary, XML tags, or explanations outside the JSON.
- **Verify your own work** against the QA WARNING before finishing.

---

Think like a top-tier strategist from HubSpot or National Geographic.
Generate the complete JSON blog package now.
"""

def generate_blog_package_tool(payload: Dict[str, Any], model_name: str) -> Dict[str, Any]:
    """
    Generates a full blog package (draft, teaser, cover prompt) from a payload.
    """
    print(f"---TOOL: 📦 Generating Blog Package with {model_name}---")
    
    system_prompt_content = BLOG_PACKAGE_SYSTEM_PROMPT.format(
        payload=json.dumps(payload, indent=2),
        topic=payload.get('topic', 'the specified topic'),
        audience=payload.get('audience', 'the target audience'),
        desired_tone=payload.get('desired_tone', 'a professional tone'),
        emotion_vibe=payload.get('emotion_vibe', 'an engaging vibe'),
        key_points_to_cover=payload.get('key_points_to_cover', ''),
        seo_keywords=payload.get('seo_keywords', ''),
        specific_cta=payload.get('specific_cta', 'read more.')
    )
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt_content},
                {"role": "user", "content": "Generate the complete blog package as a JSON object now."}
            ],
            model=model_name,
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        print(f"DEBUG TOOL (Blog Package): Raw LLM Output: {result_text[:200]}...")
        
        result_json = json.loads(result_text)
        
        if 'blog_draft' not in result_json or 'teaser_caption' not in result_json or 'cover_image_prompt' not in result_json:
            raise ValueError("LLM output is missing one or more required keys.")

        print("✅ LLM generated a valid blog package.")
        return result_json

    except Exception as e:
        print(f"❌ ERROR generating blog package: {e}")
        return {
            "blog_draft": "Error: Could not generate the blog draft.",
            "teaser_caption": "Error: Could not generate the caption.",
            "cover_image_prompt": "Error: Could not generate the prompt."
        }

# --- BLOG VALIDATION (GROQ) ---
VALIDATION_SYSTEM_PROMPT = """
You are a meticulous Quality Assurance (QA) specialist. Your job is to
validate a generated `blog_draft` against the user's original `generation_payload`.

You must answer in a specific JSON format:
{{"validation_result": "yes" | "no", "critique": "your reasoning"}}

RULES:
1.  Read the <generation_payload> to understand the user's *exact* requirements.
2.  Read the <blog_draft> to see what was generated.
3.  **VALIDATE THE KEY POINTS:** Did the blog draft *successfully address*
    ALL topics listed in `key_points_to_cover`?
4.  **VALIDATE THE CTA:** Did the blog's conclusion *creatively interpret*
    the instruction in `specific_cta`, or did it just paste it?
5.  If **BOTH** checks pass, return `"validation_result": "yes"`.
6.  If **EITHER** check fails, return `"validation_result": "no"` and
    write a *clear, actionable critique* for the processing agent.

<generation_payload>
{payload}
</generation_payload>

<blog_draft>
{blog_draft}
</blog_draft>

Generate your JSON response now.
"""

def validate_content_tool(payload: Dict[str, Any], blog_draft: str) -> Dict[str, Any]:
    """
    Calls a "checker" LLM to validate the blog draft against the user's payload.
    """
    print(f"---TOOL: Validating Blog Content---")

    model_to_use = MODEL_GPT_OSS

    system_prompt_content = VALIDATION_SYSTEM_PROMPT.format(
        payload=json.dumps(payload, indent=2),
        blog_draft=blog_draft
    )

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt_content},
                {"role": "user", "content": "Validate the content and provide your JSON response."}
            ],
            model=model_to_use,
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content
        print(f"DEBUG TOOL (Validation): Raw LLM Output: {result_text}")
        result_json = json.loads(result_text)

        if 'validation_result' not in result_json:
            raise ValueError("Validation Output is missing 'validation_result' key.")
        
        print(f"LLM Validation complete. Result: {result_json.get('validation_result')}")

        return result_json
    
    except Exception as e:
        print(f"ERROR in validation tool: {e}")
        return {
            "validation_result": "no",
            "critique": f"Validation tool failed: {e}. Defaulting to 'no'."
        }

# # --- BLOG REFINEMENT (GROQ) ---
# REFINE_BLOG_PACKAGE_SYSTEM_PROMPT = """
# You are an **elite content refinement specialist** for a multi-agent blog generation system. Your job is to FIX a failed blog draft that did not pass validation.

# ---

# ## YOUR ROLE:

# You are receiving a blog draft that was **rejected by the QA agent** because it failed to meet the user's requirements. Your task is to produce a **revised version** that:

# 1. **Addresses ALL issues raised in the critique** (this is your PRIMARY directive)
# 2. **Preserves the original writing quality, style, and tone** (do NOT rewrite from scratch)
# 3. **Keeps ALL sections that were correct** (only fix what's broken)
# 4. **Maintains the exact same markdown structure** (same headers, same sections)

# ---

# ## CRITICAL RULES:

# 1. **The critique is GOSPEL** - Whatever the QA agent flagged MUST be fixed. No exceptions.

# 2. **Surgical precision** - Only modify the sections that need fixing. Do NOT rewrite sections that were already correct.

# 3. **Match the original requirements** - The `generation_payload` contains the user's original requirements. The revised draft MUST fulfill every point in `key_points_to_cover` and use the `specific_cta` exactly as provided.

# 4. **Preserve tone and voice** - The original draft had a specific writing style. Your revision should sound like it came from the same author, just with the missing pieces added.

# 5. **Add, don't replace** - If the critique says "lacks X", ADD X to the draft. Don't remove good content to make room for it.

# ---

# ## OUTPUT REQUIREMENTS:

# Return a **valid JSON object** with these exact keys:
# ```json
# {
#   "blog_draft": "<your revised markdown blog>",
#   "teaser_caption": "<original caption UNLESS critique asked for changes>",
#   "cover_image_prompt": "<original prompt UNLESS critique asked for changes>"
# }
# ```

# **IMPORTANT**: 
# - If the critique ONLY mentions the blog draft, DO NOT modify the caption or image prompt. Return them unchanged.
# - If the critique mentions multiple components, fix only what was flagged.

# ---

# ## YOUR WORKFLOW:

# 1. **Read the critique carefully** - Identify EXACTLY what failed.
# 2. **Locate the section** - Find where in the original draft the issue exists.
# 3. **Research if needed** - If the critique asks for scriptural references, specific data, or citations, provide them accurately.
# 4. **Make surgical edits** - Add the missing content in the appropriate section WITHOUT removing good content.
# 5. **Verify completeness** - Re-read the `key_points_to_cover` and ensure your revised draft now covers ALL of them.
# 6. **Return valid JSON** - Your response must be parseable JSON with the three required keys.

# ## QUALITY CHECKLIST (Before returning):

# ✅ Does the revised draft address EVERY point in the critique?
# ✅ Did I preserve the original writing style and tone?
# ✅ Did I keep all sections that were already correct?
# ✅ Does the revised draft fulfill ALL items in `key_points_to_cover`?
# ✅ Did I use the `specific_cta` exactly as provided?
# ✅ Is my output valid JSON with all three required keys?

# Now, refine the failed blog draft using the critique as your guide. Remember: surgical precision, not a full rewrite.
# """
# --- 🔥 REPLACED: BLOG REFINEMENT PROMPT (Stricter) ---
REFINE_BLOG_PACKAGE_SYSTEM_PROMPT = """
You are an **elite content refinement specialist** and Quality Assurance (QA) editor.
Your job is to FIX a failed blog draft that was rejected by a previous QA agent.

---
### 1. YOUR TASK & CONTEXT

You will be given:
1.  `<generation_payload>`: The user's original requirements.
2.  `<failed_blog_draft>`: The draft that was just rejected.
3.  `<critique>`: The *specific reason* it was rejected.

Your task is to produce a **revised version** of the blog package.

---
### 2. YOUR CRITICAL TWO-STEP WORKFLOW

**STEP 1: Fix the Critique**
-   You MUST surgically address and fix ALL issues raised in the `<critique>`. This is your primary directive.
-   Do NOT rewrite the whole draft. Preserve the original style. Only modify what's broken.

**STEP 2: Re-Validate Against Original Payload**
-   **THIS IS A CRITICAL STEP.** After fixing the critique, you MUST re-read the *entire* `<generation_payload>`.
-   You must check your *new* draft to ensure it **NOW** meets ALL original requirements, especially:
    -   Does it cover **ALL** points in `key_points_to_cover`?
    -   Does it **creatively interpret** the `specific_cta` (not just copy-paste it)?
-   If your fix for the critique *also* broke one of these original rules, you must fix that too before finishing.

---
### 3. OUTPUT REQUIREMENTS

Return a **valid JSON object** with these exact keys:
```json
{
  "blog_draft": "<your revised markdown blog>",
  "teaser_caption": "<original caption UNLESS critique asked for changes>",
  "cover_image_prompt": "<original prompt UNLESS critique asked for changes>"
}
"""

def refine_blog_package_tool(
    generation_payload: Dict[str, Any], 
    failed_blog_draft: str, 
    failed_teaser_caption: str, 
    failed_cover_image_prompt: str,
    critique: str, 
    model_name: str = MODEL_KIMI
) -> Dict[str, Any]:
    """
    Refines a failed blog package based on QA critique.
    """
    print(f"---TOOL: Refining Blog Package with {model_name}---")

    user_prompt = f"""
Here is the data you need to refine the failed blog draft:

## ORIGINAL USER REQUIREMENTS (generation_payload):
```json
{json.dumps(generation_payload, indent=2)}
```

## FAILED BLOG DRAFT:
{failed_blog_draft}

## FAILED TEASER CAPTION:
{failed_teaser_caption}

## FAILED COVER IMAGE PROMPT:
{failed_cover_image_prompt}

## QA CRITIQUE (What to fix):
{critique}

---

Now, produce a refined version that fixes ALL issues raised in the critique while preserving the quality of the original draft.
"""
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": REFINE_BLOG_PACKAGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )

        raw_output = response.choices[0].message.content
        print(f"DEBUG TOOL (Refine): Raw LLM Output: {raw_output[:200]}---")

        refined_package = json.loads(raw_output)

        required_keys = ["blog_draft", "teaser_caption", "cover_image_prompt"]
        if not all(key in refined_package for key in required_keys):
            raise ValueError(f"Missing required keys in refined output")
        
        print("✅ LLM successfully refined the blog package.")
        return refined_package
    
    except Exception as e:
        print(f"TOOL ERROR (refine_blog_package_tool): {e}")
        return {
            "blog_draft": f"Error: Failed to refine draft. {e}",
            "teaser_caption": failed_teaser_caption,
            "cover_image_prompt": failed_cover_image_prompt
        }
