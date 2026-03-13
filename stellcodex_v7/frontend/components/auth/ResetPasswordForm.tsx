"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AuthShell, authInputClassName, authPrimaryButtonClassName } from "@/components/auth/AuthShell";
import { ApiError } from "@/lib/api/errors";
import { resetPasswordWithToken } from "@/lib/api/auth";

export function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = useMemo(() => searchParams.get("token")?.trim() || "", [searchParams]);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      setError("Reset token is missing from this link.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Password confirmation does not match.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      await resetPasswordWithToken(token, password);
      setMessage("Password updated. Redirecting to sign in.");
      window.setTimeout(() => router.push("/login"), 800);
    } catch (cause) {
      const safeMessage = cause instanceof ApiError ? cause.safeMessage : "Password reset could not be completed.";
      setError(safeMessage);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell title="Choose a new password" subtitle="Finish password recovery with the reset token issued by the live STELLCODEX account API.">
      <form className="auth-form" onSubmit={handleSubmit}>
        {!token ? <p className="page-copy">Reset link invalid or missing.</p> : null}
        <input
          className={authInputClassName}
          type="password"
          value={password}
          placeholder="New password"
          onChange={(event) => setPassword(event.target.value)}
          disabled={!token || submitting}
          required
        />
        <input
          className={authInputClassName}
          type="password"
          value={confirmPassword}
          placeholder="Confirm new password"
          onChange={(event) => setConfirmPassword(event.target.value)}
          disabled={!token || submitting}
          required
        />
        {error ? <p className="page-copy">{error}</p> : null}
        {message ? <p className="page-copy">{message}</p> : null}
        <button className={authPrimaryButtonClassName} type="submit" disabled={!token || submitting}>
          {submitting ? "Updating..." : "Update password"}
        </button>
        <Link href="/login">Return to login</Link>
      </form>
    </AuthShell>
  );
}
