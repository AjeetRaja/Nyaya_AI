from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.database.connection import get_db
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import io
import logging

router = APIRouter()

MAX_FILE_SIZE = 10485760  # 10MB Limit
BUCKET_NAME = "legal-documents"

# லோக்கல் எம்பெடிங் மாடலை குளோபலா லோட் பண்றோம் (Server ஸ்டார்ட் ஆகும்போது ஒருமுறை மட்டும் லோடாகும்)
try:
    logging.info("Macha! Loading local embedding model (all-MiniLM-L6-v2)...")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    logging.info("Embedding model loaded successfully! 🔥")
except Exception as e:
    logging.error(f"Failed to load embedding model: {str(e)}")
    embedding_model = None

@router.post("/api/legal/upload")
async def upload_legal_document(
    file: UploadFile = File(...), 
    supabase = Depends(get_db)
):
    if embedding_model is None:
        raise HTTPException(status_code=500, detail="Macha, embedding model is not initialized properly.")

    # 1. Type Validation
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, 
            detail="Macha! Only PDF files are allowed."
        )
    
    # 2. Size Validation
    try:
        file_size = 0
        while chunk := await file.read(1024 * 1024):
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400, 
                    detail="Macha! File size too large. Limit is 10MB."
                )
        await file.seek(0)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"File size check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing file size.")

    # 3. Supabase Storage Push Logic
    try:
        file_content = await file.read()
        file_path = f"uploaded_{file.filename}"

        supabase.storage.from_(BUCKET_NAME).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type, "x-upsert": "true"}
        )
        
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)

    except Exception as e:
        logging.error(f"Supabase Storage Upload Failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Macha! Failed to upload to Supabase Storage: {str(e)}"
        )

    # 4. Text Extraction Logic
    extracted_text = ""
    try:
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
        
        if not extracted_text.strip():
            extracted_text = "No extractable text found in this PDF (Scanned Image or Empty File)."

    except Exception as e:
        logging.error(f"PDF Text Extraction Failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Macha! Uploaded to storage, but failed to extract text from PDF."
        )

    # 5. Smart Text Chunking Logic
    chunks = []
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
        
        if extracted_text.strip() and "No extractable text found" not in extracted_text:
            chunks = text_splitter.split_text(extracted_text)
            
    except Exception as e:
        logging.error(f"Text chunking failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Macha! Failed to create vector chunks.")

    # 6. Vector Embedding Generation & Database Ingestion (Stage 4 Complete! 🚀)
    if chunks:
        try:
            # எல்லா சங்கிஸுக்கும் லோக்கலா வெக்டார் எம்பெடிங்ஸ் ஜெனரேட் பண்றோம்
            embeddings = embedding_model.encode(chunks).tolist()
            
            # சுபாபேஸ் டேபிள்ல போடுறதுக்கு ஏத்த மாதிரி டேட்டாவை ஸ்ட்ரக்சர் பண்றோம்
            data_to_insert = []
            for chunk, embedding in zip(chunks, embeddings):
                data_to_insert.append({
                    "file_name": file.filename,
                    "content": chunk,
                    "embedding": embedding
                })
            
            # சுபாபேஸ் pgvector டேபிளுக்கு மொத்தமா இன்செர்ட் (Bulk Insert) பண்றோம்
            supabase.table("legal_document_sections").insert(data_to_insert).execute()

        except Exception as e:
            logging.error(f"Vector Database Insertion Failed: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Macha! Uploaded & parsed, but failed to push to Vector DB: {str(e)}"
            )

    return {
        "status": "Success",
        "filename": file.filename,
        "supabase_url": public_url,
        "total_chunks_saved": len(chunks),
        "detail": "Macha! File is in storage, text is parsed, and Vector DB is loaded! Stage 4 Complete! 🔥🚀"
    }