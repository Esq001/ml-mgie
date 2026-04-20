# @taxportal/calc

Pure TypeScript Form 1040 calculation engine for tax year 2025.

## Public surface

- `Money` — decimal-backed money type with half-up and banker's rounding.
- `computeForm1040(inputs, extra)` — returns `Form1040Result` with all
  lines 1 through 38, each carrying a `Provenance` record.
- `taxFromBrackets(taxableIncome, filingStatus)` — applies the 2025
  ordinary-income schedule.
- `AUTH` — canonical authority citations (IRC, form instructions, Pubs).

## Determinism

The engine has no IO, no randomness, and no hidden state. The same
inputs produce the same outputs byte-for-byte, which is the contract
the downstream audit log and review module depend on.

## Tests

```bash
npm install
npx tsc -p tsconfig.json --noEmit
npx vitest run --coverage
```

34 passing unit + property-based tests. Coverage thresholds in
`vitest.config.ts` are lines 90%, functions 90%, branches 85%.
