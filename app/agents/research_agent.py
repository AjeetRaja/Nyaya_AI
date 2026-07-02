from app.database.connection import get_db
from sentence_transformers import SentenceTransformer
import logging

# அப்லோட் ரௌட்டர்ல யூஸ் பண்ணின அதே லோக்கல் மாடலை இங்கேயும் கனெக்ட் பண்றோம்
try:
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as e:
    logging.error(f"Research Agent embedding init failed: {str(e)}")
    embedding_model = None

def run_research_agent(state: dict) -> dict:
    """
    யூசர் கேள்வியை வெக்டாரா மாற்றி, சுபாபேஸ் மேட்சிங் ஃபங்க்ஷன் (match_legal_sections)
    மூலமாக லீகல் டேட்டாவை தேடி எடுக்கும் ஏஜென்ட்.
    """
    query = state.get("user_query", "")
    retrieved_chunks = []

    if embedding_model and query:
        try:
            # 1. கேள்வியை வெக்டாரா மாத்துறோம்
            query_embedding = embedding_model.encode(query).tolist()
            
            # 2. FastAPI டிபென்டென்சி இல்லாம நேரடியா சுபாபேஸ் கிளியண்ட்டை எடுக்கிறோம்
            # (இங்க உன்னோட சுபாபேஸ் கனெக்ஷன் லாஜிக் படி டேட்டாபேஸை கால் பண்ணனும்)
            from app.config import settings # உன்னோட config-ல் இருந்து URL, Key எடுக்க
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
            # 3. நம்ம எடிட்டர்ல எழுதின RPC ஃபங்க்ஷனை கால் பண்றோம்
            response = supabase.rpc("match_legal_sections", {
                "query_embedding": query_embedding,
                "match_threshold": 0.3, # 30% மேட்ச் ஆனாலே எடுக்கும்
                "match_count": 3        # டாப் 3 லீகல் துண்டுகள்
            }).execute()
            
            if response.data:
                for row in response.data:
                    retrieved_chunks.append(row["content"])
                    
        except Exception as e:
            logging.error(f"Research Agent Vector Search Failed: {str(e)}")

    # ஸ்டேட்டை அப்டேட் பண்ணி அடுத்த ஏஜென்ட்டுக்கு அனுப்புறோம்
    return {"retrieved_context": retrieved_chunks if retrieved_chunks else ["No matching legal database context found."]}