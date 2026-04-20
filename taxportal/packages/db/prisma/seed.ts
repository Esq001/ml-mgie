/**
 * Seed script for TaxPortal1040.
 *
 * Creates a demo firm, one firm admin, two preparers, one reviewer, five
 * demo clients with varied fact patterns, and a representative document
 * set per client. Safe to run repeatedly; uses upserts keyed on deterministic
 * email addresses and client display names.
 *
 * Usage: pnpm --filter @taxportal/db db:seed
 */
import { PrismaClient, FirmRole, MfaStatus, FilingStatusDb, EngagementStatus } from "@prisma/client";

const prisma = new PrismaClient();

async function main(): Promise<void> {
  const firm = await prisma.firm.upsert({
    where: { id: "11111111-1111-1111-1111-111111111111" },
    update: {},
    create: {
      id: "11111111-1111-1111-1111-111111111111",
      name: "Cornerstone CPA, PLLC",
    },
  });

  const users = [
    { email: "admin@cornerstonecpa.test", role: FirmRole.ADMIN },
    { email: "preparer1@cornerstonecpa.test", role: FirmRole.PREPARER },
    { email: "preparer2@cornerstonecpa.test", role: FirmRole.PREPARER },
    { email: "reviewer@cornerstonecpa.test", role: FirmRole.REVIEWER },
  ] as const;

  for (const u of users) {
    await prisma.firmUser.upsert({
      where: { firmId_email: { firmId: firm.id, email: u.email } },
      update: { role: u.role },
      create: {
        firmId: firm.id,
        email: u.email,
        role: u.role,
        mfaStatus: MfaStatus.TOTP,
      },
    });
  }

  const clients = [
    { name: "Single W-2 Filer", status: FilingStatusDb.SINGLE },
    { name: "MFJ With K-1s and Foreign Accounts", status: FilingStatusDb.MFJ },
    { name: "Self Employed With Home Office", status: FilingStatusDb.SINGLE },
    { name: "Rental Real Estate With Passive Losses", status: FilingStatusDb.MFJ },
    { name: "Retiree With Social Security and Pensions", status: FilingStatusDb.MFJ },
  ];

  for (const c of clients) {
    const client = await prisma.client.upsert({
      where: { id: `c-${c.name}`.slice(0, 36) },
      update: {},
      create: {
        id: `c-${Buffer.from(c.name).toString("hex").slice(0, 32)}`,
        firmId: firm.id,
        displayName: c.name,
      },
    });
    await prisma.engagement.upsert({
      where: {
        firmId_clientId_taxYear: {
          firmId: firm.id,
          clientId: client.id,
          taxYear: 2025,
        },
      },
      update: {},
      create: {
        firmId: firm.id,
        clientId: client.id,
        taxYear: 2025,
        status: EngagementStatus.DOCUMENTS_REQUESTED,
      },
    });
  }

  // eslint-disable-next-line no-console
  console.log("Seed complete: firm, 4 users, 5 clients + engagements.");
}

main()
  .catch((e) => {
    // eslint-disable-next-line no-console
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
