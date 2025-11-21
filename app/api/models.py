from pydantic import BaseModel,Field
from typing import Dict, Any, Optional,List
#---Request Models---
#Thease Models define the expected structre of incoming data.

class GenerateRequest(BaseModel):
    """
    Model for initial/generate request.
    The frontend only needs to send the ID of the service the user selected.
    """
    service_id: str
    #thread_id is optional, to allow resuming a previous session
    thread_id: Optional[str]= None

class ContinueRequest(BaseModel):
    """
    Model for /continue reuqest to provide answer's to the agent's questions.
    """
    thread_id: str
    user_answers: Optional[Dict[str, Any]] = None
    continue_type: str = "answer"

#---Response Models---
# This defines the structure of all data we send back to the frontend.

class ApiResponse(BaseModel):
    """
    Standard API response structure for all endpoints.
    """
    status:str
    thread_id: Optional[str] = None
    #data will hold the sessions for the user or the final results
    data: Optional[Dict[str,Any]] = None 


class AgentTask(BaseModel):
    """Defines a single, specific task for an AI agent to perform."""
    step_description: str = Field(
        ..., 
        description="A clear, concise instruction for the agent to execute."
    )
    output_keys: List[str] = Field(
        ..., 
        description="The specific data keys the agent must produce in its output dictionary after completing the task."
    )

class ActionPlan(BaseModel):
    """The complete, structured workflow plan for all agents."""
    prepare_agent: List[AgentTask] = Field(
        ..., 
        description="A list of tasks for the Prepare Agent to gather and clarify user information."
    )
    processing_agent: List[AgentTask] = Field(
        ..., 
        description="A list of tasks for the Processing Agent to perform the core creative and generative work."
    )
    execution_agent: List[AgentTask] = Field(
        ..., 
        description="A list of tasks for the Execution Agent to validate, format, and assemble the final product."
    )