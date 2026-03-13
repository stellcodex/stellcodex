import type { ReactNode } from "react";

type TableProps = {
  head: ReactNode;
  body: ReactNode;
};

export function Table({ head, body }: TableProps) {
  return (
    <div className="sc-table-wrap">
      <table className="sc-table">
        <thead>{head}</thead>
        <tbody>{body}</tbody>
      </table>
    </div>
  );
}
