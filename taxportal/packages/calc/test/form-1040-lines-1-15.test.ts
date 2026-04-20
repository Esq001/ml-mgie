import { describe, it, expect } from "vitest";
import { computeForm1040Lines1Through38 } from "../src/form-1040/lines-1-38.js";
import { zeroInputs } from "./fixtures.js";

describe("Form 1040 lines 1 through 15 (tax year 2025)", () => {
  it("sums W-2 wages into line 1a and flows to 1z", () => {
    const result = computeForm1040Lines1Through38(
      zeroInputs({ line1: { ...zeroInputs().line1, w2Box1Wages: 85_000 } }),
    );
    expect(result.line1a.value.toDollars()).toBe(85_000);
    expect(result.line1z.value.toDollars()).toBe(85_000);
  });

  it("subtracts nontaxable combat pay election on 1i from 1z", () => {
    const r = computeForm1040Lines1Through38(
      zeroInputs({
        line1: {
          ...zeroInputs().line1,
          w2Box1Wages: 50_000,
          nontaxableCombatPayElection: 5_000,
        },
      }),
    );
    expect(r.line1z.value.toDollars()).toBe(45_000);
  });

  it("computes line 9 total income for a simple single filer", () => {
    const r = computeForm1040Lines1Through38(
      zeroInputs({
        line1: { ...zeroInputs().line1, w2Box1Wages: 100_000 },
        line2: { taxExemptInterest: 0, taxableInterest: 500 },
        line3: { qualifiedDividends: 800, ordinaryDividends: 800 },
      }),
    );
    // 100000 + 500 + 800 = 101,300 (qualified dividends don't stack with ordinary)
    expect(r.line9.value.toDollars()).toBe(101_300);
  });

  it("computes AGI = line 9 - line 10 adjustments", () => {
    const r = computeForm1040Lines1Through38(
      zeroInputs({
        line1: { ...zeroInputs().line1, w2Box1Wages: 120_000 },
        schedule1: { additionalIncome: 0, adjustmentsToIncome: 7_000 },
      }),
    );
    expect(r.line11.value.toDollars()).toBe(113_000);
  });

  it("applies the 2025 single standard deduction of $15,000 on line 12", () => {
    const r = computeForm1040Lines1Through38(
      zeroInputs({ line1: { ...zeroInputs().line1, w2Box1Wages: 80_000 } }),
    );
    expect(r.line12.value.toDollars()).toBe(15_000);
  });

  it("applies the 2025 MFJ standard deduction of $30,000 on line 12", () => {
    const r = computeForm1040Lines1Through38(
      zeroInputs({
        filingStatus: "mfj",
        line1: { ...zeroInputs().line1, w2Box1Wages: 150_000 },
      }),
    );
    expect(r.line12.value.toDollars()).toBe(30_000);
  });

  it("adds age-65 and blind bumps to the standard deduction", () => {
    // Single, 65+ and blind -> 15,000 + 2,000 + 2,000 = 19,000
    const r = computeForm1040Lines1Through38(
      zeroInputs({
        filingStatus: "single",
        taxpayerAge65OrOlder: true,
        taxpayerBlind: true,
      }),
    );
    expect(r.line12.value.toDollars()).toBe(19_000);
  });

  it("adds age-65 and blind bumps for MFJ at $1,600 per bump", () => {
    // MFJ, both spouses 65+ -> 30,000 + 1,600 + 1,600 = 33,200
    const r = computeForm1040Lines1Through38(
      zeroInputs({
        filingStatus: "mfj",
        taxpayerAge65OrOlder: true,
        spouseAge65OrOlder: true,
      }),
    );
    expect(r.line12.value.toDollars()).toBe(33_200);
  });

  it("uses itemized deduction when supplied", () => {
    const r = computeForm1040Lines1Through38(
      zeroInputs({ itemizedDeduction: 42_500 }),
    );
    expect(r.line12.value.toDollars()).toBe(42_500);
  });

  it("sums QBI onto line 14 and computes taxable income line 15", () => {
    const r = computeForm1040Lines1Through38(
      zeroInputs({
        line1: { ...zeroInputs().line1, w2Box1Wages: 200_000 },
        qbiDeduction: 5_000,
      }),
    );
    // AGI 200,000 - (std ded 15,000 + QBI 5,000) = 180,000
    expect(r.line14.value.toDollars()).toBe(20_000);
    expect(r.line15.value.toDollars()).toBe(180_000);
  });

  it("clamps line 15 taxable income at zero", () => {
    const r = computeForm1040Lines1Through38(
      zeroInputs({
        line1: { ...zeroInputs().line1, w2Box1Wages: 5_000 },
      }),
    );
    expect(r.line15.value.toDollars()).toBe(0);
  });

  it("attaches authority citations to every computed line", () => {
    const r = computeForm1040Lines1Through38(zeroInputs());
    const lines = [
      r.line1z,
      r.line2b,
      r.line3b,
      r.line6b,
      r.line9,
      r.line11,
      r.line12,
      r.line15,
    ];
    for (const line of lines) {
      expect(line.provenance.authorities.length).toBeGreaterThanOrEqual(1);
      for (const a of line.provenance.authorities) {
        expect(a.url).toMatch(/^https?:\/\//);
      }
    }
  });
});
