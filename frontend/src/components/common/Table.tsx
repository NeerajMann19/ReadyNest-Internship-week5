import { ReactNode } from 'react';
import Loader from './Loader';

interface Column<T> {
  header: ReactNode;
  render: (row: T, index: number) => ReactNode;
  className?: string;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  isLoading?: boolean;
  emptyState?: ReactNode;
  className?: string;
}

export function Table<T>({
  data,
  columns,
  isLoading = false,
  emptyState,
  className = '',
}: TableProps<T>) {
  if (isLoading) {
    return <Loader type="spinner" text="Fetching records..." />;
  }

  if (data.length === 0) {
    return (
      <div className="p-8 text-center text-slate-400">
        {emptyState || 'No records found.'}
      </div>
    );
  }

  return (
    <div className={`overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40 ${className}`}>
      <table className="min-w-full divide-y divide-slate-800 text-left text-sm text-slate-300">
        <thead className="bg-slate-900 text-slate-200 uppercase font-semibold text-[10px] tracking-wider">
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} scope="col" className={`px-6 py-3.5 ${col.className || ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 bg-transparent">
          {data.map((row, rowIdx) => (
            <tr key={rowIdx} className="hover:bg-slate-800/30 transition duration-100">
              {columns.map((col, colIdx) => (
                <td key={colIdx} className={`px-6 py-4 whitespace-nowrap text-slate-300 font-medium ${col.className || ''}`}>
                  {col.render(row, rowIdx)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Table;
