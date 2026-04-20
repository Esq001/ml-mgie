import { Money } from "./money.js";

export interface AuthorityCitation {
  /** Human label, e.g. "IRC § 63(c)" */
  label: string;
  /** Canonical URL for deep link in UI. */
  url: string;
  /** Source type. */
  kind: "irc" | "treas-reg" | "form-instruction" | "pub" | "rev-rul" | "rev-proc" | "notice" | "case";
}

export interface ProvenanceInput {
  ref: string;
  value: Money | number | string | boolean;
}

export interface Provenance {
  /** Dotted line reference, e.g. "1040.L1a". */
  lineRef: string;
  /** Inputs that produced the value. */
  inputs: ProvenanceInput[];
  /** Plain English formula description. */
  formula: string;
  /** One or more authority citations. */
  authorities: AuthorityCitation[];
}

export interface LineResult {
  ref: string;
  value: Money;
  provenance: Provenance;
}

export function lineResult(
  ref: string,
  value: Money,
  formula: string,
  inputs: ProvenanceInput[],
  authorities: AuthorityCitation[],
): LineResult {
  return {
    ref,
    value,
    provenance: { lineRef: ref, inputs, formula, authorities },
  };
}
