/**
 * TaxPortal1040 API entrypoint.
 *
 * This is a placeholder for the NestJS bootstrap. The calc package is
 * already shippable; controller, auth, Prisma wiring, and OpenAPI
 * generation land in follow-up phases (see docs/roadmap.md).
 */
import { computeForm1040 } from "@taxportal/calc";

export function demoCompute(): number {
  const r = computeForm1040(
    {
      taxYear: 2025,
      filingStatus: "single",
      taxpayerAge65OrOlder: false,
      taxpayerBlind: false,
      spouseAge65OrOlder: false,
      spouseBlind: false,
      qualifyingChildrenUnder17: 0,
      otherDependents: 0,
      line1: {
        w2Box1Wages: 75000,
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
    },
    {
      schedule2Line3: 0,
      line19CtcOdc: 0,
      schedule3Line8: 0,
      schedule2Line21: 0,
      withholding: { fromW2Box2: 8000, from1099: 0, fromOther: 0 },
      estimatedPayments: 0,
      earnedIncomeCredit: 0,
      additionalCtc: 0,
      americanOpportunityCredit: 0,
      schedule3Line15: 0,
      appliedToNextYearEstimated: 0,
      estimatedTaxPenalty: 0,
    },
  );
  return r.line24.value.toDollars();
}

if (import.meta.url === `file://${process.argv[1]}`) {
  // eslint-disable-next-line no-console
  console.log(`Demo line 24 (total tax) = ${demoCompute()}`);
}
