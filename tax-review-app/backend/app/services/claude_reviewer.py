import uuid
from datetime import datetime

import anthropic

from app.config import settings
from app.models.schemas import (
    ComparisonResult,
    IssueSeverity,
    ReviewIssue,
    ReviewResult,
    ReviewStatus,
    UploadedDocument,
)
from app.services.document_processor import DocumentProcessor

SYSTEM_PROMPT = """You are an expert tax reviewer and CPA with deep knowledge of:
- US federal and state tax law (IRC, Treasury Regulations)
- IRS forms (1040, 1120, 1065, 990, schedules, etc.)
- Tax work paper preparation and review procedures
- Common tax return errors, omissions, and compliance issues
- Tax planning opportunities and risk areas

When reviewing tax documents, you should:
1. Identify mathematical errors, inconsistencies between forms/schedules
2. Flag missing required schedules, forms, or disclosures
3. Check for compliance with current tax law
4. Identify potential audit risk areas
5. Note unusual items that warrant further investigation
6. Verify proper classification of income, deductions, and credits
7. Check carryforward/carryback items for accuracy
8. Review related party transactions for proper disclosure

Provide your analysis in a structured format with clear categories and severity levels."""


class ClaudeReviewer:
    """Handles Claude API calls for tax document review."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.doc_processor = DocumentProcessor()

    async def review_document(
        self,
        document: UploadedDocument,
        review_focus: list[str] | None = None,
        custom_instructions: str = "",
    ) -> ReviewResult:
        review_id = str(uuid.uuid4())
        result = ReviewResult(
            id=review_id,
            document_id=document.id,
            status=ReviewStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
        )

        try:
            # Build the message content
            content_blocks = self._build_content_blocks(
                document, review_focus, custom_instructions
            )

            response = self.client.messages.create(
                model=settings.claude_model,
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": content_blocks}],
            )

            analysis_text = response.content[0].text
            result = self._parse_review_response(result, analysis_text)
            result.status = ReviewStatus.COMPLETED
            result.completed_at = datetime.utcnow()

        except Exception as e:
            result.status = ReviewStatus.FAILED
            result.summary = f"Review failed: {str(e)}"

        return result

    async def compare_documents(
        self,
        documents: list[UploadedDocument],
        comparison_focus: str = "",
    ) -> ComparisonResult:
        comp_id = str(uuid.uuid4())
        result = ComparisonResult(
            id=comp_id,
            document_ids=[d.id for d in documents],
            status=ReviewStatus.IN_PROGRESS,
        )

        try:
            content_blocks = self._build_comparison_blocks(
                documents, comparison_focus
            )

            response = self.client.messages.create(
                model=settings.claude_model,
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": content_blocks}],
            )

            analysis_text = response.content[0].text
            result = self._parse_comparison_response(result, analysis_text)
            result.status = ReviewStatus.COMPLETED

        except Exception as e:
            result.status = ReviewStatus.FAILED
            result.summary = f"Comparison failed: {str(e)}"

        return result

    async def generate_report(
        self, reviews: list[ReviewResult], include_details: bool = True
    ) -> str:
        review_summaries = []
        for r in reviews:
            issues_text = ""
            if include_details:
                for issue in r.issues:
                    issues_text += (
                        f"  - [{issue.severity.value.upper()}] {issue.title}: "
                        f"{issue.description}\n"
                    )
            review_summaries.append(
                f"Document: {r.document_id}\n"
                f"Status: {r.status.value}\n"
                f"Entity: {r.entity_name}\n"
                f"Tax Year: {r.tax_year}\n"
                f"Return Type: {r.return_type}\n"
                f"Summary: {r.summary}\n"
                f"Issues ({len(r.issues)}):\n{issues_text}\n"
                f"Key Findings:\n"
                + "\n".join(f"  - {f}" for f in r.key_findings)
            )

        prompt = (
            "Generate a comprehensive tax review report based on these "
            "individual document reviews. Include an executive summary, "
            "consolidated findings, risk assessment, and recommendations.\n\n"
            + "\n---\n".join(review_summaries)
        )

        response = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def _build_content_blocks(
        self,
        document: UploadedDocument,
        review_focus: list[str] | None,
        custom_instructions: str,
    ) -> list[dict]:
        blocks: list[dict] = []

        # Add any images (scanned pages)
        image_blocks = self.doc_processor.get_image_blocks(
            document.extracted_text
        )
        blocks.extend(image_blocks)

        # Build the text prompt
        text_content = self.doc_processor.get_text_content(
            document.extracted_text
        )

        prompt = (
            f"Please review the following tax document.\n\n"
            f"Document: {document.filename}\n"
            f"Type: {document.document_type.value}\n"
            f"Pages: {document.page_count or 'N/A'}\n\n"
        )

        if review_focus:
            prompt += (
                "Focus areas for this review:\n"
                + "\n".join(f"- {f}" for f in review_focus)
                + "\n\n"
            )

        if custom_instructions:
            prompt += f"Additional instructions: {custom_instructions}\n\n"

        prompt += (
            f"Document content:\n"
            f"{'=' * 60}\n"
            f"{text_content}\n"
            f"{'=' * 60}\n\n"
            "Please provide your review in the following structured format:\n\n"
            "ENTITY NAME: [name]\n"
            "TAX YEAR: [year]\n"
            "RETURN TYPE: [type]\n"
            "TOTAL INCOME: [amount]\n"
            "TOTAL DEDUCTIONS: [amount]\n"
            "TAX LIABILITY: [amount]\n\n"
            "SUMMARY:\n[overall summary of the document and review]\n\n"
            "ISSUES:\n"
            "For each issue use this format:\n"
            "- SEVERITY: [HIGH/MEDIUM/LOW/INFO]\n"
            "  CATEGORY: [category]\n"
            "  TITLE: [brief title]\n"
            "  DESCRIPTION: [detailed description]\n"
            "  LOCATION: [where in the document]\n"
            "  RECOMMENDATION: [what to do]\n\n"
            "KEY FINDINGS:\n- [finding 1]\n- [finding 2]\n..."
        )

        blocks.append({"type": "text", "text": prompt})
        return blocks

    def _build_comparison_blocks(
        self,
        documents: list[UploadedDocument],
        comparison_focus: str,
    ) -> list[dict]:
        blocks: list[dict] = []

        prompt = (
            "Please compare the following tax documents and identify "
            "discrepancies, inconsistencies, and reconciliation items.\n\n"
        )

        if comparison_focus:
            prompt += f"Comparison focus: {comparison_focus}\n\n"

        for i, doc in enumerate(documents, 1):
            text_content = self.doc_processor.get_text_content(
                doc.extracted_text
            )
            prompt += (
                f"DOCUMENT {i}: {doc.filename}\n"
                f"Type: {doc.document_type.value}\n"
                f"{'=' * 40}\n"
                f"{text_content}\n"
                f"{'=' * 40}\n\n"
            )

            image_blocks = self.doc_processor.get_image_blocks(
                doc.extracted_text
            )
            blocks.extend(image_blocks)

        prompt += (
            "Provide your comparison in this format:\n\n"
            "SUMMARY:\n[overall comparison summary]\n\n"
            "DISCREPANCIES:\n"
            "For each discrepancy:\n"
            "- SEVERITY: [HIGH/MEDIUM/LOW/INFO]\n"
            "  CATEGORY: [category]\n"
            "  TITLE: [brief title]\n"
            "  DESCRIPTION: [detailed description]\n"
            "  RECOMMENDATION: [what to do]\n\n"
            "RECONCILIATION NOTES:\n- [note 1]\n- [note 2]\n..."
        )

        blocks.append({"type": "text", "text": prompt})
        return blocks

    def _parse_review_response(
        self, result: ReviewResult, text: str
    ) -> ReviewResult:
        result.raw_analysis = text

        # Extract structured fields
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("ENTITY NAME:"):
                result.entity_name = line.split(":", 1)[1].strip()
            elif line.startswith("TAX YEAR:"):
                result.tax_year = line.split(":", 1)[1].strip()
            elif line.startswith("RETURN TYPE:"):
                result.return_type = line.split(":", 1)[1].strip()
            elif line.startswith("TOTAL INCOME:"):
                result.total_income = line.split(":", 1)[1].strip()
            elif line.startswith("TOTAL DEDUCTIONS:"):
                result.total_deductions = line.split(":", 1)[1].strip()
            elif line.startswith("TAX LIABILITY:"):
                result.tax_liability = line.split(":", 1)[1].strip()

        # Extract summary
        if "SUMMARY:" in text:
            summary_start = text.index("SUMMARY:") + len("SUMMARY:")
            summary_end = text.find("\nISSUES:", summary_start)
            if summary_end == -1:
                summary_end = text.find("\nKEY FINDINGS:", summary_start)
            if summary_end == -1:
                summary_end = summary_start + 1000
            result.summary = text[summary_start:summary_end].strip()

        # Extract issues
        result.issues = self._parse_issues(text)

        # Extract key findings
        if "KEY FINDINGS:" in text:
            findings_start = text.index("KEY FINDINGS:") + len("KEY FINDINGS:")
            findings_text = text[findings_start:]
            for line in findings_text.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    result.key_findings.append(line[2:])
                elif line and not line.startswith("- ") and result.key_findings:
                    break

        return result

    def _parse_comparison_response(
        self, result: ComparisonResult, text: str
    ) -> ComparisonResult:
        if "SUMMARY:" in text:
            summary_start = text.index("SUMMARY:") + len("SUMMARY:")
            summary_end = text.find("\nDISCREPANCIES:", summary_start)
            if summary_end == -1:
                summary_end = summary_start + 1000
            result.summary = text[summary_start:summary_end].strip()

        result.discrepancies = self._parse_issues(text)

        if "RECONCILIATION NOTES:" in text:
            notes_start = text.index("RECONCILIATION NOTES:") + len(
                "RECONCILIATION NOTES:"
            )
            notes_text = text[notes_start:]
            for line in notes_text.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    result.reconciliation_notes.append(line[2:])
                elif (
                    line
                    and not line.startswith("- ")
                    and result.reconciliation_notes
                ):
                    break

        return result

    def _parse_issues(self, text: str) -> list[ReviewIssue]:
        issues = []
        current_issue: dict = {}

        in_issues = False
        for line in text.split("\n"):
            stripped = line.strip()

            if stripped.startswith("ISSUES:") or stripped.startswith(
                "DISCREPANCIES:"
            ):
                in_issues = True
                continue

            if in_issues and stripped.startswith("KEY FINDINGS:"):
                break
            if in_issues and stripped.startswith("RECONCILIATION NOTES:"):
                break

            if not in_issues:
                continue

            if stripped.startswith("- SEVERITY:"):
                if current_issue.get("severity"):
                    issues.append(self._make_issue(current_issue))
                    current_issue = {}
                current_issue["severity"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("CATEGORY:"):
                current_issue["category"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("TITLE:"):
                current_issue["title"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("DESCRIPTION:"):
                current_issue["description"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("LOCATION:"):
                current_issue["location"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("RECOMMENDATION:"):
                current_issue["recommendation"] = (
                    stripped.split(":", 1)[1].strip()
                )

        if current_issue.get("severity"):
            issues.append(self._make_issue(current_issue))

        return issues

    def _make_issue(self, data: dict) -> ReviewIssue:
        severity_map = {
            "HIGH": IssueSeverity.HIGH,
            "MEDIUM": IssueSeverity.MEDIUM,
            "LOW": IssueSeverity.LOW,
            "INFO": IssueSeverity.INFO,
        }
        return ReviewIssue(
            id=str(uuid.uuid4()),
            severity=severity_map.get(
                data.get("severity", "").upper(), IssueSeverity.INFO
            ),
            category=data.get("category", "General"),
            title=data.get("title", "Untitled Issue"),
            description=data.get("description", ""),
            location=data.get("location", ""),
            recommendation=data.get("recommendation", ""),
        )
