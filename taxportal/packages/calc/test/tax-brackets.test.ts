import { describe, it, expect } from "vitest";
import fc from "fast-check";
import { Money } from "../src/money.js";
import { BRACKETS_2025, taxFromBrackets } from "../src/tax-brackets-2025.js";
import type { FilingStatus } from "../src/filing-status.js";

const closeEnough = (a: number, b: number, tol = 1) => Math.abs(a - b) <= tol;

describe("taxFromBrackets 2025", () => {
  it("returns zero for zero or negative income", () => {
    expect(taxFromBrackets(Money.zero(), "single").toDollars()).toBe(0);
    expect(taxFromBrackets(Money.fromDollars(-500), "mfj").toDollars()).toBe(0);
  });

  it("computes single $50,000 correctly", () => {
    // 10% * 11,925 = 1,192.50
    // 12% * (48,475 - 11,925) = 12% * 36,550 = 4,386.00
    // 22% * (50,000 - 48,475) = 22% * 1,525 = 335.50
    // Total = 5,914.00
    const tax = taxFromBrackets(Money.fromDollars(50_000), "single").toDollars();
    expect(closeEnough(tax, 5914)).toBe(true);
  });

  it("computes MFJ $200,000 correctly", () => {
    // 10% * 23,850 = 2,385
    // 12% * (96,950 - 23,850) = 12% * 73,100 = 8,772
    // 22% * (200,000 - 96,950) = 22% * 103,050 = 22,671
    // Total = 33,828
    const tax = taxFromBrackets(Money.fromDollars(200_000), "mfj").toDollars();
    expect(closeEnough(tax, 33_828)).toBe(true);
  });

  it("produces monotonically non-decreasing tax as income rises (property)", () => {
    const statuses: FilingStatus[] = ["single", "mfj", "mfs", "hoh", "qss"];
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 2_000_000 }),
        fc.integer({ min: 0, max: 200_000 }),
        fc.constantFrom(...statuses),
        (base, delta, status) => {
          const low = taxFromBrackets(Money.fromDollars(base), status).toDollars();
          const high = taxFromBrackets(
            Money.fromDollars(base + delta),
            status,
          ).toDollars();
          expect(high).toBeGreaterThanOrEqual(low - 1); // tolerance for rounding
        },
      ),
    );
  });

  it("marginal rate never exceeds 37% over a $10,000 window (property)", () => {
    // Use a large-enough bump that whole-dollar rounding is negligible.
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 5_000_000 }),
        (base) => {
          const bump = 10_000;
          const a = taxFromBrackets(Money.fromDollars(base), "single").toDollars();
          const b = taxFromBrackets(
            Money.fromDollars(base + bump),
            "single",
          ).toDollars();
          const marginal = (b - a) / bump;
          expect(marginal).toBeLessThanOrEqual(0.371);
          expect(marginal).toBeGreaterThanOrEqual(0);
        },
      ),
    );
  });

  it("exposes 7 brackets per filing status", () => {
    for (const status of Object.keys(BRACKETS_2025) as FilingStatus[]) {
      expect(BRACKETS_2025[status]).toHaveLength(7);
    }
  });
});
