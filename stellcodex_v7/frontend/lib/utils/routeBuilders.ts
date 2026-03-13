export const routeBuilders = {
  dashboard: () => "/dashboard",
  projects: () => "/projects",
  project: (projectId: string) => `/projects/${encodeURIComponent(projectId)}`,
  file: (fileId: string) => `/files/${encodeURIComponent(fileId)}`,
  viewer: (fileId: string) => `/files/${encodeURIComponent(fileId)}/viewer`,
  shares: () => "/shares",
  publicShare: (token: string) => `/s/${encodeURIComponent(token)}`,
  admin: () => "/admin",
  settings: () => "/settings",
};
