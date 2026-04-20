import { Money } from "../money.js";
import { AUTH } from "../authorities.js";
import { lineResult, type LineResult } from "../provenance.js";
import { taxFromBrackets } from "../tax-brackets-2025.js";
import type { Form1040Inputs } from "./inputs.js";
import type { Form1040Lines1Through38 } from "./lines-1-38.js";

const d = (n: number): Money => Money.fromDollars(n);

/**
 * Additional inputs needed for lines 16 through 38. These originate from
 * Schedules 2 and 3, Schedule 8812, EIC Worksheet, Form 8863, and payment
 * documents (W-2 Box 2, 1099 withholding, estimated payments).
 */
export interface Form1040Lines16Through38Inputs {
  /** Override for the tax on Line 16 when Schedule D Tax Wksht / QDCGW applies. */
  line16Override?: number;
  /** Schedule 2, line 3 (AMT + excess APTC repayment). */
  schedule2Line3: number;
  /** Schedule 8812, child tax credit + ODC (nonrefundable portion on line 19). */
  line19CtcOdc: number;
  /** Schedule 3, line 8 (nonrefundable credits). */
  schedule3Line8: number;
  /** Schedule 2, line 21 (other taxes). */
  schedule2Line21: number;
  /** Federal income tax withheld. */
  withholding: {
    fromW2Box2: number; // 25a
    from1099: number; // 25b
    fromOther: number; // 25c
  };
  /** 2025 estimated tax payments and amount applied from 2024 return. */
  estimatedPayments: number; // 26
  /** Earned income credit (Line 27). */
  earnedIncomeCredit: number; // 27
  /** Additional CTC from Sched 8812 (Line 28). */
  additionalCtc: number; // 28
  /** American opportunity credit refundable portion (Form 8863 Line 8). */
  americanOpportunityCredit: number; // 29
  /** Schedule 3, line 15 (refundable credits + payments). */
  schedule3Line15: number; // 31
  /** Amount of overpayment the taxpayer wants applied to 2026 estimated tax. */
  appliedToNextYearEstimated: number; // 36
  /** Form 2210 estimated tax penalty. */
  estimatedTaxPenalty: number; // 38
}

export interface Form1040Lines16Through38 {
  line16: LineResult;
  line17: LineResult;
  line18: LineResult;
  line19: LineResult;
  line20: LineResult;
  line21: LineResult;
  line22: LineResult;
  line23: LineResult;
  line24: LineResult;
  line25a: LineResult;
  line25b: LineResult;
  line25c: LineResult;
  line25d: LineResult;
  line26: LineResult;
  line27: LineResult;
  line28: LineResult;
  line29: LineResult;
  line31: LineResult;
  line32: LineResult;
  line33: LineResult;
  line34: LineResult;
  line35a: LineResult;
  line36: LineResult;
  line37: LineResult;
  line38: LineResult;
}

export function computeForm1040Lines16Through38(
  input: Form1040Inputs,
  upstream: Form1040Lines1Through38,
  extra: Form1040Lines16Through38Inputs,
): Form1040Lines16Through38 {
  // Line 16: tax. If override supplied (Schedule D Tax Wksht, QDCGTW, etc.) use it.
  const line16Value =
    extra.line16Override !== undefined
      ? d(extra.line16Override).roundToDollar()
      : taxFromBrackets(upstream.line15.value, input.filingStatus);
  const line16 = lineResult(
    "1040.L16",
    line16Value,
    extra.line16Override !== undefined
      ? "Tax from Schedule D Tax Worksheet, Qualified Div/Cap Gain Worksheet, or other method."
      : "Tax from 2025 tax brackets applied to line 15.",
    [
      { ref: "1040.L15", value: upstream.line15.value },
      { ref: "input.filingStatus", value: input.filingStatus },
    ],
    [AUTH.IRC_1, AUTH.FORM_1040_INSTR],
  );

  const line17 = lineResult(
    "1040.L17",
    d(extra.schedule2Line3).roundToDollar(),
    "Amount from Schedule 2, line 3 (AMT + excess advance premium tax credit).",
    [{ ref: "sched-2.L3", value: d(extra.schedule2Line3) }],
    [AUTH.FORM_1040_INSTR],
  );

  const line18 = lineResult(
    "1040.L18",
    line16.value.add(line17.value).roundToDollar(),
    "Sum of lines 16 and 17.",
    [
      { ref: "1040.L16", value: line16.value },
      { ref: "1040.L17", value: line17.value },
    ],
    [AUTH.FORM_1040_INSTR],
  );

  const line19 = lineResult(
    "1040.L19",
    d(extra.line19CtcOdc).roundToDollar(),
    "Child tax credit and credit for other dependents (Schedule 8812).",
    [{ ref: "sched-8812.nonrefundable", value: d(extra.line19CtcOdc) }],
    [AUTH.FORM_1040_INSTR],
  );

  const line20 = lineResult(
    "1040.L20",
    d(extra.schedule3Line8).roundToDollar(),
    "Amount from Schedule 3, line 8 (nonrefundable credits).",
    [{ ref: "sched-3.L8", value: d(extra.schedule3Line8) }],
    [AUTH.FORM_1040_INSTR],
  );

  const line21 = lineResult(
    "1040.L21",
    line19.value.add(line20.value).roundToDollar(),
    "Sum of lines 19 and 20.",
    [
      { ref: "1040.L19", value: line19.value },
      { ref: "1040.L20", value: line20.value },
    ],
    [AUTH.FORM_1040_INSTR],
  );

  const line22Raw = line18.value.subtract(line21.value);
  const line22Value = line22Raw.isNegative() ? Money.zero() : line22Raw.roundToDollar();
  const line22 = lineResult(
    "1040.L22",
    line22Value,
    "Subtract line 21 from line 18; if zero or less, enter -0-.",
    [
      { ref: "1040.L18", value: line18.value },
      { ref: "1040.L21", value: line21.value },
    ],
    [AUTH.FORM_1040_INSTR],
  );

  const line23 = lineResult(
    "1040.L23",
    d(extra.schedule2Line21).roundToDollar(),
    "Other taxes from Schedule 2, line 21.",
    [{ ref: "sched-2.L21", value: d(extra.schedule2Line21) }],
    [AUTH.FORM_1040_INSTR],
  );

  const line24 = lineResult(
    "1040.L24",
    line22.value.add(line23.value).roundToDollar(),
    "Total tax: sum of lines 22 and 23.",
    [
      { ref: "1040.L22", value: line22.value },
      { ref: "1040.L23", value: line23.value },
    ],
    [AUTH.FORM_1040_INSTR],
  );

  const line25a = lineResult(
    "1040.L25a",
    d(extra.withholding.fromW2Box2).roundToDollar(),
    "Federal income tax withheld from Forms W-2, Box 2.",
    [{ ref: "w2.box2", value: d(extra.withholding.fromW2Box2) }],
    [AUTH.FORM_1040_INSTR],
  );
  const line25b = lineResult(
    "1040.L25b",
    d(extra.withholding.from1099).roundToDollar(),
    "Federal income tax withheld from Forms 1099.",
    [{ ref: "1099.withholding", value: d(extra.withholding.from1099) }],
    [AUTH.FORM_1040_INSTR],
  );
  const line25c = lineResult(
    "1040.L25c",
    d(extra.withholding.fromOther).roundToDollar(),
    "Federal income tax withheld from other forms (W-2G, etc.).",
    [{ ref: "other.withholding", value: d(extra.withholding.fromOther) }],
    [AUTH.FORM_1040_INSTR],
  );
  const line25d = lineResult(
    "1040.L25d",
    Money.sum([line25a.value, line25b.value, line25c.value]).roundToDollar(),
    "Sum of lines 25a through 25c.",
    [
      { ref: "1040.L25a", value: line25a.value },
      { ref: "1040.L25b", value: line25b.value },
      { ref: "1040.L25c", value: line25c.value },
    ],
    [AUTH.FORM_1040_INSTR],
  );

  const line26 = lineResult(
    "1040.L26",
    d(extra.estimatedPayments).roundToDollar(),
    "2025 estimated tax payments and amount applied from 2024 return.",
    [{ ref: "payments.estimated", value: d(extra.estimatedPayments) }],
    [AUTH.FORM_1040_INSTR],
  );

  const line27 = lineResult(
    "1040.L27",
    d(extra.earnedIncomeCredit).roundToDollar(),
    "Earned income credit (EIC).",
    [{ ref: "eic-worksheet.result", value: d(extra.earnedIncomeCredit) }],
    [AUTH.FORM_1040_INSTR],
  );

  const line28 = lineResult(
    "1040.L28",
    d(extra.additionalCtc).roundToDollar(),
    "Additional child tax credit from Schedule 8812.",
    [{ ref: "sched-8812.refundable", value: d(extra.additionalCtc) }],
    [AUTH.FORM_1040_INSTR],
  );

  const line29 = lineResult(
    "1040.L29",
    d(extra.americanOpportunityCredit).roundToDollar(),
    "American opportunity credit refundable portion from Form 8863, line 8.",
    [{ ref: "form-8863.L8", value: d(extra.americanOpportunityCredit) }],
    [AUTH.FORM_1040_INSTR],
  );

  const line31 = lineResult(
    "1040.L31",
    d(extra.schedule3Line15).roundToDollar(),
    "Amount from Schedule 3, line 15 (refundable credits and payments).",
    [{ ref: "sched-3.L15", value: d(extra.schedule3Line15) }],
    [AUTH.FORM_1040_INSTR],
  );

  const line32 = lineResult(
    "1040.L32",
    Money.sum([line27.value, line28.value, line29.value, line31.value]).roundToDollar(),
    "Total other payments and refundable credits: lines 27 + 28 + 29 + 31.",
    [
      { ref: "1040.L27", value: line27.value },
      { ref: "1040.L28", value: line28.value },
      { ref: "1040.L29", value: line29.value },
      { ref: "1040.L31", value: line31.value },
    ],
    [AUTH.FORM_1040_INSTR],
  );

  const line33 = lineResult(
    "1040.L33",
    Money.sum([line25d.value, line26.value, line32.value]).roundToDollar(),
    "Total payments: lines 25d + 26 + 32.",
    [
      { ref: "1040.L25d", value: line25d.value },
      { ref: "1040.L26", value: line26.value },
      { ref: "1040.L32", value: line32.value },
    ],
    [AUTH.FORM_1040_INSTR],
  );

  // Line 34 overpayment = line 33 - line 24 if > 0 else 0.
  const overpaymentRaw = line33.value.subtract(line24.value);
  const line34Value = overpaymentRaw.isNegative() ? Money.zero() : overpaymentRaw.roundToDollar();
  const line34 = lineResult(
    "1040.L34",
    line34Value,
    "Overpayment: line 33 minus line 24 when positive, else zero.",
    [
      { ref: "1040.L33", value: line33.value },
      { ref: "1040.L24", value: line24.value },
    ],
    [AUTH.FORM_1040_INSTR],
  );

  const line36Capped = Money.fromDollars(
    Math.min(extra.appliedToNextYearEstimated, line34.value.toDollars()),
  );
  const line36 = lineResult(
    "1040.L36",
    line36Capped.roundToDollar(),
    "Amount of overpayment applied to 2026 estimated tax (cannot exceed line 34).",
    [
      { ref: "1040.L34", value: line34.value },
      { ref: "input.appliedToNextYear", value: d(extra.appliedToNextYearEstimated) },
    ],
    [AUTH.FORM_1040_INSTR],
  );

  // Line 35a = line 34 - line 36 (amount to be refunded).
  const line35aValue = line34.value.subtract(line36.value).roundToDollar();
  const line35a = lineResult(
    "1040.L35a",
    line35aValue.isNegative() ? Money.zero() : line35aValue,
    "Amount of overpayment refunded: line 34 minus line 36.",
    [
      { ref: "1040.L34", value: line34.value },
      { ref: "1040.L36", value: line36.value },
    ],
    [AUTH.FORM_1040_INSTR],
  );

  // Line 37 amount you owe = line 24 - line 33 if > 0 else 0.
  const owedRaw = line24.value.subtract(line33.value);
  const line37Value = owedRaw.isNegative() ? Money.zero() : owedRaw.roundToDollar();
  const line37 = lineResult(
    "1040.L37",
    line37Value,
    "Amount you owe: line 24 minus line 33 when positive, else zero.",
    [
      { ref: "1040.L24", value: line24.value },
      { ref: "1040.L33", value: line33.value },
    ],
    [AUTH.FORM_1040_INSTR],
  );

  const line38 = lineResult(
    "1040.L38",
    d(extra.estimatedTaxPenalty).roundToDollar(),
    "Estimated tax penalty from Form 2210 (included in line 37).",
    [{ ref: "form-2210.penalty", value: d(extra.estimatedTaxPenalty) }],
    [AUTH.FORM_1040_INSTR],
  );

  return {
    line16,
    line17,
    line18,
    line19,
    line20,
    line21,
    line22,
    line23,
    line24,
    line25a,
    line25b,
    line25c,
    line25d,
    line26,
    line27,
    line28,
    line29,
    line31,
    line32,
    line33,
    line34,
    line35a,
    line36,
    line37,
    line38,
  };
}
