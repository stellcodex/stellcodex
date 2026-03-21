import { redirect } from "next/navigation";

import { SignInScreen } from "@/components/auth/SignInScreen";
import { DEFAULT_WORKSPACE_ROUTE, getServerSession, sanitizeNextPath } from "@/lib/server/auth";

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ auth?: string; next?: string }>;
}) {
  const [session, params] = await Promise.all([getServerSession(), searchParams]);
  const nextPath = sanitizeNextPath(params.next) ?? DEFAULT_WORKSPACE_ROUTE;

  if (session.authenticated) {
    redirect(nextPath);
  }

  return <SignInScreen authCode={params.auth} nextPath={nextPath} />;
}
