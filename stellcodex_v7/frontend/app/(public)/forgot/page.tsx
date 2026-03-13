"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { AuthShell, authInputClassName, authPrimaryButtonClassName } from "@/components/auth/AuthShell";
import { ApiError } from "@/lib/api/errors";
import { requestPasswordReset } from "@/lib/api/auth";

export default function ForgotPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      const result = await requestPasswordReset(email.trim());
      if (result.deliveryEnabled) {
        setMessage("If that account exists, a reset link will be sent to the inbox on file.");
      } else {
        setMessage("Password recovery mail is not configured on this deployment. Use a signed-in session or contact an administrator.");
      }
    } catch (cause) {
      const safeMessage = cause instanceof ApiError ? cause.safeMessage : "Password recovery could not be requested.";
      setError(safeMessage);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell title="Reset access" subtitle="Request a one-time reset link through the live STELLCODEX account API.">
      <form className="auth-form" onSubmit={handleSubmit}>
        <input
          className={authInputClassName}
          type="email"
          value={email}
          placeholder="name@company.com"
          onChange={(event) => setEmail(event.target.value)}
          required
        />
        {error ? <p className="page-copy">{error}</p> : null}
        {message ? <p className="page-copy">{message}</p> : null}
        <button className={authPrimaryButtonClassName} type="submit" disabled={submitting}>
          {submitting ? "Requesting..." : "Send reset link"}
        </button>
        <Link href="/login">Back to login</Link>
      </form>
    </AuthShell>
  );
}
