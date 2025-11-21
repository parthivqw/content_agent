# 🚀 Agentic Content Creation System  
### Multi-Agent LangGraph Pipeline • Real-Time SSE Streaming • Full End-to-End AI Workflow

This project is a **production-grade multi-agent system** built using **LangGraph**, designed to automate complex content-generation workflows such as blog creation, social media posts, and structured content plans.  

It uses **4 specialized agents** that collaborate inside a supervisor graph, with **real-time streaming (SSE)** and a clean & modular backend written in **FastAPI**.

---

# ⭐ Features

### 🔹 **1. Multi-Agent LangGraph Architecture**
- Supervisor graph controlling flow
- Subgraphs for Planning, Preparing, Processing & Execution
- Shared state (`AgentState`) with memory passing
- HITL (human-in-the-loop) interrupts and resume flows
- Automatic retry, fallback & validation loops

### 🔹 **2. Real-Time SSE Updates**
- Step-by-step agent transitions streamed to the frontend
- Heartbeats for connection stability
- UI state mirrors LangGraph state machine
- No WebSockets needed — clean, reliable SSE

### 🔹 **3. Dynamic Model Routing**
- Automatic provider ranking  
- Claude → GPT → Gemini → Local Llama fallback chain  
- Try/Except–based reliability guards  
- Multi-provider cascading when APIs fail  

### 🔹 **4. Modular Python Codebase**
Organized cleanly into:
app/
agents/
planning/
preparing/
processing/
execution/
core/
supervisor/
tools/
api/
index.html

markdown
Copy code

### 🔹 **5. Frontend Included**
- `index.html` provides:
  - Live logs
  - Agent step cards
  - Real-time progress bar
  - Streaming output area

---

# ⭐ Architecture Overview

### **Supervisor Graph**
Controls the entire workflow:
- dispatches tasks to sub-agents  
- handles state transitions  
- enforces safety conditions  
- performs retries and validation

### **Planning Agent**
- Breaks down user request  
- Generates action plans  
- Scores complexity  
- Produces structured steps

### **Prepare Agent**
- Validates inputs  
- Ranks best model provider  
- Prepares context before workflow

### **Processing Agent**
- Executes the LLM logic  
- Includes fallback loops  
- Ensures coherent structured output  
- Guards token + latency limits

### **Execution Agent**
- Final synthesis  
- Blog/post/asset generation  
- Sends final output to UI via SSE  

---

# ⭐ Frontend: Real-Time Streaming UI

The included `index.html` provides:
- Step-by-step agent progression  
- Live SSE logs  
- Task status cards  
- Smooth UX with no refreshes  
- Perfect for demos & presentations  

A perfect showcase for recruiters & founders.

---

# ⭐ How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/parthivqw/content_agent.git
cd content_agent
2. Create a virtual environment
bash
Copy code
python -m venv venv
venv\Scripts\activate  # Windows
3. Install dependencies
bash
Copy code
pip install -r requirements.txt
4. Add your environment variables
Create .env:

env
Copy code
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key
5. Run the FastAPI Server
bash
Copy code
uvicorn app.api.main:app --reload
6. Open the UI
Open:

bash
Copy code
http://localhost:8000/index.html
⭐ Screenshots
(Add these after you push — I will help)

⭐ Roadmap
 Add Web UI with React

 Docker deployment

 Background workers for async agents

 Multi-tenant user support

 Advanced analytics for agent decisions

⭐ Why This Project Exists
This system demonstrates:

real production-grade agentic workflows

LangGraph mastery

orchestration thinking

state machines

streaming systems

LLM reliability engineering

modular backend architecture

It is designed as a portfolio-grade project proving end-to-end ownership.

⭐ Author
Parthiv S (23)
Full-stack AI Engineer • Agentic Systems Builder
🚀 Passion for production-ready LLM engineering
