import { describe, it, expect } from "vitest";
import fc from "fast-check";
import { Money } from "../src/money.js";

describe("Money", () => {
  it("adds, subtracts, multiplies, and rounds without float error", () => {
    const a = Money.fromDollars("0.10");
    const b = Money.fromDollars("0.20");
    expect(a.add(b).toString()).toBe("0.30");
  });

  it("rounds half up to whole dollars", () => {
    expect(Money.fromDollars("100.50").roundToDollar().toString()).toBe("101.00");
    expect(Money.fromDollars("100.49").roundToDollar().toString()).toBe("100.00");
  });

  it("rounds banker's to two places when requested", () => {
    expect(Money.fromDollars("2.125").roundBankers(2).toString()).toBe("2.12");
    expect(Money.fromDollars("2.135").roundBankers(2).toString()).toBe("2.14");
  });

  it("converts to cents as bigint without loss", () => {
    expect(Money.fromDollars("1234.56").toCents()).toBe(123456n);
  });

  it("sums a list", () => {
    const sum = Money.sum([
      Money.fromDollars("1.11"),
      Money.fromDollars("2.22"),
      Money.fromDollars("3.33"),
    ]);
    expect(sum.toString()).toBe("6.66");
  });

  it("supports subtract, divide, min, max, and comparisons", () => {
    const a = Money.fromDollars("10.00");
    const b = Money.fromDollars("3.00");
    expect(a.subtract(b).toString()).toBe("7.00");
    expect(a.divide(2).toString()).toBe("5.00");
    expect(a.min(b).toString()).toBe("3.00");
    expect(a.max(b).toString()).toBe("10.00");
    expect(a.greaterThan(b)).toBe(true);
    expect(b.lessThan(a)).toBe(true);
    expect(Money.zero().isZero()).toBe(true);
    expect(Money.fromDollars(-1).isNegative()).toBe(true);
  });

  it("is associative under addition (property)", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: -1_000_000, max: 1_000_000 }),
        fc.integer({ min: -1_000_000, max: 1_000_000 }),
        fc.integer({ min: -1_000_000, max: 1_000_000 }),
        (a, b, c) => {
          const lhs = Money.fromCents(a).add(Money.fromCents(b)).add(Money.fromCents(c));
          const rhs = Money.fromCents(a).add(Money.fromCents(b).add(Money.fromCents(c)));
          expect(lhs.toCents()).toBe(rhs.toCents());
        },
      ),
    );
  });
});
