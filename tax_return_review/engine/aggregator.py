"""Aggregates source documents into expected 1040 line item values."""

from decimal import Decimal

from ..models.tax_data import Form1099Data, LineItem, ParsedDocuments, TaxReturn, W2Data


def aggregate_source_documents(docs: ParsedDocuments) -> TaxReturn:
    """Roll up W-2s and 1099s into expected 1040 line values.

    This creates a synthetic TaxReturn representing what the source
    documents indicate the return should contain.
    """
    expected = TaxReturn(source_file="[Aggregated Source Documents]")
    items = []

    # Line 1: Wages = sum of all W-2 Box 1
    total_wages = sum((w2.wages for w2 in docs.w2s), Decimal("0"))
    if total_wages > 0:
        items.append(LineItem(
            form="1040", line="1", label="Wages, salaries, tips",
            amount=total_wages, source_file="W-2 total",
        ))

    # Line 2b: Taxable interest = sum of 1099-INT Box 1
    total_interest = Decimal("0")
    for f in docs.form_1099s:
        if f.variant == "INT":
            total_interest += f.box_amounts.get("1", Decimal("0"))
    if total_interest > 0:
        items.append(LineItem(
            form="1040", line="2b", label="Taxable interest",
            amount=total_interest, source_file="1099-INT total",
        ))

    # Line 3b: Ordinary dividends = sum of 1099-DIV Box 1a
    total_div = Decimal("0")
    for f in docs.form_1099s:
        if f.variant == "DIV":
            total_div += f.box_amounts.get("1a", Decimal("0"))
    if total_div > 0:
        items.append(LineItem(
            form="1040", line="3b", label="Ordinary dividends",
            amount=total_div, source_file="1099-DIV total",
        ))

    # Line 3a: Qualified dividends = sum of 1099-DIV Box 1b
    total_qual_div = Decimal("0")
    for f in docs.form_1099s:
        if f.variant == "DIV":
            total_qual_div += f.box_amounts.get("1b", Decimal("0"))
    if total_qual_div > 0:
        items.append(LineItem(
            form="1040", line="3a", label="Qualified dividends",
            amount=total_qual_div, source_file="1099-DIV total",
        ))

    # Line 4b: IRA/pension distributions from 1099-R Box 2a
    total_pension_taxable = Decimal("0")
    for f in docs.form_1099s:
        if f.variant == "R":
            total_pension_taxable += f.box_amounts.get("2a", Decimal("0"))
    if total_pension_taxable > 0:
        items.append(LineItem(
            form="1040", line="4b", label="IRA distributions taxable",
            amount=total_pension_taxable, source_file="1099-R total",
        ))

    # Line 25a: Federal withholding from W-2s
    total_w2_withholding = sum(
        (w2.federal_tax_withheld for w2 in docs.w2s), Decimal("0")
    )
    if total_w2_withholding > 0:
        items.append(LineItem(
            form="1040", line="25a", label="W-2 withholding",
            amount=total_w2_withholding, source_file="W-2 total",
        ))

    # Line 25b: Federal withholding from 1099s
    total_1099_withholding = Decimal("0")
    for f in docs.form_1099s:
        total_1099_withholding += f.federal_tax_withheld
    if total_1099_withholding > 0:
        items.append(LineItem(
            form="1040", line="25b", label="1099 withholding",
            amount=total_1099_withholding, source_file="1099 total",
        ))

    # Line 25d: Total federal withholding
    total_withholding = total_w2_withholding + total_1099_withholding
    if total_withholding > 0:
        items.append(LineItem(
            form="1040", line="25d", label="Total federal tax withheld",
            amount=total_withholding, source_file="All sources",
        ))

    expected.line_items = items
    return expected
