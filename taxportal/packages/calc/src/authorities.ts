import type { AuthorityCitation } from "./provenance.js";

export const AUTH = {
  IRC_61: {
    label: "IRC § 61",
    url: "https://www.law.cornell.edu/uscode/text/26/61",
    kind: "irc",
  },
  IRC_62: {
    label: "IRC § 62",
    url: "https://www.law.cornell.edu/uscode/text/26/62",
    kind: "irc",
  },
  IRC_63: {
    label: "IRC § 63",
    url: "https://www.law.cornell.edu/uscode/text/26/63",
    kind: "irc",
  },
  IRC_86: {
    label: "IRC § 86",
    url: "https://www.law.cornell.edu/uscode/text/26/86",
    kind: "irc",
  },
  IRC_151: {
    label: "IRC § 151",
    url: "https://www.law.cornell.edu/uscode/text/26/151",
    kind: "irc",
  },
  IRC_199A: {
    label: "IRC § 199A",
    url: "https://www.law.cornell.edu/uscode/text/26/199A",
    kind: "irc",
  },
  IRC_1: {
    label: "IRC § 1",
    url: "https://www.law.cornell.edu/uscode/text/26/1",
    kind: "irc",
  },
  FORM_1040_INSTR: {
    label: "2025 Form 1040 Instructions",
    url: "https://www.irs.gov/forms-pubs/about-form-1040",
    kind: "form-instruction",
  },
  SCHED_1_INSTR: {
    label: "2025 Schedule 1 (Form 1040) Instructions",
    url: "https://www.irs.gov/forms-pubs/about-schedule-1-form-1040",
    kind: "form-instruction",
  },
  PUB_17: {
    label: "IRS Publication 17",
    url: "https://www.irs.gov/publications/p17",
    kind: "pub",
  },
} as const satisfies Record<string, AuthorityCitation>;
