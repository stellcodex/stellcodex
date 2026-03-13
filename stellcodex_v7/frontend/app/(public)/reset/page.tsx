"use client";

import Link from "next/link";
import { AuthShell } from "@/components/auth/AuthShell";

export default function ResetPage() {
  return (
    <AuthShell title="Choose a new password" subtitle="The public reset-token flow remains blocked until backend recovery contracts are implemented.">
      <div className="auth-form">
        <p className="page-copy">Reset tokens are not accepted by this deployment yet, so this route fails closed.</p>
        <p className="page-copy">Use a signed-in session to change your password or ask an administrator to rotate access.</p>
        <Link href="/login">Return to login</Link>
      </div>
    </AuthShell>
  );
}
