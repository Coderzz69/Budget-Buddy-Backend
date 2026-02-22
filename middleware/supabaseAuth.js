import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
dotenv.config();

// Initialize the Supabase client
const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_KEY
);

export const SupabaseAuth = () => {
    return async (req, res, next) => {
        try {
            const authHeader = req.headers.authorization;

            if (!authHeader || !authHeader.startsWith('Bearer ')) {
                return res.status(401).json({ error: 'Unauthenticated: No token provided' });
            }

            const token = authHeader.split(' ')[1];

            // Verify the token with Supabase
            const { data: { user }, error } = await supabase.auth.getUser(token);

            if (error || !user) {
                console.error("Supabase Auth Error:", error?.message);
                return res.status(401).json({ error: 'Unauthenticated: Invalid or expired token' });
            }

            // Attach user data to the request object (matching previous req.auth structure)
            req.auth = {
                userId: user.id, // This is the Supabase Auth User ID (UUID)
                claims: {
                    email: user.email,
                }
            };

            next();
        } catch (error) {
            console.error("Supabase Auth Middleware Exception:", error);
            res.status(500).json({ error: 'Internal server error during authentication' });
        }
    };
};
