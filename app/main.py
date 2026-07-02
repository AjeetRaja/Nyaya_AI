from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.agents.nyaya_agent import nyaya_brain
from langchain_core.messages import HumanMessage  # இதை இம்போர்ட் பண்ணிக்கோ மச்சா

app = FastAPI(title="Nyaya_AI Orchestrator API")

class ChatRequest(BaseModel):
    user_query: str
    thread_id: str = "default_user"

@app.get("/")
def read_root():
    return {"message": "Welcome to Nyaya_AI Legal Assistant Backend, Macha!"}

@app.post("/api/chat")
async def chat_with_nyaya(request: ChatRequest):
    if not request.user_query:
        raise HTTPException(status_code=400, detail="Macha, query empty-ஆ இருக்குடா!")
    
    try:
        # யூசர் கேக்குற கேள்வியை HumanMessage-ஆ மாத்தி 'messages' லிஸ்ட்டுக்குள்ள போடுறோம்
        initial_state = {
            "messages": [HumanMessage(content=request.user_query)],
            "user_query": request.user_query,
            "retrieved_context": [],
            "case_analysis": "",
            "final_response": ""
        }
        
        config = {"configurable": {"thread_id": request.thread_id}}
        output_state = nyaya_brain.invoke(initial_state, config=config)
        
        return {
            "status": "Success",
            "thread_id": request.thread_id,
            "case_analysis": output_state.get("case_analysis"),
            "retrieved_chunks_count": len(output_state.get("retrieved_context", [])),
            "response": output_state.get("final_response")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Macha, Agent Error: {str(e)}")