from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import AgentState
from app.agents.research_agent import run_research_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import logging

def run_nyaya_orchestrator(state: AgentState) -> dict:
    """
    முழு சாட் ஹிஸ்டரியையும் எடுத்து ஜெமினிக்கு அனுப்பி, 
    பழைய விஷயங்களை ஞாபகம் வச்சு பதில் சொல்ல வைக்கும் முதன்மை ஏஜென்ட் மச்சா!
    """
    context = state.get("retrieved_context", [])
    context_str = "\n\n".join(context)
    
    # 1. சிஸ்டம் பிராம்ப்ட் செட் பண்றோம்
    system_prompt = f"""
    You are Nyaya_AI, an expert Indian Legal Assistant. 
    Analyze the user's legal issue based on the extracted document sections and provide advice.
    
    Legal Case Context from Database:
    {context_str}
    
    Instructions:
    - Determine if the case is Civil or Criminal.
    - Reference specific sections from the context if applicable.
    - Provide structured, practical advice in a supportive tone.
    """
    
    # 2. நம்ம ஸ்டேட்ல இருக்குற முழு மெசேஜ் லிஸ்ட்டையும் எடுக்கிறோம் மச்சா (இதுல தான் பழைய சாட் இருக்கும்)
    messages_history = state.get("messages", [])
    
    # சிஸ்டம் மெசேஜையும், பழைய சாட் ஹிஸ்டரியையும் ஒன்னா சேர்க்கிறோம்
    input_messages = [SystemMessage(content=system_prompt)] + messages_history
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        # இப்போ வெறும் பிராம்ப்ட் ஸ்ட்ரிங்குக்கு பதிலா, முழு மெசேஜ் லிஸ்ட்டையும் இன்வோக் பண்றோம்!
        response = llm.invoke(input_messages)
        final_text = response.content
    except Exception as e:
        logging.error(f"Nyaya Orchestrator LLM Invoke Failed: {str(e)}")
        final_text = f"Macha, LLM failed to generate advice: {str(e)}"

    # இப்போ அவுட்புட்ல ஜெமினியோட பதிலை AI மெசேஜாக 'messages' கீ-ல ரிட்டர்ன் பண்றோம்
    return {
        "final_response": final_text, 
        "case_analysis": "Analyzed by Nyaya Orchestrator Graph",
        "messages": [response] # இது லேங்கிராப் ஹிஸ்டரியில ஆட் ஆகிடும்!
    }

# 3. கிராப் கம்பைலேஷன் (மாற்றங்கள் இல்லை மச்சா)
workflow = StateGraph(AgentState)
workflow.add_node("research_agent", run_research_agent)
workflow.add_node("nyaya_orchestrator", run_nyaya_orchestrator)

workflow.set_entry_point("research_agent")
workflow.add_edge("research_agent", "nyaya_orchestrator")
workflow.add_edge("nyaya_orchestrator", END)

memory = MemorySaver()
nyaya_brain = workflow.compile(checkpointer=memory)