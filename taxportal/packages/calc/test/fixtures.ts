import type { Form1040Inputs } from "../src/form-1040/inputs.js";
import type { Form1040Lines16Through38Inputs } from "../src/form-1040/lines-16-38.js";

export function zeroInputs(
  overrides: Partial<Form1040Inputs> = {},
): Form1040Inputs {
  return {
    taxYear: 2025,
    filingStatus: "single",
    taxpayerAge65OrOlder: false,
    taxpayerBlind: false,
    spouseAge65OrOlder: false,
    spouseBlind: false,
    qualifyingChildrenUnder17: 0,
    otherDependents: 0,
    line1: {
      w2Box1Wages: 0,
      householdEmployeeWages: 0,
      tipIncomeNotReported: 0,
      medicaidWaiverPayments: 0,
      dependentCareBenefits: 0,
      employerAdoptionBenefits: 0,
      wagesFromForm8919: 0,
      otherEarnedIncome: 0,
      nontaxableCombatPayElection: 0,
    },
    line2: { taxExemptInterest: 0, taxableInterest: 0 },
    line3: { qualifiedDividends: 0, ordinaryDividends: 0 },
    line4: { grossIraDistributions: 0, taxableIraDistributions: 0 },
    line5: { grossPensions: 0, taxablePensions: 0 },
    line6: { grossSocialSecurity: 0, taxableSocialSecurity: 0, lumpSumElection: false },
    line7: { capitalGainOrLoss: 0, scheduleDNotRequired: true },
    schedule1: { additionalIncome: 0, adjustmentsToIncome: 0 },
    qbiDeduction: 0,
    ...overrides,
  };
}

export function zeroExtra(
  overrides: Partial<Form1040Lines16Through38Inputs> = {},
): Form1040Lines16Through38Inputs {
  return {
    schedule2Line3: 0,
    line19CtcOdc: 0,
    schedule3Line8: 0,
    schedule2Line21: 0,
    withholding: { fromW2Box2: 0, from1099: 0, fromOther: 0 },
    estimatedPayments: 0,
    earnedIncomeCredit: 0,
    additionalCtc: 0,
    americanOpportunityCredit: 0,
    schedule3Line15: 0,
    appliedToNextYearEstimated: 0,
    estimatedTaxPenalty: 0,
    ...overrides,
  };
}
