"""Data models for comparison reports."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from ..models.enums import DiscrepancyLevel


@dataclass
class ReportItem:
    """A single line item comparison result."""
    line: str = ""
    label: str = ""
    prior_year_value: Optional[Decimal] = None
    source_doc_value: Optional[Decimal] = None
    draft_value: Optional[Decimal] = None
    status: DiscrepancyLevel = DiscrepancyLevel.MATCH
    notes: str = ""


@dataclass
class ComparisonReport:
    """Complete comparison report."""
    generated_at: datetime = field(default_factory=datetime.now)
    prior_year_file: str = ""
    source_doc_files: list[str] = field(default_factory=list)
    draft_file: str = ""
    items: list[ReportItem] = field(default_factory=list)
    summary: str = ""
