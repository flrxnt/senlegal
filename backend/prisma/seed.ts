import 'dotenv/config';
import { PrismaClient, UserRole, Plan } from '@prisma/client';
import { PrismaPg } from '@prisma/adapter-pg';
import bcrypt from 'bcrypt';

async function main() {
  const url = process.env.DATABASE_URL;
  if (!url) throw new Error('DATABASE_URL is required to seed.');

  const adapter = new PrismaPg({ connectionString: url });
  const prisma = new PrismaClient({ adapter });

  const email = process.env.ADMIN_EMAIL ?? 'admin@senlegal.sn';
  const password = process.env.ADMIN_PASSWORD ?? 'ChangeMeNow!2026';
  const name = process.env.ADMIN_NAME ?? 'Administrateur SenLégal';
  const rounds = Number(process.env.BCRYPT_ROUNDS ?? 12);
  const passwordHash = await bcrypt.hash(password, rounds);

  const admin = await prisma.user.upsert({
    where: { email },
    update: { role: UserRole.ADMIN, plan: Plan.PRO, isActive: true, name },
    create: {
      email,
      name,
      passwordHash,
      role: UserRole.ADMIN,
      plan: Plan.PRO,
      isActive: true,
    },
  });

  console.log(`[seed] admin ready -> ${admin.email}`);
  await prisma.$disconnect();
}

main().catch((err) => {
  console.error('[seed] failed', err);
  process.exit(1);
});
