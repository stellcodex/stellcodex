import { LayoutShell } from "@/components/layout/LayoutShell";

export default function AccountPage() {
  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="text-fs2 font-semibold">Hesap</div>
        <div className="flex flex-col gap-cardGap rounded-r2 border-soft bg-surface px-cardPad py-cardPad">
          <div className="text-fs1">Ad: Ayşe Yılmaz</div>
          <div className="text-fs1">Rol: Yönetici</div>
          <button className="h-btnH rounded-r1 border-soft bg-surface px-sp3 text-fs1">Çıkış yap</button>
        </div>
      </div>
    </LayoutShell>
  );
}
