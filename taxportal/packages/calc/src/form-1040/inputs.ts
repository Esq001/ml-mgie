import type { FilingStatus } from "../filing-status.js";

/**
 * Minimal taxpayer input surface required to compute Form 1040 lines 1–38
 * for tax year 2025. This is intentionally flat; downstream packages will
 * derive it from the Prisma data model.
 */
export interface Form1040Inputs {
  taxYear: 2025;
  filingStatus: FilingStatus;

  // Age and vision flags used for the additional standard deduction.
  taxpayerAge65OrOlder: boolean;
  taxpayerBlind: boolean;
  spouseAge65OrOlder: boolean;
  spouseBlind: boolean;

  // Dependents for CTC / ODC purposes; only counts used at this phase.
  qualifyingChildrenUnder17: number;
  otherDependents: number;

  // Line 1: wages + compensation components.
  line1: {
    w2Box1Wages: number; // 1a
    householdEmployeeWages: number; // 1b
    tipIncomeNotReported: number; // 1c
    medicaidWaiverPayments: number; // 1d
    dependentCareBenefits: number; // 1e
    employerAdoptionBenefits: number; // 1f
    wagesFromForm8919: number; // 1g
    otherEarnedIncome: number; // 1h
    nontaxableCombatPayElection: number; // 1i (reduces 1z; election)
  };

  // Line 2: interest.
  line2: {
    taxExemptInterest: number; // 2a
    taxableInterest: number; // 2b
  };

  // Line 3: dividends.
  line3: {
    qualifiedDividends: number; // 3a
    ordinaryDividends: number; // 3b
  };

  // Line 4: IRA distributions.
  line4: {
    grossIraDistributions: number; // 4a
    taxableIraDistributions: number; // 4b
  };

  // Line 5: pensions and annuities.
  line5: {
    grossPensions: number; // 5a
    taxablePensions: number; // 5b
  };

  // Line 6: social security.
  line6: {
    grossSocialSecurity: number; // 6a
    taxableSocialSecurity: number; // 6b
    /** Election under IRC § 86(e): lump-sum method. */
    lumpSumElection: boolean; // 6c
  };

  // Line 7: capital gain or loss.
  line7: {
    capitalGainOrLoss: number;
    /** If true, Schedule D is not required. */
    scheduleDNotRequired: boolean;
  };

  // Line 8: additional income from Schedule 1, line 10.
  schedule1: {
    /** Line 10 — total additional income. */
    additionalIncome: number;
    /** Line 26 — total adjustments to income. */
    adjustmentsToIncome: number;
  };

  // Line 12: standard or itemized deduction.
  itemizedDeduction?: number;

  // Line 13: QBI deduction from Form 8995 / 8995-A.
  qbiDeduction: number;
}
