from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # add_messages போட்டா தான் பழைய சாட் ஹிஸ்டரியோட புது மெசேஜ் அபெண்ட் ஆகும் மச்சா!
    messages: Annotated[list, add_messages] 
    user_query: str
    retrieved_context: List[str]
    case_analysis: str
    final_response: str