"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { AuthShell, authInputClassName, authPrimaryButtonClassName } from "@/components/auth/AuthShell";

export default function ForgotPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSent(true);
  }

  return (
    <AuthShell title="Reset access" subtitle="Keep recovery simple and aligned with the main suite shell.">
      <form className="auth-form" onSubmit={handleSubmit}>
        <input className={authInputClassName} value={email} placeholder="name@company.com" onChange={(event) => setEmail(event.target.value)} />
        <button className={authPrimaryButtonClassName} type="submit">
          Send reset link
        </button>
        {sent ? <p className="page-copy">If this email exists, a reset link has been prepared.</p> : null}
        <Link href="/login">Back to login</Link>
      </form>
    </AuthShell>
  );
}
