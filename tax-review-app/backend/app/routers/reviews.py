from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    CompareRequest,
    ComparisonResult,
    ReportRequest,
    ReviewRequest,
    ReviewResult,
)
from app.routers.documents import documents_store
from app.services.claude_reviewer import ClaudeReviewer

router = APIRouter(prefix="/reviews", tags=["reviews"])

reviews_store: dict[str, ReviewResult] = {}
comparisons_store: dict[str, ComparisonResult] = {}
reviewer = ClaudeReviewer()


@router.post("/review", response_model=ReviewResult)
async def review_document(request: ReviewRequest):
    doc = documents_store.get(request.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    result = await reviewer.review_document(
        document=doc,
        review_focus=request.review_focus,
        custom_instructions=request.custom_instructions,
    )
    reviews_store[result.id] = result
    return result


@router.get("/", response_model=list[ReviewResult])
async def list_reviews():
    return list(reviews_store.values())


@router.get("/{review_id}", response_model=ReviewResult)
async def get_review(review_id: str):
    review = reviews_store.get(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.patch("/{review_id}/issues/{issue_id}/resolve")
async def resolve_issue(review_id: str, issue_id: str):
    review = reviews_store.get(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    for issue in review.issues:
        if issue.id == issue_id:
            issue.resolved = True
            return issue
    raise HTTPException(status_code=404, detail="Issue not found")


@router.post("/compare", response_model=ComparisonResult)
async def compare_documents(request: CompareRequest):
    docs = []
    for doc_id in request.document_ids:
        doc = documents_store.get(doc_id)
        if not doc:
            raise HTTPException(
                status_code=404, detail=f"Document {doc_id} not found"
            )
        docs.append(doc)

    result = await reviewer.compare_documents(
        documents=docs, comparison_focus=request.comparison_focus
    )
    comparisons_store[result.id] = result
    return result


@router.post("/report")
async def generate_report(request: ReportRequest):
    reviews = []
    for review_id in request.review_ids:
        review = reviews_store.get(review_id)
        if not review:
            raise HTTPException(
                status_code=404, detail=f"Review {review_id} not found"
            )
        reviews.append(review)

    report = await reviewer.generate_report(
        reviews=reviews, include_details=request.include_details
    )
    return {"report": report, "format": request.report_format}
