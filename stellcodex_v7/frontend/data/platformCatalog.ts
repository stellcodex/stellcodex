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

export type PlatformSurface =
  | "viewer3d"
  | "viewer2d"
  | "docviewer"
  | "job"
  | "configurator"
  | "records"
  | "route";

export type PlatformApp = {
  id: PlatformAppId;
  name: string;
  shortName: string;
  category: "Engineering" | "Library" | "Business" | "Social" | "Web" | "System";
  surface: PlatformSurface;
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
    surface: "viewer3d",
    description: "Opens STEP, STL, OBJ, and GLB files inside the embedded workspace.",
    summary: "3D review, deep-link viewing, and project-linked output flow.",
    route: "/app/viewer3d",
  },
  {
    id: "viewer2d",
    name: "Viewer 2D",
    shortName: "2D",
    category: "Engineering",
    surface: "viewer2d",
    description: "Opens DXF and drawing-based 2D files in the embedded viewer.",
    summary: "2D technical drawing review and layer-focused flow.",
    route: "/app/viewer2d",
  },
  {
    id: "docviewer",
    name: "Doc Viewer",
    shortName: "DOC",
    category: "Engineering",
    surface: "docviewer",
    description: "Opens PDF and document files together with processing state.",
    summary: "Document preview, processing, and download flow.",
    route: "/app/docviewer",
  },
  {
    id: "convert",
    name: "Convert",
    shortName: "CNV",
    category: "Engineering",
    surface: "job",
    description: "Triggers a conversion job for an existing file.",
    summary: "Conversion job dispatch through the real worker queue.",
    route: "/app/convert",
  },
  {
    id: "mesh2d3d",
    name: "Mesh 2D/3D",
    shortName: "M23",
    category: "Engineering",
    surface: "job",
    description: "Generates an approximate 3D mesh artifact from the source file.",
    summary: "Produces OBJ output and links it back to the project.",
    route: "/app/mesh2d3d",
  },
  {
    id: "moldcodes",
    name: "MoldCodes",
    shortName: "MOL",
    category: "Engineering",
    surface: "configurator",
    description: "Generates STEP artifacts from mold base, guiding, and ejector catalog selections.",
    summary: "Catalog, configurator, BOM recording, and export job flow.",
    route: "/app/moldcodes",
  },
  {
    id: "library",
    name: "Library",
    shortName: "LIB",
    category: "Library",
    surface: "route",
    description: "Lists shared assets and publishing flows.",
    summary: "Feed and publish actions.",
    route: "/app/library",
  },
  {
    id: "drive",
    name: "Drive",
    shortName: "DRV",
    category: "Library",
    surface: "route",
    description: "Acts as the file, project, and share hub.",
    summary: "Upload, deep-link viewer, and share creation flow.",
    route: "/app/drive",
  },
  {
    id: "projects",
    name: "Projects",
    shortName: "PRJ",
    category: "Business",
    surface: "route",
    description: "Creates and opens projects, then links files to them.",
    summary: "CRUD project list and project detail flow.",
    route: "/app/projects",
  },
  {
    id: "accounting",
    name: "Accounting",
    shortName: "ACC",
    category: "Business",
    surface: "records",
    description: "Stores billing, income, and expense records as project-linked JSON artifacts.",
    summary: "Accounting MVP with real persistence.",
    route: "/app/accounting",
  },
  {
    id: "socialmanager",
    name: "Social Manager",
    shortName: "SOC",
    category: "Social",
    surface: "records",
    description: "Keeps connection drafts; live OAuth is hidden until the blocker credentials exist.",
    summary: "Draft account registry, blocker visibility, and hidden post actions.",
    route: "/app/socialmanager",
  },
  {
    id: "feedpublisher",
    name: "Feed Publisher",
    shortName: "FED",
    category: "Social",
    surface: "records",
    description: "Stores content drafts and scheduler records; publishing stays hidden until blocker credentials exist.",
    summary: "Draft scheduler MVP, publish hidden until OAuth creds exist.",
    route: "/app/feedpublisher",
  },
  {
    id: "webbuilder",
    name: "Web Builder",
    shortName: "WEB",
    category: "Web",
    surface: "records",
    description: "Stores landing and page drafts and can generate real /s token publish links.",
    summary: "Real save/edit flow and publish-through-share flow.",
    route: "/app/webbuilder",
  },
  {
    id: "cms",
    name: "CMS",
    shortName: "CMS",
    category: "Web",
    surface: "records",
    description: "Provides simple content management for slug, title, and body content and can generate a real public share link.",
    summary: "Draft plus publish-through-share CMS MVP.",
    route: "/app/cms",
  },
  {
    id: "admin",
    name: "Admin",
    shortName: "ADM",
    category: "System",
    surface: "route",
    description: "Role-gated operations and release status panel.",
    summary: "Admin control focused on health, build, and audit.",
    route: "/app/admin",
    adminOnly: true,
  },
  {
    id: "status",
    name: "Status",
    shortName: "STS",
    category: "System",
    surface: "route",
    description: "Live release health and build evidence view.",
    summary: "Admin-visible release gate summary.",
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
