import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient({
    datasourceUrl: "postgresql://postgres.ojrhotaxanegfonsqieu:GuGJqlhNZGXpWH9Y@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true"
});
async function main() {
  try {
    const user = await prisma.user.findFirst();
    console.log("Found user:", user?.id);
    
    if (user) {
      console.log("Fetching transactions...");
      const txs = await prisma.transaction.findMany({
          where: { userId: user.id }
      });
      console.log("Transactions:", txs.length);
    }
    
  } catch (e) {
    console.error("DB Error:", e);
  } finally {
    await prisma.$disconnect();
  }
}
main();
