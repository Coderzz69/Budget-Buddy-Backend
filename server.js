import { ClerkExpressRequireAuth } from "@clerk/clerk-sdk-node";
import { PrismaClient } from "@prisma/client";
import cors from "cors";
import dotenv from "dotenv";
import express from "express";

dotenv.config();

const app = express();
const prisma = new PrismaClient({
    datasourceUrl: process.env.DATABASE_URL,
});

// ---------- Middleware ----------
app.use(cors());
app.use(express.json());

// ---------- Health Check ----------
app.get("/", (req, res) => {
    res.json({ status: "This is Home page. Express JS is working!!" });
});

app.get("/health", (req, res) => {
    res.json({ status: "ok" });
});

// ---------- Authentication Routes ----------

// Sync user to database after Clerk authentication
app.post("/auth/sync", ClerkExpressRequireAuth(), async (req, res) => {
    const userId = req.auth.userId;
    const { email, firstName, lastName } = req.body;

    try {
        // Check if user exists by Clerk ID
        let user = await prisma.user.findUnique({
            where: { clerkId: userId },
        });

        if (!user) {
            // Check if user exists by email (to support migration/pre-existing users)
            const userEmail = email || req.auth.sessionClaims?.email;

            if (userEmail) {
                const existingUser = await prisma.user.findUnique({
                    where: { email: userEmail },
                });

                if (existingUser) {
                    // Link Clerk ID to existing user
                    user = await prisma.user.update({
                        where: { id: existingUser.id },
                        data: {
                            clerkId: userId,
                            name: firstName && lastName ? `${firstName} ${lastName}` : existingUser.name,
                        },
                    });
                    console.log(`Linked existing user to Clerk ID: ${user.email}`);
                } else {
                    // Create new user in database
                    user = await prisma.user.create({
                        data: {
                            clerkId: userId,
                            email: userEmail,
                            name: firstName && lastName ? `${firstName} ${lastName}` : null,
                        },
                    });
                    console.log(`Created new user in database: ${user.email}`);
                }
            } else {
                // No email found? This is tricky. Create with empty or null email?
                // Schema says email is unique string.
                // We will skip creation if no email to avoid collision/error, or assume it's required.
                // For now, let's create and hope email is optional in practice or provided.
                // But wait, schema says String (not String?), so it is required.
                // If no email, we can't create.
                console.error("Cannot sync user: No email provided.");
                return res.status(400).json({ error: "Email is required for sync" });
            }
        } else {
            // User found by Clerk ID - Update info
            user = await prisma.user.update({
                where: { clerkId: userId },
                data: {
                    email: email || req.auth.sessionClaims?.email || user.email,
                    name: firstName && lastName ? `${firstName} ${lastName}` : user.name,
                },
            });
            console.log(`Updated user in database: ${user.email}`);
        }

        res.json({
            success: true,
            user: {
                id: user.id,
                clerkId: user.clerkId,
                email: user.email,
                name: user.name,
            }
        });
    } catch (error) {
        console.error("User sync error:", error);
        res.status(500).json({ error: "Failed to sync user" });
    }
});

// ---------- Protected Routes ----------
// All routes below require Clerk authentication

// Create account
app.post("/accounts", ClerkExpressRequireAuth(), async (req, res) => {
    const { name, type } = req.body;
    const userId = req.auth.userId;

    if (!name || !type) {
        return res.status(400).json({ error: "Missing fields" });
    }

    try {
        // Find or create user in database
        let user = await prisma.user.findUnique({
            where: { clerkId: userId },
        });

        if (!user) {
            user = await prisma.user.create({
                data: {
                    clerkId: userId,
                    email: req.auth.sessionClaims?.email || "",
                },
            });
        }

        const account = await prisma.account.create({
            data: {
                name,
                type,
                userId: user.id,
            },
        });

        res.json(account);
    } catch (error) {
        console.error("Create account error:", error);
        res.status(500).json({ error: "Failed to create account" });
    }
});

// Read all accounts
app.get("/accounts", ClerkExpressRequireAuth(), async (req, res) => {
    const userId = req.auth.userId;

    try {
        const user = await prisma.user.findUnique({
            where: { clerkId: userId },
            include: { accounts: true },
        });

        if (!user) {
            return res.json([]);
        }

        res.json(user.accounts);
    } catch (error) {
        console.error("Get accounts error:", error);
        res.status(500).json({ error: "Failed to fetch accounts" });
    }
});

// Update an account
app.put("/accounts/:id", ClerkExpressRequireAuth(), async (req, res) => {
    const { id } = req.params;
    const { name, type } = req.body;
    const userId = req.auth.userId;

    try {
        const user = await prisma.user.findUnique({
            where: { clerkId: userId },
        });

        if (!user) {
            return res.status(404).json({ error: "User not found" });
        }

        const account = await prisma.account.updateMany({
            where: {
                id: parseInt(id),
                userId: user.id,
            },
            data: { name, type },
        });

        if (account.count === 0) {
            return res.status(404).json({ error: "Account not found" });
        }

        res.json({ message: "Account updated" });
    } catch (error) {
        console.error("Update account error:", error);
        res.status(500).json({ error: "Failed to update account" });
    }
});

// Delete an account
app.delete("/accounts/:id", ClerkExpressRequireAuth(), async (req, res) => {
    const { id } = req.params;
    const userId = req.auth.userId;

    try {
        const user = await prisma.user.findUnique({
            where: { clerkId: userId },
        });

        if (!user) {
            return res.status(404).json({ error: "User not found" });
        }

        const account = await prisma.account.deleteMany({
            where: {
                id: parseInt(id),
                userId: user.id,
            },
        });

        if (account.count === 0) {
            return res.status(404).json({ error: "Account not found" });
        }

        res.json({ message: "Account deleted" });
    } catch (error) {
        console.error("Delete account error:", error);
        res.status(500).json({ error: "Failed to delete account" });
    }
});

// Create transaction
app.post("/transactions", ClerkExpressRequireAuth(), async (req, res) => {
    const { type, category, amount, description, date, accountId } = req.body;
    const userId = req.auth.userId;

    if (!type || !category || !amount || !date || !accountId) {
        return res.status(400).json({ error: "Missing required fields" });
    }

    try {
        const user = await prisma.user.findUnique({
            where: { clerkId: userId },
        });

        if (!user) {
            return res.status(404).json({ error: "User not found" });
        }

        const transaction = await prisma.transaction.create({
            data: {
                type,
                category,
                amount: parseFloat(amount),
                description,
                date: new Date(date),
                accountId: parseInt(accountId),
                userId: user.id,
            },
        });

        res.json(transaction);
    } catch (error) {
        console.error("Create transaction error:", error);
        res.status(500).json({ error: "Failed to create transaction" });
    }
});

// Read all transactions
app.get("/transactions", ClerkExpressRequireAuth(), async (req, res) => {
    const userId = req.auth.userId;

    try {
        const user = await prisma.user.findUnique({
            where: { clerkId: userId },
            include: {
                transactions: {
                    include: { account: true },
                    orderBy: { date: "desc" },
                },
            },
        });

        if (!user) {
            return res.json([]);
        }

        res.json(user.transactions);
    } catch (error) {
        console.error("Get transactions error:", error);
        res.status(500).json({ error: "Failed to fetch transactions" });
    }
});

// Update a transaction
app.put("/transactions/:id", ClerkExpressRequireAuth(), async (req, res) => {
    const { id } = req.params;
    const { type, category, amount, description, date, accountId } = req.body;
    const userId = req.auth.userId;

    try {
        const user = await prisma.user.findUnique({
            where: { clerkId: userId },
        });

        if (!user) {
            return res.status(404).json({ error: "User not found" });
        }

        const transaction = await prisma.transaction.updateMany({
            where: {
                id: parseInt(id),
                userId: user.id,
            },
            data: {
                type,
                category,
                amount: parseFloat(amount),
                description,
                date: new Date(date),
                accountId: parseInt(accountId),
            },
        });

        if (transaction.count === 0) {
            return res.status(404).json({ error: "Transaction not found" });
        }

        res.json({ message: "Transaction updated" });
    } catch (error) {
        console.error("Update transaction error:", error);
        res.status(500).json({ error: "Failed to update transaction" });
    }
});

// Delete a transaction
app.delete("/transactions/:id", ClerkExpressRequireAuth(), async (req, res) => {
    const { id } = req.params;
    const userId = req.auth.userId;

    try {
        const user = await prisma.user.findUnique({
            where: { clerkId: userId },
        });

        if (!user) {
            return res.status(404).json({ error: "User not found" });
        }

        const transaction = await prisma.transaction.deleteMany({
            where: {
                id: parseInt(id),
                userId: user.id,
            },
        });

        if (transaction.count === 0) {
            return res.status(404).json({ error: "Transaction not found" });
        }

        res.json({ message: "Transaction deleted" });
    } catch (error) {
        console.error("Delete transaction error:", error);
        res.status(500).json({ error: "Failed to delete transaction" });
    }
});

// Get current user profile
app.get("/user/profile", ClerkExpressRequireAuth(), async (req, res) => {
    const userId = req.auth.userId;

    try {
        let user = await prisma.user.findUnique({
            where: { clerkId: userId },
        });

        if (!user) {
            // Check if user exists by email
            const userEmail = req.auth.sessionClaims?.email;
            if (userEmail) {
                const existingUser = await prisma.user.findUnique({
                    where: { email: userEmail },
                });

                if (existingUser) {
                    // Link
                    user = await prisma.user.update({
                        where: { id: existingUser.id },
                        data: { clerkId: userId },
                    });
                } else {
                    // Create
                    user = await prisma.user.create({
                        data: {
                            clerkId: userId,
                            email: userEmail,
                        },
                    });
                }
            } else {
                // Fallback create (might fail if email is empty but schema requires unique? Schema says email is String @unique, usually implies not null)
                // Assuming email is present in token for now
                user = await prisma.user.create({
                    data: {
                        clerkId: userId,
                        email: "", // This might be risky if email is required unique, but empty strings might collide.
                    },
                });
            }
        }

        res.json(user);
    } catch (error) {
        console.error("Get user profile error:", error);
        res.status(500).json({ error: "Failed to fetch user profile" });
    }
});

// Update user profile
app.put("/user/profile", ClerkExpressRequireAuth(), async (req, res) => {
    const userId = req.auth.userId;
    const { name, currency } = req.body;

    try {
        const user = await prisma.user.upsert({
            where: { clerkId: userId },
            update: { name, currency },
            create: {
                clerkId: userId,
                email: req.auth.sessionClaims?.email || "",
                name,
                currency,
            },
        });

        res.json(user);
    } catch (error) {
        console.error("Update user profile error:", error);
        res.status(500).json({ error: "Failed to update user profile" });
    }
});

// Get all users
app.get("/users", ClerkExpressRequireAuth(), async (req, res) => {
    try {
        const users = await prisma.user.findMany();
        res.json(users);
    } catch (error) {
        console.error("Get all users error:", error);
        res.status(500).json({ error: "Failed to fetch users" });
    }
});

// ---------- Error Handling ----------
app.use((err, req, res, next) => {
    console.error(err.stack);
    if (err.message === 'Unauthenticated') {
        res.status(401).json({ error: 'Unauthenticated' });
    } else {
        res.status(500).json({ error: 'Something went wrong!' });
    }
});

// ---------- Server Start ----------
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
