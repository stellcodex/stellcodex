"use client";

import { useUser } from "@/context/UserContext";

type AiInsightsPanelProps = {
  mode: "admin" | "user";
};

const adminInsights = [
  "Render kuyruğunda hata artışı var",
  "Blender işleri ortalamaya göre yavaşladı",
  "DXF içe aktarmada katman ayrıştırma gecikiyor",
  "Depolama senkronunda birikim tespit edildi",
];

const userInsights = [
  "Güncel revizyonlar için Render deneyin",
  "DXF katman incelemesi için 2D’yi açın",
  "Montaj denetimi için Patlatma modunu kullanın",
];

export function AiInsightsPanel({ mode }: AiInsightsPanelProps) {
  const { user } = useUser();
  const items = mode === "admin" ? adminInsights : userInsights;

  return (
    <div className="flex flex-col gap-sp2 rounded-r2 border-soft bg-surface px-cardPad py-cardPad">
      <div className="text-fs1 font-semibold">AI Önerileri</div>
      <div className="text-fs0 text-muted">
        {mode === "admin" ? "Operasyon sinyalleri" : `${user.name} için`}
      </div>
      <ul className="flex flex-col gap-sp1 text-fs1 text-text">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-sp1">
            <span className="text-icon">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
