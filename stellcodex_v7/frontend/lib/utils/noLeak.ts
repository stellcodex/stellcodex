const BANNED_TOKENS = [
  "storage_key",
  "object_key",
  "\"bucket\"",
  "provider_url",
  "provider url",
  "filesystem path",
  "revision_id",
  "uploads/",
];

export function containsLeak(value: unknown) {
  const text = JSON.stringify(value ?? "", (_key, input) =>
    typeof input === "string" ? input.toLowerCase() : input
  );
  return BANNED_TOKENS.some((token) => text.includes(token));
}

export function assertNoLeak(value: unknown) {
  if (containsLeak(value)) {
    throw new Error("Unsafe backend field leak detected.");
  }
}

export function safePreview(value: unknown) {
  if (value == null) return null;
  if (containsLeak(value)) return "Restricted metadata";
  const raw = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  if (!raw) return null;
  return raw.length > 140 ? `${raw.slice(0, 137)}...` : raw;
}
