export * from "./inputs.js";
export * from "./lines-1-38.js";
export * from "./lines-16-38.js";

import type { Form1040Inputs } from "./inputs.js";
import {
  computeForm1040Lines1Through38,
  type Form1040Lines1Through38,
} from "./lines-1-38.js";
import {
  computeForm1040Lines16Through38,
  type Form1040Lines16Through38,
  type Form1040Lines16Through38Inputs,
} from "./lines-16-38.js";

export interface Form1040Result
  extends Form1040Lines1Through38,
    Form1040Lines16Through38 {}

/**
 * Compute the full set of Form 1040 lines 1 through 38.
 */
export function computeForm1040(
  inputs: Form1040Inputs,
  extra: Form1040Lines16Through38Inputs,
): Form1040Result {
  const upstream = computeForm1040Lines1Through38(inputs);
  const downstream = computeForm1040Lines16Through38(inputs, upstream, extra);
  return { ...upstream, ...downstream };
}
