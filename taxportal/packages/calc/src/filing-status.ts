export type FilingStatus =
  | "single"
  | "mfj"
  | "mfs"
  | "hoh"
  | "qss";

export const STANDARD_DEDUCTION_2025: Record<FilingStatus, number> = {
  // Tax year 2025 figures per Rev. Proc. 2024-40.
  single: 15000,
  mfj: 30000,
  mfs: 15000,
  hoh: 22500,
  qss: 30000,
};

export const ADDITIONAL_STD_DED_2025 = {
  /** Age 65+ or blind, MFJ/QSS/MFS. */
  married: 1600,
  /** Age 65+ or blind, Single/HOH. */
  unmarried: 2000,
};
