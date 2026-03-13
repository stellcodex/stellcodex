import type { ReactNode } from "react";

type TableProps = {
  head: ReactNode;
  body: ReactNode;
  empty?: ReactNode;
  loading?: boolean;
};

export function Table({ head, body, empty, loading = false }: TableProps) {
  return (
    <div className="sc-table-wrap">
      <table className="sc-table">
        <thead>{head}</thead>
        <tbody>{loading ? <tr><td colSpan={99}>{empty || "Loading..."}</td></tr> : body}</tbody>
      </table>
    </div>
  );
}
