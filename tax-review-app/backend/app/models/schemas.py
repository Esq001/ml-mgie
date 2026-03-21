from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DocumentType(str, Enum):
    TAX_RETURN = "tax_return"
    WORK_PAPER = "work_paper"
    SCHEDULE = "schedule"
    SUPPORTING_DOC = "supporting_doc"
    OTHER = "other"


class UploadedDocument(BaseModel):
    id: str
    filename: str
    file_type: str
    document_type: DocumentType = DocumentType.OTHER
    upload_time: datetime = Field(default_factory=datetime.utcnow)
    size_bytes: int = 0
    page_count: int | None = None
    extracted_text: str = ""


class ReviewIssue(BaseModel):
    id: str
    severity: IssueSeverity
    category: str
    title: str
    description: str
    location: str = ""
    recommendation: str = ""
    resolved: bool = False


class ReviewResult(BaseModel):
    id: str
    document_id: str
    status: ReviewStatus = ReviewStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    summary: str = ""
    issues: list[ReviewIssue] = []
    key_findings: list[str] = []
    tax_year: str = ""
    entity_name: str = ""
    return_type: str = ""
    total_income: str = ""
    total_deductions: str = ""
    tax_liability: str = ""
    raw_analysis: str = ""


class ComparisonResult(BaseModel):
    id: str
    document_ids: list[str]
    summary: str = ""
    discrepancies: list[ReviewIssue] = []
    reconciliation_notes: list[str] = []
    status: ReviewStatus = ReviewStatus.PENDING


class ReviewRequest(BaseModel):
    document_id: str
    review_focus: list[str] = []
    custom_instructions: str = ""


class CompareRequest(BaseModel):
    document_ids: list[str]
    comparison_focus: str = ""


class ReportRequest(BaseModel):
    review_ids: list[str]
    include_details: bool = True
    report_format: str = "markdown"
