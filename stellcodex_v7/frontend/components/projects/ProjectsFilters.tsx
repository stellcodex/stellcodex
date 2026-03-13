"use client";

import { Input } from "@/components/primitives/Input";
import { Select } from "@/components/primitives/Select";

export interface ProjectsFiltersValue {
  search: string;
  sort: string;
}

export interface ProjectsFiltersProps {
  value: ProjectsFiltersValue;
  onChange: (value: ProjectsFiltersValue) => void;
}

export function ProjectsFilters({ value, onChange }: ProjectsFiltersProps) {
  return (
    <div className="sc-grid sc-grid-2">
      <Input
        placeholder="Search projects"
        value={value.search}
        onChange={(event) => onChange({ ...value, search: event.target.value })}
      />
      <Select value={value.sort} onChange={(event) => onChange({ ...value, sort: event.target.value })}>
        <option value="updated_desc">Recently updated</option>
        <option value="name_asc">Name A-Z</option>
      </Select>
    </div>
  );
}
