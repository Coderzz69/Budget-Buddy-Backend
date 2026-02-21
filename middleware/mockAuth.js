
export const MockAuth = () => {
    return (req, res, next) => {
        console.log("Using Mock Auth Middleware");
        req.auth = {
            userId: "user_399XsciyzrSXXP6i8PGgoyzCr5l",
            sessionId: "mock_session",
            getToken: async () => "mock_token",
            claims: { email: "snathkumarcoonani@gmail.com" },
            sessionClaims: { email: "snathkumarcoonani@gmail.com" }
        };
        next();
    };
};
