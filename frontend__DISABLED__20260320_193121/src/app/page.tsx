import { redirect } from "next/navigation";

import { DEFAULT_WORKSPACE_ROUTE, SIGN_IN_ROUTE, getServerSession } from "@/lib/server/auth";

export default async function RootPage() {
  const session = await getServerSession();
  redirect(session.authenticated ? DEFAULT_WORKSPACE_ROUTE : SIGN_IN_ROUTE);
}
