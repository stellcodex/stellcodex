function resolveBackendOrigin() {
  const value = String(process.env.BACKEND_API_ORIGIN || "").trim().replace(/\/+$/, "");
  return value || "http://127.0.0.1:18000";
}

type ViewerPageProps = {
  searchParams: Promise<{
    id?: string | string[];
  }>;
};

export default async function ViewerPage({ searchParams }: ViewerPageProps) {
  const params = await searchParams;
  const rawId = params.id;
  const id = Array.isArray(rawId) ? (rawId[0] ?? "").trim() : (rawId ?? "").trim();

  if (!id) {
    return (
      <main className="mx-auto max-w-[900px] px-4 py-6 text-sm leading-6">
        <p>Missing id</p>
      </main>
    );
  }

  try {
    const response = await fetch(`${resolveBackendOrigin()}/api/v1/files/${encodeURIComponent(id)}`, {
      cache: "no-store",
    });
    const json = await response.json();

    if (!response.ok) {
      const detail =
        json && typeof json === "object" && "detail" in json ? String(json.detail ?? "") : "";
      throw new Error(detail || `File request failed with ${response.status}`);
    }

    const data: Record<string, unknown> =
      json && typeof json === "object" && !Array.isArray(json)
        ? (json as Record<string, unknown>)
        : { body: json };

    return (
      <main className="mx-auto max-w-[900px] px-4 py-6 text-sm leading-6">
        <div>id: {String(data.id ?? "")}</div>
        {data.name !== undefined ? <div>name: {String(data.name)}</div> : null}
        {data.status !== undefined ? <div>status: {String(data.status)}</div> : null}
        {data.contentType !== undefined ? <div>contentType: {String(data.contentType)}</div> : null}
        <pre className="mt-4 whitespace-pre-wrap text-sm leading-6">
          body:{" "}
          {typeof data.body === "string" ? data.body : JSON.stringify(data.body ?? data, null, 2)}
        </pre>
      </main>
    );
  } catch (error) {
    return (
      <main className="mx-auto max-w-[900px] px-4 py-6 text-sm leading-6">
        <p>{error instanceof Error ? error.message : "Failed to load file."}</p>
      </main>
    );
  }
}
