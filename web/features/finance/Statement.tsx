import { money } from '../../lib/format';

export type StatementRow = { label: string; amount?: number; kind?: 'section' | 'item' | 'subtotal' | 'total' };

// Tabla contable: conceptos a la izquierda, importes alineados a la derecha; negativos entre paréntesis.
export function Statement({ rows, testId }: { rows: StatementRow[]; testId: string }) {
  return (
    <div className="adminTableWrap">
      <table className="adminTable financeTable" data-testid={testId}>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.label}-${index}`} className={`financeRow-${row.kind ?? 'item'}`}>
              <td>{row.label}</td>
              <td className={`financeAmount${row.amount !== undefined && row.amount < 0 ? ' negative' : ''}`}>
                {row.amount === undefined ? '' : row.amount < 0 ? `(${money(-row.amount)})` : money(row.amount)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
