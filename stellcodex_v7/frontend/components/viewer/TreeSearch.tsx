"use client";

import { Input } from "@/components/primitives/Input";

export interface TreeSearchProps {
  value: string;
  onChange: (value: string) => void;
}

export function TreeSearch({ value, onChange }: TreeSearchProps) {
  return <Input placeholder="Search occurrences" value={value} onChange={(event) => onChange(event.target.value)} />;
}
