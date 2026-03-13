"use client";

import Link from "next/link";
import { AuthShell } from "@/components/auth/AuthShell";

export default function ForgotPage() {
  return (
    <AuthShell title="Reset access" subtitle="Password recovery is disabled until the live reset flow is wired end to end.">
      <div className="auth-form">
        <p className="page-copy">This deployment does not expose a verified password recovery endpoint yet.</p>
        <p className="page-copy">Use an active session to change your password or contact a STELLCODEX administrator.</p>
        <Link href="/login">Back to login</Link>
      </div>
    </AuthShell>
  );
}
