// @ts-nocheck
/* eslint-disable no-console */
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  await prisma.project.upsert({
    where: { id: "genel-project" },
    update: { name: "Genel" },
    create: { id: "genel-project", name: "Genel" },
  });

  const folders = [
    ["folder-3d", "3D Modeller", "MODELS_3D"],
    ["folder-2d", "2D Çizimler", "DRAWINGS_2D"],
    ["folder-docs", "Dokümanlar", "DOCUMENTS"],
    ["folder-img", "Görseller", "IMAGES"],
    ["folder-archive", "Arşiv", "ARCHIVE"],
  ] as const;

  for (const [id, name, systemKey] of folders) {
    await prisma.folder.upsert({
      where: { id },
      update: { name, systemKey, isSystem: true },
      create: {
        id,
        projectId: "genel-project",
        name,
        systemKey,
        isSystem: true,
      },
    });
  }

  const files = [
    ["file-step", "folder-3d", "ornek.step", "step", "model/octet-stream", BigInt(1000000), "3d", "viewer3d"],
    ["file-dxf", "folder-2d", "plan.dxf", "dxf", "image/vnd.dxf", BigInt(200000), "2d", "viewer2d"],
    ["file-pdf", "folder-docs", "teklif.pdf", "pdf", "application/pdf", BigInt(500000), "pdf", "pdf"],
    ["file-img", "folder-img", "urun.png", "png", "image/png", BigInt(600000), "image", "image"],
    ["file-zip", "folder-archive", "paket.zip", "zip", "application/zip", BigInt(700000), "zip", "archive"],
  ] as const;

  for (const [id, folderId, name, ext, mime, sizeBytes, kind, engine] of files) {
    await prisma.file.upsert({
      where: { id },
      update: { folderId, name, ext, mime, sizeBytes, kind, engine },
      create: {
        id,
        projectId: "genel-project",
        folderId,
        name,
        ext,
        mime,
        sizeBytes,
        kind,
        engine,
        storageKey: `seed/${name}`,
      },
    });
  }

  const jobs = [
    ["job-ready", "file-step", "SUCCEEDED", "ready", 100],
    ["job-preview", "file-dxf", "RUNNING", "preview", 72],
    ["job-security", "file-pdf", "RUNNING", "security", 35],
    ["job-approval", "file-zip", "NEEDS_APPROVAL", "ready", 100],
  ] as const;

  for (const [id, fileId, status, stage, progress] of jobs) {
    await prisma.job.upsert({
      where: { id },
      update: { fileId, status, stage, progress },
      create: { id, fileId, status, stage, progress },
    });
  }

  await prisma.shareLink.upsert({
    where: { token: "demo-share-token" },
    update: { fileId: "file-step" },
    create: {
      fileId: "file-step",
      token: "demo-share-token",
      canView: true,
      canDownload: true,
    },
  });

  console.log("STELLCODEX seed completed");
}

main()
  .catch((err) => {
    console.error(err);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
