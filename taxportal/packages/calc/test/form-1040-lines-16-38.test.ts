import { describe, it, expect } from "vitest";
import { computeForm1040 } from "../src/form-1040/index.js";
import { zeroExtra, zeroInputs } from "./fixtures.js";

describe("Form 1040 lines 16 through 38 (tax year 2025)", () => {
  it("computes tax on line 16 from taxable income", () => {
    const r = computeForm1040(
      zeroInputs({
        line1: { ...zeroInputs().line1, w2Box1Wages: 65_000 },
      }),
      zeroExtra(),
    );
    // Taxable income = 65,000 - 15,000 = 50,000.
    // Single tax: 1,192.50 + 4,386.00 + 22% * (50,000 - 48,475) = 5,914.00.
    // Rounded: 5,914.
    expect(Math.abs(r.line16.value.toDollars() - 5_914)).toBeLessThanOrEqual(1);
  });

  it("honors line 16 override when supplied (e.g., QDCGW)", () => {
    const r = computeForm1040(
      zeroInputs({
        line1: { ...zeroInputs().line1, w2Box1Wages: 65_000 },
      }),
      zeroExtra({ line16Override: 4_000 }),
    );
    expect(r.line16.value.toDollars()).toBe(4_000);
  });

  it("adds Schedule 2 line 3 onto line 18", () => {
    const r = computeForm1040(
      zeroInputs({ line1: { ...zeroInputs().line1, w2Box1Wages: 100_000 } }),
      zeroExtra({ schedule2Line3: 2_500 }),
    );
    expect(r.line18.value.toDollars()).toBe(r.line16.value.toDollars() + 2_500);
  });

  it("clamps line 22 at zero when credits exceed tax", () => {
    const r = computeForm1040(
      zeroInputs(),
      zeroExtra({ line19CtcOdc: 10_000 }),
    );
    expect(r.line22.value.toDollars()).toBe(0);
  });

  it("sums withholding into line 25d", () => {
    const r = computeForm1040(
      zeroInputs(),
      zeroExtra({
        withholding: { fromW2Box2: 8_000, from1099: 1_500, fromOther: 500 },
      }),
    );
    expect(r.line25d.value.toDollars()).toBe(10_000);
  });

  it("computes overpayment and refund on lines 34 and 35a", () => {
    const r = computeForm1040(
      zeroInputs({ line1: { ...zeroInputs().line1, w2Box1Wages: 40_000 } }),
      zeroExtra({
        withholding: { fromW2Box2: 5_000, from1099: 0, fromOther: 0 },
      }),
    );
    // Taxable income = 25,000. Tax = 10% * 11,925 + 12% * (25,000 - 11,925)
    //   = 1,192.50 + 1,569.00 = 2,761.50 -> rounds to 2,762.
    // Payments = 5,000. Overpayment = 2,238 or 2,239 depending on rounding.
    expect(r.line24.value.toDollars()).toBeLessThan(3_000);
    expect(r.line33.value.toDollars()).toBe(5_000);
    expect(r.line34.value.toDollars()).toBeGreaterThan(2_000);
    expect(r.line37.value.toDollars()).toBe(0);
  });

  it("computes amount owed on line 37 when tax exceeds payments", () => {
    const r = computeForm1040(
      zeroInputs({ line1: { ...zeroInputs().line1, w2Box1Wages: 200_000 } }),
      zeroExtra({
        withholding: { fromW2Box2: 10_000, from1099: 0, fromOther: 0 },
      }),
    );
    expect(r.line34.value.toDollars()).toBe(0);
    expect(r.line37.value.toDollars()).toBeGreaterThan(0);
  });

  it("caps line 36 (applied to next year) at the overpayment amount", () => {
    const r = computeForm1040(
      zeroInputs({ line1: { ...zeroInputs().line1, w2Box1Wages: 30_000 } }),
      zeroExtra({
        withholding: { fromW2Box2: 5_000, from1099: 0, fromOther: 0 },
        appliedToNextYearEstimated: 99_999,
      }),
    );
    expect(r.line36.value.toDollars()).toBe(r.line34.value.toDollars());
    expect(r.line35a.value.toDollars()).toBe(0);
  });

  it("records estimated tax penalty on line 38", () => {
    const r = computeForm1040(
      zeroInputs(),
      zeroExtra({ estimatedTaxPenalty: 125 }),
    );
    expect(r.line38.value.toDollars()).toBe(125);
  });

  it("produces a provenance record on every line 16-38 output", () => {
    const r = computeForm1040(
      zeroInputs({ line1: { ...zeroInputs().line1, w2Box1Wages: 75_000 } }),
      zeroExtra(),
    );
    const lines = [
      r.line16, r.line17, r.line18, r.line19, r.line20, r.line21,
      r.line22, r.line23, r.line24, r.line25a, r.line25b, r.line25c,
      r.line25d, r.line26, r.line27, r.line28, r.line29, r.line31,
      r.line32, r.line33, r.line34, r.line35a, r.line36, r.line37, r.line38,
    ];
    for (const l of lines) {
      expect(l.provenance.formula.length).toBeGreaterThan(10);
      expect(l.provenance.lineRef).toMatch(/^1040\.L/);
    }
  });
});
