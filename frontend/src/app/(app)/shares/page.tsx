"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { listFiles, FileItem } from "@/services/api";

export default function SharesPage() {
  const router = useRouter();
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listFiles()
      .then((data) => setFiles(data.filter((f) => f.status === "ready")))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold text-slate-900">Paylaşımlar</h1>
      <p className="mt-1 text-sm text-slate-500">
        Dosyalarınızı buradan paylaşıma açabilirsiniz. Paylaşım linki viewer ekranında oluşturulur.
      </p>

      <div className="mt-6">
        {loading && <div className="text-sm text-slate-500">Yükleniyor...</div>}
        {!loading && files.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-200 p-8 text-center">
            <div className="text-3xl">⇗</div>
            <div className="mt-2 text-sm text-slate-500">
              Henüz hazır dosyanız yok. Önce dosya yükleyin.
            </div>
            <button
              onClick={() => router.push("/dashboard")}
              className="mt-3 rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Dashboard'a git
            </button>
          </div>
        )}
        {!loading && files.length > 0 && (
          <div className="grid gap-2">
            {files.map((file) => (
              <div
                key={file.file_id}
                className="flex items-center gap-3 rounded-xl border border-slate-100 bg-white px-4 py-3"
              >
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium text-slate-900">
                    {file.original_filename || file.original_name}
                  </div>
                  <div className="mt-0.5 text-xs text-slate-400">{file.kind?.toUpperCase()}</div>
                </div>
                <button
                  onClick={() => router.push(`/view/${file.file_id}`)}
                  className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-700 transition"
                >
                  Viewer'da Aç ve Paylaş
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
