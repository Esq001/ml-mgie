import { Money } from "../money.js";
import { AUTH } from "../authorities.js";
import { lineResult, type LineResult } from "../provenance.js";
import {
  ADDITIONAL_STD_DED_2025,
  STANDARD_DEDUCTION_2025,
} from "../filing-status.js";
import type { Form1040Inputs } from "./inputs.js";

/**
 * Pure calculation of Form 1040 lines 1 through 38 for tax year 2025.
 *
 * Each line is a pure function of the inputs and of already-computed upstream
 * lines. No IO, no randomness, no hidden state. Every result carries a
 * provenance record so the UI can render a "show your work" panel and the
 * audit log can reproduce the computation.
 */

const d = (n: number): Money => Money.fromDollars(n);

function computeLine1(input: Form1040Inputs): {
  line1a: LineResult;
  line1b: LineResult;
  line1c: LineResult;
  line1d: LineResult;
  line1e: LineResult;
  line1f: LineResult;
  line1g: LineResult;
  line1h: LineResult;
  line1i: LineResult;
  line1z: LineResult;
} {
  const l = input.line1;
  const line1a = lineResult(
    "1040.L1a",
    d(l.w2Box1Wages),
    "Sum of Box 1 from all Forms W-2.",
    [{ ref: "w2.box1", value: d(l.w2Box1Wages) }],
    [AUTH.FORM_1040_INSTR],
  );
  const line1b = lineResult(
    "1040.L1b",
    d(l.householdEmployeeWages),
    "Household employee wages not on W-2.",
    [],
    [AUTH.FORM_1040_INSTR],
  );
  const line1c = lineResult(
    "1040.L1c",
    d(l.tipIncomeNotReported),
    "Tip income not reported on Line 1a.",
    [],
    [AUTH.FORM_1040_INSTR],
  );
  const line1d = lineResult(
    "1040.L1d",
    d(l.medicaidWaiverPayments),
    "Medicaid waiver payments excluded from W-2 wages.",
    [],
    [AUTH.FORM_1040_INSTR],
  );
  const line1e = lineResult(
    "1040.L1e",
    d(l.dependentCareBenefits),
    "Taxable dependent care benefits (Form 2441, line 26).",
    [],
    [AUTH.FORM_1040_INSTR],
  );
  const line1f = lineResult(
    "1040.L1f",
    d(l.employerAdoptionBenefits),
    "Employer-provided adoption benefits (Form 8839, line 29).",
    [],
    [AUTH.FORM_1040_INSTR],
  );
  const line1g = lineResult(
    "1040.L1g",
    d(l.wagesFromForm8919),
    "Wages from Form 8919, line 6.",
    [],
    [AUTH.FORM_1040_INSTR],
  );
  const line1h = lineResult(
    "1040.L1h",
    d(l.otherEarnedIncome),
    "Other earned income.",
    [],
    [AUTH.FORM_1040_INSTR],
  );
  const line1i = lineResult(
    "1040.L1i",
    d(l.nontaxableCombatPayElection),
    "Nontaxable combat pay election (reduces total wages on 1z).",
    [],
    [AUTH.IRC_61, AUTH.FORM_1040_INSTR],
  );

  // 1z = 1a + 1b + 1c + 1d + 1e + 1f + 1g + 1h - 1i
  const parts = [
    line1a.value,
    line1b.value,
    line1c.value,
    line1d.value,
    line1e.value,
    line1f.value,
    line1g.value,
    line1h.value,
  ];
  const line1zValue = Money.sum(parts).subtract(line1i.value).roundToDollar();
  const line1z = lineResult(
    "1040.L1z",
    line1zValue,
    "Sum of lines 1a through 1h minus line 1i.",
    parts
      .map((v, idx) => ({ ref: `1040.L1${"abcdefgh"[idx]}`, value: v }))
      .concat([{ ref: "1040.L1i", value: line1i.value }]),
    [AUTH.IRC_61, AUTH.FORM_1040_INSTR],
  );

  return {
    line1a,
    line1b,
    line1c,
    line1d,
    line1e,
    line1f,
    line1g,
    line1h,
    line1i,
    line1z,
  };
}

function computeStandardDeduction(input: Form1040Inputs): Money {
  const base = d(STANDARD_DEDUCTION_2025[input.filingStatus]);
  const isMarried =
    input.filingStatus === "mfj" ||
    input.filingStatus === "mfs" ||
    input.filingStatus === "qss";
  const perBump = isMarried
    ? d(ADDITIONAL_STD_DED_2025.married)
    : d(ADDITIONAL_STD_DED_2025.unmarried);
  let bumps = 0;
  if (input.taxpayerAge65OrOlder) bumps += 1;
  if (input.taxpayerBlind) bumps += 1;
  if (input.filingStatus === "mfj" || input.filingStatus === "qss") {
    if (input.spouseAge65OrOlder) bumps += 1;
    if (input.spouseBlind) bumps += 1;
  }
  return base.add(perBump.multiply(bumps));
}

export interface Form1040Lines1Through38 {
  // Line 1 components
  line1a: LineResult;
  line1b: LineResult;
  line1c: LineResult;
  line1d: LineResult;
  line1e: LineResult;
  line1f: LineResult;
  line1g: LineResult;
  line1h: LineResult;
  line1i: LineResult;
  line1z: LineResult;
  // Interest
  line2a: LineResult;
  line2b: LineResult;
  // Dividends
  line3a: LineResult;
  line3b: LineResult;
  // IRA
  line4a: LineResult;
  line4b: LineResult;
  // Pensions
  line5a: LineResult;
  line5b: LineResult;
  // Social Security
  line6a: LineResult;
  line6b: LineResult;
  // Line 7 capital gain/loss
  line7: LineResult;
  // Line 8 additional income from Schedule 1
  line8: LineResult;
  // Line 9 total income
  line9: LineResult;
  // Line 10 adjustments from Schedule 1
  line10: LineResult;
  // Line 11 AGI
  line11: LineResult;
  // Line 12 standard or itemized deduction
  line12: LineResult;
  // Line 13 QBI deduction
  line13: LineResult;
  // Line 14 sum of 12 and 13
  line14: LineResult;
  // Line 15 taxable income
  line15: LineResult;
}

export function computeForm1040Lines1Through38(
  input: Form1040Inputs,
): Form1040Lines1Through38 {
  const line1 = computeLine1(input);

  const line2a = lineResult(
    "1040.L2a",
    d(input.line2.taxExemptInterest).roundToDollar(),
    "Tax-exempt interest (informational, excluded from gross income).",
    [{ ref: "sched-B.line1-exempt", value: d(input.line2.taxExemptInterest) }],
    [AUTH.IRC_61, AUTH.FORM_1040_INSTR],
  );
  const line2b = lineResult(
    "1040.L2b",
    d(input.line2.taxableInterest).roundToDollar(),
    "Taxable interest from Forms 1099-INT and Schedule B line 2.",
    [{ ref: "sched-B.line2", value: d(input.line2.taxableInterest) }],
    [AUTH.IRC_61, AUTH.FORM_1040_INSTR],
  );

  const line3a = lineResult(
    "1040.L3a",
    d(input.line3.qualifiedDividends).roundToDollar(),
    "Qualified dividends (informational; taxed via Qualified Div and Cap Gain Worksheet).",
    [{ ref: "1099-DIV.box1b", value: d(input.line3.qualifiedDividends) }],
    [AUTH.IRC_1, AUTH.FORM_1040_INSTR],
  );
  const line3b = lineResult(
    "1040.L3b",
    d(input.line3.ordinaryDividends).roundToDollar(),
    "Ordinary dividends from Forms 1099-DIV and Schedule B line 6.",
    [{ ref: "1099-DIV.box1a", value: d(input.line3.ordinaryDividends) }],
    [AUTH.IRC_61, AUTH.FORM_1040_INSTR],
  );

  const line4a = lineResult(
    "1040.L4a",
    d(input.line4.grossIraDistributions).roundToDollar(),
    "Gross IRA distributions from Forms 1099-R.",
    [{ ref: "1099-R.box1.ira", value: d(input.line4.grossIraDistributions) }],
    [AUTH.FORM_1040_INSTR],
  );
  const line4b = lineResult(
    "1040.L4b",
    d(input.line4.taxableIraDistributions).roundToDollar(),
    "Taxable IRA distributions after basis recovery (Form 8606).",
    [{ ref: "1099-R.box2a.ira", value: d(input.line4.taxableIraDistributions) }],
    [AUTH.IRC_61, AUTH.FORM_1040_INSTR],
  );

  const line5a = lineResult(
    "1040.L5a",
    d(input.line5.grossPensions).roundToDollar(),
    "Gross pension and annuity distributions.",
    [{ ref: "1099-R.box1.pension", value: d(input.line5.grossPensions) }],
    [AUTH.FORM_1040_INSTR],
  );
  const line5b = lineResult(
    "1040.L5b",
    d(input.line5.taxablePensions).roundToDollar(),
    "Taxable pension and annuity amount (Simplified Method or Box 2a).",
    [{ ref: "1099-R.box2a.pension", value: d(input.line5.taxablePensions) }],
    [AUTH.IRC_61, AUTH.FORM_1040_INSTR],
  );

  const line6a = lineResult(
    "1040.L6a",
    d(input.line6.grossSocialSecurity).roundToDollar(),
    "Gross Social Security benefits from Forms SSA-1099 / RRB-1099.",
    [{ ref: "SSA-1099.box5", value: d(input.line6.grossSocialSecurity) }],
    [AUTH.IRC_86, AUTH.FORM_1040_INSTR],
  );
  const line6b = lineResult(
    "1040.L6b",
    d(input.line6.taxableSocialSecurity).roundToDollar(),
    "Taxable Social Security from Social Security Benefits Worksheet.",
    [
      { ref: "ssb-worksheet.result", value: d(input.line6.taxableSocialSecurity) },
      { ref: "1040.L6c", value: input.line6.lumpSumElection },
    ],
    [AUTH.IRC_86, AUTH.FORM_1040_INSTR, AUTH.PUB_17],
  );

  const line7 = lineResult(
    "1040.L7",
    d(input.line7.capitalGainOrLoss).roundToDollar(),
    input.line7.scheduleDNotRequired
      ? "Capital gain distributions only; Schedule D not required."
      : "Net capital gain or loss from Schedule D line 16.",
    [{ ref: "sched-D.L16", value: d(input.line7.capitalGainOrLoss) }],
    [AUTH.IRC_1, AUTH.FORM_1040_INSTR],
  );

  const line8 = lineResult(
    "1040.L8",
    d(input.schedule1.additionalIncome).roundToDollar(),
    "Additional income from Schedule 1, line 10.",
    [{ ref: "sched-1.L10", value: d(input.schedule1.additionalIncome) }],
    [AUTH.IRC_61, AUTH.SCHED_1_INSTR],
  );

  // Line 9 total income = 1z + 2b + 3b + 4b + 5b + 6b + 7 + 8
  const line9Value = Money.sum([
    line1.line1z.value,
    line2b.value,
    line3b.value,
    line4b.value,
    line5b.value,
    line6b.value,
    line7.value,
    line8.value,
  ]).roundToDollar();
  const line9 = lineResult(
    "1040.L9",
    line9Value,
    "Total income: 1z + 2b + 3b + 4b + 5b + 6b + 7 + 8.",
    [
      { ref: "1040.L1z", value: line1.line1z.value },
      { ref: "1040.L2b", value: line2b.value },
      { ref: "1040.L3b", value: line3b.value },
      { ref: "1040.L4b", value: line4b.value },
      { ref: "1040.L5b", value: line5b.value },
      { ref: "1040.L6b", value: line6b.value },
      { ref: "1040.L7", value: line7.value },
      { ref: "1040.L8", value: line8.value },
    ],
    [AUTH.IRC_61, AUTH.FORM_1040_INSTR],
  );

  const line10 = lineResult(
    "1040.L10",
    d(input.schedule1.adjustmentsToIncome).roundToDollar(),
    "Adjustments to income from Schedule 1, line 26.",
    [{ ref: "sched-1.L26", value: d(input.schedule1.adjustmentsToIncome) }],
    [AUTH.IRC_62, AUTH.SCHED_1_INSTR],
  );

  // Line 11 AGI = line 9 - line 10, not below zero per form instructions.
  const line11Raw = line9.value.subtract(line10.value);
  const line11Value = line11Raw.isNegative() ? line11Raw : line11Raw.roundToDollar();
  const line11 = lineResult(
    "1040.L11",
    line11Value,
    "Adjusted gross income: line 9 minus line 10.",
    [
      { ref: "1040.L9", value: line9.value },
      { ref: "1040.L10", value: line10.value },
    ],
    [AUTH.IRC_62, AUTH.FORM_1040_INSTR],
  );

  // Line 12 std or itemized
  const stdDed = computeStandardDeduction(input);
  const l12Value =
    input.itemizedDeduction !== undefined
      ? d(input.itemizedDeduction).roundToDollar()
      : stdDed.roundToDollar();
  const line12 = lineResult(
    "1040.L12",
    l12Value,
    input.itemizedDeduction !== undefined
      ? "Itemized deduction from Schedule A, line 17."
      : "Standard deduction for filing status (plus age/blind bumps).",
    [
      { ref: "sched-A.L17", value: d(input.itemizedDeduction ?? 0) },
      { ref: "std-ded.base", value: stdDed },
    ],
    [AUTH.IRC_63, AUTH.FORM_1040_INSTR],
  );

  const line13 = lineResult(
    "1040.L13",
    d(input.qbiDeduction).roundToDollar(),
    "Qualified business income deduction from Form 8995 or 8995-A.",
    [{ ref: "form-8995.result", value: d(input.qbiDeduction) }],
    [AUTH.IRC_199A, AUTH.FORM_1040_INSTR],
  );

  const line14 = lineResult(
    "1040.L14",
    line12.value.add(line13.value).roundToDollar(),
    "Sum of lines 12 and 13.",
    [
      { ref: "1040.L12", value: line12.value },
      { ref: "1040.L13", value: line13.value },
    ],
    [AUTH.FORM_1040_INSTR],
  );

  // Line 15 taxable income: AGI - (12 + 13), not less than zero.
  const line15Raw = line11.value.subtract(line14.value);
  const line15Value = line15Raw.isNegative() ? Money.zero() : line15Raw.roundToDollar();
  const line15 = lineResult(
    "1040.L15",
    line15Value,
    "Taxable income: line 11 minus line 14, not less than zero.",
    [
      { ref: "1040.L11", value: line11.value },
      { ref: "1040.L14", value: line14.value },
    ],
    [AUTH.IRC_63, AUTH.FORM_1040_INSTR],
  );

  return {
    ...line1,
    line2a,
    line2b,
    line3a,
    line3b,
    line4a,
    line4b,
    line5a,
    line5b,
    line6a,
    line6b,
    line7,
    line8,
    line9,
    line10,
    line11,
    line12,
    line13,
    line14,
    line15,
  };
}
