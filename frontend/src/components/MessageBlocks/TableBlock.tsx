import type { TableBlock as TableBlockType } from '../../types/messageBlocks';

interface TableBlockProps {
  block: TableBlockType;
}

// Helper function to parse HTML color styling and extract content
function parseStyledCell(cell: string | number): { content: string | number; className: string } {
  if (typeof cell === 'number') {
    return { content: cell, className: '' };
  }

  // Check for HTML span with color style
  const colorMatch = cell.match(/<span style="color:(\w+)">(.*?)<\/span>/);
  if (colorMatch) {
    const color = colorMatch[1];
    const content = colorMatch[2];

    // Map HTML colors to Tailwind classes
    const colorMap: Record<string, string> = {
      'red': 'text-red-500',
      'green': 'text-green-500',
      'blue': 'text-blue-500',
      'orange': 'text-orange-500',
      'yellow': 'text-yellow-500',
    };

    return {
      content,
      className: colorMap[color] || '',
    };
  }

  return { content: cell, className: '' };
}

export function TableBlock({ block }: TableBlockProps) {
  return (
    <div className="overflow-x-auto -mx-3 px-3 sm:mx-0 sm:px-0">
      {block.caption && (
        <div className="text-sm font-medium text-foreground mb-2">{block.caption}</div>
      )}
      <table className="min-w-full divide-y divide-border border border-border rounded-lg text-xs sm:text-sm">
        <thead className="bg-muted/50">
          <tr>
            {block.headers.map((header, idx) => (
              <th
                key={idx}
                className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-card divide-y divide-border">
          {block.rows.map((row, rowIdx) => (
            <tr key={rowIdx} className="hover:bg-muted/30 transition-colors">
              {row.map((cell, cellIdx) => {
                const { content, className } = parseStyledCell(cell);
                return (
                  <td key={cellIdx} className={`px-4 py-3 text-sm whitespace-nowrap ${className}`}>
                    {typeof content === 'number' ? content.toLocaleString('fr-CH') : content}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
