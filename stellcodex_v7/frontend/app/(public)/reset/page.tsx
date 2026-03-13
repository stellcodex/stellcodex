"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { AuthShell, authInputClassName, authPrimaryButtonClassName } from "@/components/auth/AuthShell";

export default function ResetPage() {
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDone(true);
  }

  return (
    <AuthShell title="Choose a new password" subtitle="Recovery stays light and avoids a second branded interface.">
      <form className="auth-form" onSubmit={handleSubmit}>
        <input
          className={authInputClassName}
          type="password"
          value={password}
          placeholder="New password"
          onChange={(event) => setPassword(event.target.value)}
        />
        <button className={authPrimaryButtonClassName} type="submit">
          Update password
        </button>
        {done ? <p className="page-copy">Password updated for the next sign-in.</p> : null}
        <Link href="/login">Return to login</Link>
      </form>
    </AuthShell>
  );
}
