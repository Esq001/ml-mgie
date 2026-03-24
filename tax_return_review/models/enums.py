"""Enumerations for tax return review application."""

from enum import Enum


class DocumentType(Enum):
    """Type of document being processed."""
    PRIOR_YEAR_RETURN = "prior_year_return"
    SOURCE_DOCUMENT = "source_document"
    DRAFT_RETURN = "draft_return"


class DiscrepancyLevel(Enum):
    """Severity level of a comparison discrepancy."""
    MATCH = "match"
    WARNING = "warning"
    ERROR = "error"
    MISSING = "missing"


class FormType(Enum):
    """Recognized tax form types."""
    FORM_1040 = "1040"
    W2 = "W-2"
    FORM_1099_INT = "1099-INT"
    FORM_1099_DIV = "1099-DIV"
    FORM_1099_NEC = "1099-NEC"
    FORM_1099_MISC = "1099-MISC"
    FORM_1099_R = "1099-R"
    FORM_1099_G = "1099-G"
    UNKNOWN = "unknown"
