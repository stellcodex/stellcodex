"use client";

import { Input } from "@/components/primitives/Input";

export interface AdminFiltersProps {
  value: string;
  onChange: (value: string) => void;
}

export function AdminFilters({ value, onChange }: AdminFiltersProps) {
  return <Input placeholder="Filter" value={value} onChange={(event) => onChange(event.target.value)} />;
}
