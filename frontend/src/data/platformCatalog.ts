export type PlatformAppId =
  | "viewer3d"
  | "viewer2d"
  | "docviewer"
  | "convert"
  | "mesh2d3d"
  | "moldcodes"
  | "library"
  | "drive"
  | "projects"
  | "accounting"
  | "socialmanager"
  | "feedpublisher"
  | "webbuilder"
  | "cms"
  | "admin"
  | "status";

export type PlatformApp = {
  id: PlatformAppId;
  name: string;
  shortName: string;
  category: "Engineering" | "Library" | "Business" | "Social" | "Web" | "System";
  description: string;
  summary: string;
  route: string;
  adminOnly?: boolean;
};

export const platformApps: PlatformApp[] = [
  {
    id: "viewer3d",
    name: "Viewer 3D",
    shortName: "3D",
    category: "Engineering",
    description: "STEP, STL, OBJ ve GLB dosyalarini embedded workspace icinde acar.",
    summary: "3D inceleme, deep-link viewer ve proje bagli cikti akisi.",
    route: "/app/viewer3d",
  },
  {
    id: "viewer2d",
    name: "Viewer 2D",
    shortName: "2D",
    category: "Engineering",
    description: "DXF ve cizim tabanli 2D dosyalari embedded viewer ile acar.",
    summary: "2D teknik cizim ve katman odakli akis.",
    route: "/app/viewer2d",
  },
  {
    id: "docviewer",
    name: "Doc Viewer",
    shortName: "DOC",
    category: "Engineering",
    description: "PDF ve dokuman dosyalarini isleme durumuyla birlikte acar.",
    summary: "Dokuman preview, processing ve download akisi.",
    route: "/app/docviewer",
  },
  {
    id: "convert",
    name: "Convert",
    shortName: "CNV",
    category: "Engineering",
    description: "Mevcut bir dosya icin donusum isi tetikler.",
    summary: "Gercek worker queue ile convert job cagrisi.",
    route: "/app/convert",
  },
  {
    id: "mesh2d3d",
    name: "Mesh 2D/3D",
    shortName: "M23",
    category: "Engineering",
    description: "Kaynak dosyadan yaklasik 3D mesh artefakti uretir.",
    summary: "OBJ cikti uretilir ve projeye baglanir.",
    route: "/app/mesh2d3d",
  },
  {
    id: "moldcodes",
    name: "MoldCodes",
    shortName: "MOL",
    category: "Engineering",
    description: "Mold base, guiding ve ejector katalog secimi ile STEP artefakti uretir.",
    summary: "Katalog, configurator, BOM kaydi ve export job akisi.",
    route: "/app/moldcodes",
  },
  {
    id: "library",
    name: "Library",
    shortName: "LIB",
    category: "Library",
    description: "Paylasilan varliklari ve publish akislarini listeler.",
    summary: "Feed ve publish aksiyonlari.",
    route: "/app/library",
  },
  {
    id: "drive",
    name: "Drive",
    shortName: "DRV",
    category: "Library",
    description: "Dosya, proje ve share merkezidir.",
    summary: "Upload, deep-link viewer ve share olusturma akisi.",
    route: "/app/drive",
  },
  {
    id: "projects",
    name: "Projects",
    shortName: "PRJ",
    category: "Business",
    description: "Proje olusturur, acar ve dosyalari projeye baglar.",
    summary: "CRUD proje listesi ve proje detay akisi.",
    route: "/app/projects",
  },
  {
    id: "accounting",
    name: "Accounting",
    shortName: "ACC",
    category: "Business",
    description: "Fatura, gelir ve gider kayitlarini proje bagli JSON artefakti olarak saklar.",
    summary: "Gercek persistence ile accounting MVP.",
    route: "/app/accounting",
  },
  {
    id: "socialmanager",
    name: "Social Manager",
    shortName: "SOC",
    category: "Social",
    description: "Baglanti kayitlari ve kanal hazirliklarini tutar.",
    summary: "OAuth olmadan draft ve account register MVP.",
    route: "/app/socialmanager",
  },
  {
    id: "feedpublisher",
    name: "Feed Publisher",
    shortName: "FED",
    category: "Social",
    description: "Icerik taslagi ve scheduler kayitlarini saklar.",
    summary: "Draft ve yayin takvimi MVP.",
    route: "/app/feedpublisher",
  },
  {
    id: "webbuilder",
    name: "Web Builder",
    shortName: "WEB",
    category: "Web",
    description: "Landing ve sayfa taslaklarini kaydeder.",
    summary: "Gercek save/edit akisi.",
    route: "/app/webbuilder",
  },
  {
    id: "cms",
    name: "CMS",
    shortName: "CMS",
    category: "Web",
    description: "Slug, baslik ve govde icerigi icin basit icerik yonetimi saglar.",
    summary: "Taslak tabanli CMS MVP.",
    route: "/app/cms",
  },
  {
    id: "admin",
    name: "Admin",
    shortName: "ADM",
    category: "System",
    description: "Rol-gated operasyon ve release durumu paneli.",
    summary: "Health, build ve audit odakli admin kontrolu.",
    route: "/app/admin",
    adminOnly: true,
  },
  {
    id: "status",
    name: "Status",
    shortName: "STS",
    category: "System",
    description: "Canli release sagligi ve build kaniti gorunumu.",
    summary: "Admin gorunur release gate ozeti.",
    route: "/app/status",
    adminOnly: true,
  },
];

export const platformCategories = ["Engineering", "Library", "Business", "Social", "Web", "System"] as const;

export function getPlatformApp(appId: string) {
  return platformApps.find((app) => app.id === appId) || null;
}

export function getVisiblePlatformApps(role: "user" | "admin") {
  return platformApps.filter((app) => !app.adminOnly || role === "admin");
}
