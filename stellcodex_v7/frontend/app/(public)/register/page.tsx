"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthShell, authInputClassName, authPrimaryButtonClassName } from "@/components/auth/AuthShell";
import { ApiError } from "@/lib/api/errors";
import { registerWithPassword } from "@/lib/api/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await registerWithPassword(email.trim(), password);
      router.push("/");
    } catch (cause) {
      const message = cause instanceof ApiError ? cause.safeMessage : "Account creation could not be completed.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell title="Create account" subtitle="Create a real STELLCODEX user session through the live account API.">
      <form className="auth-form" onSubmit={handleSubmit}>
        <input className={authInputClassName} value={email} placeholder="name@company.com" onChange={(event) => setEmail(event.target.value)} />
        <input
          className={authInputClassName}
          type="password"
          value={password}
          placeholder="Password"
          onChange={(event) => setPassword(event.target.value)}
        />
        {error ? <p className="page-copy">{error}</p> : null}
        <button className={authPrimaryButtonClassName} type="submit" disabled={submitting}>
          {submitting ? "Creating..." : "Create account"}
        </button>
        <Link href="/login">Already have access?</Link>
      </form>
    </AuthShell>
  );
}
