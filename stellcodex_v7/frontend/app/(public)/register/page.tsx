"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthShell, authInputClassName, authPrimaryButtonClassName } from "@/components/auth/AuthShell";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (typeof window !== "undefined") {
      window.localStorage.setItem("scx_token", `${name || "user"}:${email || "demo"}`);
    }
    router.push("/");
  }

  return (
    <AuthShell title="Create account" subtitle="Stay inside the same suite identity from signup to daily work.">
      <form className="auth-form" onSubmit={handleSubmit}>
        <input className={authInputClassName} value={name} placeholder="Full name" onChange={(event) => setName(event.target.value)} />
        <input className={authInputClassName} value={email} placeholder="name@company.com" onChange={(event) => setEmail(event.target.value)} />
        <button className={authPrimaryButtonClassName} type="submit">
          Create account
        </button>
        <Link href="/login">Already have access?</Link>
      </form>
    </AuthShell>
  );
}
