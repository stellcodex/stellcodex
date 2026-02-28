import { SectionHeader } from "@/components/layout/SectionHeader";

const plans = [
  {
    name: "Free",
    quota: "5 dosya / ay",
    features: ["Temel viewer", "Unlisted share", "Standart export"],
  },
  {
    name: "Pro",
    quota: "200 dosya / ay",
    features: ["DXF + STEP gelişmiş", "Library publish", "Priority processing"],
  },
  {
    name: "Enterprise",
    quota: "Sınırsız",
    features: ["SSO/SAML", "RBAC + audit", "Dedicated support"],
  },
];

export default function DashboardPlansPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Plans"
        description="Paketler, kotalar ve faturalama entegrasyonu."
        crumbs={[{ label: "Panel", href: "/dashboard" }, { label: "Plans" }]}
      />

      <div className="grid gap-4 lg:grid-cols-3">
        {plans.map((plan) => (
          <article key={plan.name} className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="text-lg font-semibold text-slate-900">{plan.name}</div>
            <div className="mt-1 text-sm text-slate-500">{plan.quota}</div>
            <ul className="mt-4 grid gap-2 text-sm text-slate-700">
              {plan.features.map((feature) => (
                <li key={feature} className="rounded-lg bg-slate-50 px-2 py-1">
                  {feature}
                </li>
              ))}
            </ul>
            <button className="mt-4 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700">
              Billing Hook
            </button>
          </article>
        ))}
      </div>
    </div>
  );
}

