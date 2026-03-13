export const designTokens = {
  colors: {
    bgApp: "var(--sc-bg-app)",
    bgSidebar: "var(--sc-bg-sidebar)",
    bgHeader: "var(--sc-bg-header)",
    bgPanel: "var(--sc-bg-panel)",
    fgPrimary: "var(--sc-fg-primary)",
    fgMuted: "var(--sc-fg-muted)",
    border: "var(--sc-border-default)",
    accent: "var(--sc-accent)",
  },
  spacing: {
    1: "var(--sc-space-1)",
    2: "var(--sc-space-2)",
    3: "var(--sc-space-3)",
    4: "var(--sc-space-4)",
    5: "var(--sc-space-5)",
    6: "var(--sc-space-6)",
    8: "var(--sc-space-8)",
  },
  radius: {
    sm: "var(--sc-radius-sm)",
    md: "var(--sc-radius-md)",
    lg: "var(--sc-radius-lg)",
  },
} as const;
