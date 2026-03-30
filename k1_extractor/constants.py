"""
K-1 form field definitions for all three IRS Schedule K-1 variants.

Each variant maps box IDs to their official field labels as they appear
on the IRS forms. These are used for both regex-based extraction and
Excel column headers.
"""

# =============================================================================
# Form 1065 - Schedule K-1 (Partner's Share of Income, Deductions, Credits)
# =============================================================================

FORM_1065_BOXES = {
    "1": "Ordinary business income (loss)",
    "2": "Net rental real estate income (loss)",
    "3": "Other net rental income (loss)",
    "4a": "Guaranteed payments for services",
    "4b": "Guaranteed payments for capital",
    "4c": "Total guaranteed payments",
    "5": "Interest income",
    "6a": "Ordinary dividends",
    "6b": "Qualified dividends",
    "6c": "Dividend equivalents",
    "7": "Royalties",
    "8": "Net short-term capital gain (loss)",
    "9a": "Net long-term capital gain (loss)",
    "9b": "Collectibles (28%) gain (loss)",
    "9c": "Unrecaptured section 1250 gain",
    "10": "Net section 1231 gain (loss)",
    "11": "Other income (loss)",
    "12": "Section 179 deduction",
    "13": "Other deductions",
    "14": "Self-employment earnings (loss)",
    "15": "Credits",
    "16": "Foreign transactions",
    "17": "Alternative minimum tax (AMT) items",
    "18": "Tax-exempt income and nondeductible expenses",
    "19": "Distributions",
    "20": "Other information",
}

FORM_1065_ENTITY_LABEL = "Partnership"
FORM_1065_RECIPIENT_LABEL = "Partner"

# =============================================================================
# Form 1120-S - Schedule K-1 (Shareholder's Share of Income, Deductions, Credits)
# =============================================================================

FORM_1120S_BOXES = {
    "1": "Ordinary business income (loss)",
    "2": "Net rental real estate income (loss)",
    "3": "Other net rental income (loss)",
    "4": "Interest income",
    "5a": "Ordinary dividends",
    "5b": "Qualified dividends",
    "6": "Royalties",
    "7": "Net short-term capital gain (loss)",
    "8a": "Net long-term capital gain (loss)",
    "8b": "Collectibles (28%) gain (loss)",
    "8c": "Unrecaptured section 1250 gain",
    "9": "Net section 1231 gain (loss)",
    "10": "Other income (loss)",
    "11": "Section 179 deduction",
    "12": "Other deductions",
    "13": "Credits",
    "14": "Foreign transactions",
    "15": "Alternative minimum tax (AMT) items",
    "16": "Items affecting shareholder basis",
    "17": "Other information",
}

FORM_1120S_ENTITY_LABEL = "S Corporation"
FORM_1120S_RECIPIENT_LABEL = "Shareholder"

# =============================================================================
# Form 1041 - Schedule K-1 (Beneficiary's Share of Income, Deductions, Credits)
# =============================================================================

FORM_1041_BOXES = {
    "1": "Interest income",
    "2a": "Ordinary dividends",
    "2b": "Qualified dividends",
    "3": "Net short-term capital gain",
    "4a": "Net long-term capital gain",
    "4b": "28% rate gain",
    "4c": "Unrecaptured section 1250 gain",
    "5": "Other portfolio and nonbusiness income",
    "6": "Ordinary business income",
    "7": "Net rental real estate income",
    "8": "Other rental income",
    "9": "Directly apportioned deductions",
    "10": "Estate tax deduction",
    "11": "Final year deductions",
    "12": "Alternative minimum tax adjustment",
    "13": "Credits and credit recapture",
    "14": "Other information",
}

FORM_1041_ENTITY_LABEL = "Estate or Trust"
FORM_1041_RECIPIENT_LABEL = "Beneficiary"

# =============================================================================
# Mapping of form types to their definitions
# =============================================================================

FORM_DEFINITIONS = {
    "1065": {
        "boxes": FORM_1065_BOXES,
        "entity_label": FORM_1065_ENTITY_LABEL,
        "recipient_label": FORM_1065_RECIPIENT_LABEL,
        "form_title": "Schedule K-1 (Form 1065)",
        "description": "Partner's Share of Income, Deductions, Credits, etc.",
    },
    "1120S": {
        "boxes": FORM_1120S_BOXES,
        "entity_label": FORM_1120S_ENTITY_LABEL,
        "recipient_label": FORM_1120S_RECIPIENT_LABEL,
        "form_title": "Schedule K-1 (Form 1120-S)",
        "description": "Shareholder's Share of Income, Deductions, Credits, etc.",
    },
    "1041": {
        "boxes": FORM_1041_BOXES,
        "entity_label": FORM_1041_ENTITY_LABEL,
        "recipient_label": FORM_1041_RECIPIENT_LABEL,
        "form_title": "Schedule K-1 (Form 1041)",
        "description": "Beneficiary's Share of Income, Deductions, Credits, etc.",
    },
}

# All box IDs across all form types (union), used for Excel column generation
ALL_BOX_IDS = sorted(
    set(FORM_1065_BOXES.keys()) | set(FORM_1120S_BOXES.keys()) | set(FORM_1041_BOXES.keys()),
    key=lambda x: (int("".join(c for c in x if c.isdigit()) or "0"), x),
)
