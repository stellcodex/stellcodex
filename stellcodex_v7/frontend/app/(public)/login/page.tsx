"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthShell, authInputClassName, authPrimaryButtonClassName } from "@/components/auth/AuthShell";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (typeof window !== "undefined") {
      window.localStorage.setItem("scx_token", `${email || "guest"}:${password || "demo"}`);
    }
    router.push("/");
  }

  return (
    <AuthShell title="Sign in" subtitle="Return to the shared STELLCODEX shell without a detached console.">
      <form className="auth-form" onSubmit={handleSubmit}>
        <input className={authInputClassName} value={email} placeholder="name@company.com" onChange={(event) => setEmail(event.target.value)} />
        <input
          className={authInputClassName}
          type="password"
          value={password}
          placeholder="Password"
          onChange={(event) => setPassword(event.target.value)}
        />
        <button className={authPrimaryButtonClassName} type="submit">
          Continue
        </button>
        <Link href="/forgot">Forgot password?</Link>
      </form>
    </AuthShell>
  );
}
