

import json
from pathlib import Path
from .state import PlanningState
from app.tools.llm_tools import generate_action_plan_tool

def _load_static_plan(plan_path: str)-> dict:
    """Helper function to load a static plan from a file"""
    try:
        #We define the path relative to this file.
        #Path(__file__).parents[2] goes up two levels (from agents/planning to app/)
        full_path=Path(__file__).parents[2] / plan_path
        print(f"---PLANNING AGENT:Loading static plan from:{full_path}---")

        with open(full_path,'r') as f:
            action_plan=json.load(f)
        
        print("Static plan loaded successfully.")
        return action_plan
    except FileNotFoundError:
        print(f"ERROR:Static plan not found at {full_path}")
        return {'error':f"Static plan file not found :{plan_path}"}
    except json.JSONDecodeError:
        print(f"ERROR:Static plan file at {full_path} is not valid JSON.")
        return {"error":"Static plan file is corrupted."}
    except Exception as e:
        print(f"ERROR: Unknown error loading static plan:{e}")
        return {'error':f"An unknown error occured:{e}"}
    
def planning_conversation_node(state: PlanningState)-> dict:
    """
    This node acts as the master planner.It checks the 'plan_node' from
    the service_info and either loads a static plan or invokes the LLM
    to generate one dynamically.
    """
    print("---PLANNING AGENT:Master Planning Node---")
    service_info=state.get('service_info')
    if not service_info:
        raise ValueError("Service info is missing from the planning state.")
    #---THIS IS THE SWITCH---
    plan_mode=service_info.get("plan_mode") 
    action_plan=None

    if plan_mode == "static":
        print("---PLANNING AGENT:'static' mode selected.---")
        plan_path=service_info.get('plan_path')
        if not plan_path:
            return {'action_plan':{"error":"Static mode selected but no 'plan_path' was provided."}}   
        
        action_plan = _load_static_plan(plan_path)

    
    elif plan_mode =="ai":
        print("---PLANNING AGENT:'ai' mode selected.----")
        if not service_info.get("planning_guidelines"):
            return {'action_plan':{'error':"AI mode selected but no 'planning_guidelines' were provided."}}
        
        action_plan=generate_action_plan_tool(service_info)

    
    else:
        #Default behaviour if 'plan_mode' is missing or invalid
        print(f"Unknown 'plan_mode':{plan_mode}.Deafaulting to AI.")
        guidelines=service_info.get("planning_guidelines")
        if not guidelines:
            return {"action_plan":{"error":"AI mode selected but no 'planning_guidelines' were provided."}}
        
        action_plan=generate_action_plan_tool(guidelines)

    #---END OF SWITCH ---

    return {'action_plan':action_plan}