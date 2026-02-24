import { NextResponse } from "next/server";
import { createFolder, deleteFiles, getProjectTree, moveFiles } from "@/lib/stellcodex/mock-db";

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tree = getProjectTree(id);
  if (!tree) return NextResponse.json({ error: "Proje bulunamadı." }, { status: 404 });
  return NextResponse.json(tree);
}

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;
  const action = String(body.action || "");
  if (action === "createFolder") {
    const folder = createFolder({
      projectId: id,
      parentId: typeof body.parentId === "string" ? body.parentId : null,
      name: typeof body.name === "string" ? body.name : "Yeni Klasör",
    });
    return NextResponse.json({ folder });
  }
  if (action === "moveFiles") {
    const fileIds = Array.isArray(body.fileIds) ? body.fileIds.filter((v): v is string => typeof v === "string") : [];
    const folderId = typeof body.folderId === "string" ? body.folderId : "";
    if (!folderId) return NextResponse.json({ error: "Hedef klasör gerekli." }, { status: 400 });
    const moved = moveFiles({ fileIds, folderId });
    return NextResponse.json({ moved: moved.length });
  }
  if (action === "deleteFiles") {
    const fileIds = Array.isArray(body.fileIds) ? body.fileIds.filter((v): v is string => typeof v === "string") : [];
    const result = deleteFiles(fileIds);
    return NextResponse.json(result);
  }
  return NextResponse.json({ error: "Geçersiz işlem." }, { status: 400 });
}

