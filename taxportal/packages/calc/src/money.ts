import Decimal from "decimal.js";

Decimal.set({ precision: 28, rounding: Decimal.ROUND_HALF_UP });

export type Cents = bigint;

export class Money {
  private readonly value: Decimal;

  private constructor(value: Decimal) {
    this.value = value;
  }

  static fromDollars(dollars: number | string): Money {
    return new Money(new Decimal(dollars));
  }

  static fromCents(cents: Cents | number): Money {
    const c = typeof cents === "bigint" ? cents.toString() : String(cents);
    return new Money(new Decimal(c).dividedBy(100));
  }

  static zero(): Money {
    return new Money(new Decimal(0));
  }

  add(other: Money): Money {
    return new Money(this.value.plus(other.value));
  }

  subtract(other: Money): Money {
    return new Money(this.value.minus(other.value));
  }

  multiply(factor: number | string | Decimal): Money {
    return new Money(this.value.times(factor));
  }

  divide(divisor: number | string | Decimal): Money {
    return new Money(this.value.dividedBy(divisor));
  }

  min(other: Money): Money {
    return this.value.lessThan(other.value) ? this : other;
  }

  max(other: Money): Money {
    return this.value.greaterThan(other.value) ? this : other;
  }

  isZero(): boolean {
    return this.value.isZero();
  }

  isNegative(): boolean {
    return this.value.isNegative();
  }

  lessThan(other: Money): boolean {
    return this.value.lessThan(other.value);
  }

  greaterThan(other: Money): boolean {
    return this.value.greaterThan(other.value);
  }

  /**
   * IRS line items are reported as whole dollars. Standard half-up rounding.
   */
  roundToDollar(): Money {
    return new Money(this.value.toDecimalPlaces(0, Decimal.ROUND_HALF_UP));
  }

  /**
   * Banker's rounding for statutory percentages that explicitly require it.
   */
  roundBankers(places = 2): Money {
    return new Money(this.value.toDecimalPlaces(places, Decimal.ROUND_HALF_EVEN));
  }

  toCents(): Cents {
    return BigInt(
      this.value.times(100).toDecimalPlaces(0, Decimal.ROUND_HALF_UP).toFixed(0),
    );
  }

  toDollars(): number {
    return this.value.toNumber();
  }

  toString(): string {
    return this.value.toFixed(2);
  }

  static sum(values: Money[]): Money {
    return values.reduce((acc, v) => acc.add(v), Money.zero());
  }
}
