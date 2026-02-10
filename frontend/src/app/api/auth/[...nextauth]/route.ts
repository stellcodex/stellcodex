import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

const providers = [];

if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) {
  providers.push(
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    })
  );
}

const authHandler =
  providers.length > 0
    ? NextAuth({
        providers,
        secret: process.env.NEXTAUTH_SECRET,
      })
    : () =>
        new Response("OAuth not configured", {
          status: 503,
          headers: { "Content-Type": "text/plain" },
        });

export { authHandler as GET, authHandler as POST };
