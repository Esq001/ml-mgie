from fastapi import APIRouter, HTTPException, UploadFile

from app.config import settings
from app.models.schemas import DocumentType, UploadedDocument
from app.services.document_processor import DocumentProcessor

router = APIRouter(prefix="/documents", tags=["documents"])

# In-memory store (swap for a database in production)
documents_store: dict[str, UploadedDocument] = {}
processor = DocumentProcessor()


@router.post("/upload", response_model=UploadedDocument)
async def upload_document(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_file_size_mb}MB limit",
        )

    try:
        document = await processor.process_upload(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    documents_store[document.id] = document
    return document


@router.get("/", response_model=list[UploadedDocument])
async def list_documents():
    return list(documents_store.values())


@router.get("/{document_id}", response_model=UploadedDocument)
async def get_document(document_id: str):
    doc = documents_store.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.patch("/{document_id}/type")
async def update_document_type(document_id: str, doc_type: DocumentType):
    doc = documents_store.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.document_type = doc_type
    return doc


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    del documents_store[document_id]
    return {"status": "deleted"}
