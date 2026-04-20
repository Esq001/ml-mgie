import { Money } from "./money.js";
import type { FilingStatus } from "./filing-status.js";

export interface Bracket {
  /** Lower bound of this bracket (inclusive). */
  over: number;
  /** Upper bound (exclusive). Infinity means open-ended top bracket. */
  notOver: number;
  /** Marginal rate, e.g. 0.22. */
  rate: number;
}

/**
 * Tax year 2025 ordinary income brackets per Rev. Proc. 2024-40.
 */
export const BRACKETS_2025: Record<FilingStatus, Bracket[]> = {
  single: [
    { over: 0, notOver: 11925, rate: 0.1 },
    { over: 11925, notOver: 48475, rate: 0.12 },
    { over: 48475, notOver: 103350, rate: 0.22 },
    { over: 103350, notOver: 197300, rate: 0.24 },
    { over: 197300, notOver: 250525, rate: 0.32 },
    { over: 250525, notOver: 626350, rate: 0.35 },
    { over: 626350, notOver: Infinity, rate: 0.37 },
  ],
  mfj: [
    { over: 0, notOver: 23850, rate: 0.1 },
    { over: 23850, notOver: 96950, rate: 0.12 },
    { over: 96950, notOver: 206700, rate: 0.22 },
    { over: 206700, notOver: 394600, rate: 0.24 },
    { over: 394600, notOver: 501050, rate: 0.32 },
    { over: 501050, notOver: 751600, rate: 0.35 },
    { over: 751600, notOver: Infinity, rate: 0.37 },
  ],
  mfs: [
    { over: 0, notOver: 11925, rate: 0.1 },
    { over: 11925, notOver: 48475, rate: 0.12 },
    { over: 48475, notOver: 103350, rate: 0.22 },
    { over: 103350, notOver: 197300, rate: 0.24 },
    { over: 197300, notOver: 250525, rate: 0.32 },
    { over: 250525, notOver: 375800, rate: 0.35 },
    { over: 375800, notOver: Infinity, rate: 0.37 },
  ],
  hoh: [
    { over: 0, notOver: 17000, rate: 0.1 },
    { over: 17000, notOver: 64850, rate: 0.12 },
    { over: 64850, notOver: 103350, rate: 0.22 },
    { over: 103350, notOver: 197300, rate: 0.24 },
    { over: 197300, notOver: 250500, rate: 0.32 },
    { over: 250500, notOver: 626350, rate: 0.35 },
    { over: 626350, notOver: Infinity, rate: 0.37 },
  ],
  qss: [
    { over: 0, notOver: 23850, rate: 0.1 },
    { over: 23850, notOver: 96950, rate: 0.12 },
    { over: 96950, notOver: 206700, rate: 0.22 },
    { over: 206700, notOver: 394600, rate: 0.24 },
    { over: 394600, notOver: 501050, rate: 0.32 },
    { over: 501050, notOver: 751600, rate: 0.35 },
    { over: 751600, notOver: Infinity, rate: 0.37 },
  ],
};

/**
 * Apply the progressive bracket schedule to a taxable income amount.
 * Pure and deterministic.
 */
export function taxFromBrackets(
  taxableIncome: Money,
  filingStatus: FilingStatus,
): Money {
  if (taxableIncome.isNegative() || taxableIncome.isZero()) return Money.zero();
  const income = taxableIncome.toDollars();
  const brackets = BRACKETS_2025[filingStatus];
  let tax = Money.zero();
  for (const b of brackets) {
    if (income <= b.over) break;
    const upper = Math.min(income, b.notOver);
    const slice = upper - b.over;
    if (slice > 0) {
      tax = tax.add(Money.fromDollars(slice).multiply(b.rate));
    }
    if (income <= b.notOver) break;
  }
  return tax.roundToDollar();
}
