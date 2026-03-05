export type PlatformAppId =
  | "workspace"
  | "viewer3d"
  | "viewer2d"
  | "docviewer"
  | "dataanalyzer"
  | "agentdashboard"
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

export type PlatformAppStatus = "active" | "beta" | "hidden";

export type PlatformApp = {
  id: PlatformAppId;
  name: string;
  shortName: string;
  icon: string;
  category: "Workspace" | "Engineering" | "Library" | "Business" | "Social" | "Web" | "System";
  description: string;
  summary: string;
  route: string;
  status: PlatformAppStatus;
  requiresBackend: boolean;
  adminOnly?: boolean;
};

export const platformApps: PlatformApp[] = [
  {
    id: "workspace",
    name: "Workspace",
    shortName: "WS",
    icon: "WS",
    category: "Workspace",
    description: "Projeler, dosyalar, kutuphane ve ayarlar icin merkezi calisma alani.",
    summary: "Session tabanli tek girisli calisma paneli.",
    route: "/workspace",
    status: "active",
    requiresBackend: false,
  },
  {
    id: "viewer3d",
    name: "CAD Viewer",
    shortName: "CAD",
    icon: "3D",
    category: "Engineering",
    description: "STEP/STP, Parasolid, IGES, STL, OBJ, GLTF ve benzeri 3D CAD dosyalarini acar.",
    summary: "Orbit/pan/zoom, fit, section, explode, hide-isolate ve olcum akislarini sunar.",
    route: "/app/viewer3d",
    status: "active",
    requiresBackend: true,
  },
  {
    id: "viewer2d",
    name: "Viewer 2D",
    shortName: "2D",
    icon: "2D",
    category: "Engineering",
    description: "DXF ve cizim tabanli 2D dosyalari embedded viewer ile acar.",
    summary: "2D teknik cizim ve katman odakli akis.",
    route: "/app/viewer2d",
    status: "active",
    requiresBackend: true,
  },
  {
    id: "docviewer",
    name: "Document Viewer",
    shortName: "DOC",
    icon: "DOC",
    category: "Engineering",
    description: "PDF/DOCX/XLSX/TXT/MD ve arsiv preview dosyalarini acar.",
    summary: "Dokuman preview, arama, download ve donusum fallback akislarini sunar.",
    route: "/app/docviewer",
    status: "active",
    requiresBackend: true,
  },
  {
    id: "dataanalyzer",
    name: "Data Analyzer",
    shortName: "ANL",
    icon: "ANL",
    category: "Engineering",
    description: "CAD geometry, assembly ve DFM bulgularini tek raporda analiz eder.",
    summary: "Bounding box, part count, wall/draft, risk flag ve oneriler uretir.",
    route: "/app/dataanalyzer",
    status: "active",
    requiresBackend: true,
  },
  {
    id: "agentdashboard",
    name: "Agent Dashboard",
    shortName: "AGT",
    icon: "AGT",
    category: "Engineering",
    description: "Geometry/Manufacturing/CAD Repair/Document/Web/Data agentlerini calistirir.",
    summary: "Tek agent cagrisi veya coklu agent orchestrator akisi.",
    route: "/app/agentdashboard",
    status: "active",
    requiresBackend: true,
  },
  {
    id: "convert",
    name: "Convert",
    shortName: "CNV",
    icon: "CNV",
    category: "Engineering",
    description: "Mevcut bir dosya icin donusum isi tetikler.",
    summary: "Gercek worker queue ile convert job cagrisi.",
    route: "/app/convert",
    status: "active",
    requiresBackend: true,
  },
  {
    id: "mesh2d3d",
    name: "Mesh 2D/3D",
    shortName: "M23",
    icon: "M23",
    category: "Engineering",
    description: "Kaynak dosyadan yaklasik 3D mesh artefakti uretir.",
    summary: "OBJ cikti uretilir ve projeye baglanir.",
    route: "/app/mesh2d3d",
    status: "beta",
    requiresBackend: true,
  },
  {
    id: "moldcodes",
    name: "MoldCodes",
    shortName: "MOL",
    icon: "MOL",
    category: "Engineering",
    description: "Mold base, guiding ve ejector katalog secimi ile STEP artefakti uretir.",
    summary: "Katalog, configurator, BOM kaydi ve export job akisi.",
    route: "/app/moldcodes",
    status: "beta",
    requiresBackend: true,
  },
  {
    id: "library",
    name: "Library Manager",
    shortName: "LIB",
    icon: "LIB",
    category: "Library",
    description: "Paylasilan varliklari ve publish akislarini listeler.",
    summary: "Feed ve publish aksiyonlari.",
    route: "/app/library",
    status: "active",
    requiresBackend: true,
  },
  {
    id: "drive",
    name: "Drive",
    shortName: "DRV",
    icon: "DRV",
    category: "Library",
    description: "Dosya, proje ve share merkezidir.",
    summary: "Upload, deep-link viewer ve share olusturma akisi.",
    route: "/app/drive",
    status: "active",
    requiresBackend: true,
  },
  {
    id: "projects",
    name: "Project Manager",
    shortName: "PRJ",
    icon: "PRJ",
    category: "Business",
    description: "Proje olusturur, acar ve dosyalari projeye baglar.",
    summary: "CRUD proje listesi ve proje detay akisi.",
    route: "/app/projects",
    status: "active",
    requiresBackend: true,
  },
  {
    id: "accounting",
    name: "Accounting",
    shortName: "ACC",
    icon: "ACC",
    category: "Business",
    description: "Fatura, gelir ve gider kayitlarini proje bagli JSON artefakti olarak saklar.",
    summary: "Gercek persistence ile accounting MVP.",
    route: "/app/accounting",
    status: "beta",
    requiresBackend: true,
  },
  {
    id: "socialmanager",
    name: "Social Manager",
    shortName: "SOC",
    icon: "SOC",
    category: "Social",
    description: "Baglanti taslaklarini tutar; canli OAuth baglantisi blocker anahtarlari gelene kadar gizlidir.",
    summary: "Draft account registry, blocker gorunumu ve gizli post aksiyonlari.",
    route: "/app/socialmanager",
    status: "beta",
    requiresBackend: true,
  },
  {
    id: "feedpublisher",
    name: "Feed Publisher",
    shortName: "FED",
    icon: "FED",
    category: "Social",
    description: "Icerik taslagi ve scheduler kayitlarini saklar; publish aksiyonu blocker anahtarlari gelene kadar gizlidir.",
    summary: "Draft scheduler MVP, publish hidden until OAuth creds exist.",
    route: "/app/feedpublisher",
    status: "beta",
    requiresBackend: true,
  },
  {
    id: "webbuilder",
    name: "Web Builder",
    shortName: "WEB",
    icon: "WEB",
    category: "Web",
    description: "Landing ve sayfa taslaklarini kaydeder ve gercek /s token publish linki uretebilir.",
    summary: "Gercek save/edit ve publish-through-share akisi.",
    route: "/app/webbuilder",
    status: "beta",
    requiresBackend: true,
  },
  {
    id: "cms",
    name: "CMS",
    shortName: "CMS",
    icon: "CMS",
    category: "Web",
    description: "Slug, baslik ve govde icerigi icin basit icerik yonetimi saglar ve gercek public share linki uretebilir.",
    summary: "Taslak + publish-through-share CMS MVP.",
    route: "/app/cms",
    status: "beta",
    requiresBackend: true,
  },
  {
    id: "admin",
    name: "Admin",
    shortName: "ADM",
    icon: "ADM",
    category: "System",
    description: "Rol-gated operasyon ve release durumu paneli.",
    summary: "Health, build ve audit odakli admin kontrolu.",
    route: "/app/admin",
    status: "hidden",
    requiresBackend: true,
    adminOnly: true,
  },
  {
    id: "status",
    name: "Status",
    shortName: "STS",
    icon: "STS",
    category: "System",
    description: "Canli release sagligi ve build kaniti gorunumu.",
    summary: "Admin gorunur release gate ozeti.",
    route: "/app/status",
    status: "hidden",
    requiresBackend: true,
    adminOnly: true,
  },
];

export const platformCategories = ["Workspace", "Engineering", "Library", "Business", "Social", "Web", "System"] as const;

export function getPlatformApp(appId: string) {
  return platformApps.find((app) => app.id === appId) || null;
}

export function getVisiblePlatformApps(
  role: "user" | "admin",
  options?: {
    showBeta?: boolean;
    includeHidden?: boolean;
  }
) {
  const showBeta = options?.showBeta === true;
  const includeHidden = options?.includeHidden === true;
  return platformApps.filter((app) => {
    if (app.adminOnly && role !== "admin") return false;
    if (app.status === "hidden" && !includeHidden) return false;
    if (app.status === "beta" && !showBeta) return false;
    return true;
  });
}
