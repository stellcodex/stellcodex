import { LayoutShell } from "@/components/layout/LayoutShell";
import { ListRow } from "@/components/common/ListRow";
import Link from "next/link";

const chats = [
  { id: "alpha", title: "DXF inceleme", subtitle: "3 gün önce" },
  { id: "beta", title: "Model kalite kontrol", subtitle: "Dün" },
  { id: "gamma", title: "Render planı", subtitle: "Bugün" },
];

export default function ChatsPage() {
  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="flex items-center justify-between">
          <div className="text-fs2 font-semibold">Sohbetler</div>
          <Link href="/chats/new" className="text-fs0 text-muted">
            Yeni sohbet
          </Link>
        </div>
        <div className="flex flex-col gap-cardGap">
          {chats.map((chat) => (
            <ListRow key={chat.id} title={chat.title} subtitle={chat.subtitle} href={`/chats/${chat.id}`} />
          ))}
        </div>
      </div>
    </LayoutShell>
  );
}
