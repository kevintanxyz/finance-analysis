import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { TextBlock as TextBlockType } from '../../types/messageBlocks';

interface TextBlockProps {
  block: TextBlockType;
}

export function TextBlock({ block }: TextBlockProps) {
  return (
    <div className="text-sm max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Ensure proper paragraph spacing
          p: ({ children }) => <p className="mb-2 leading-relaxed text-sm">{children}</p>,
          // Ensure headers have BETTER contrast - larger sizes
          h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-4">{children}</h1>,
          h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-3">{children}</h2>,
          h3: ({ children }) => <h3 className="text-base font-semibold mb-2 mt-2">{children}</h3>,
          // Ensure lists have proper spacing
          ul: ({ children }) => <ul className="mb-2 space-y-1 text-sm">{children}</ul>,
          ol: ({ children }) => <ol className="mb-2 space-y-1 text-sm">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed text-sm">{children}</li>,
          // Tables (GitHub Flavored Markdown)
          table: ({ children }) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full divide-y divide-border border border-border rounded-lg">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-muted/50">{children}</thead>,
          tbody: ({ children }) => <tbody className="bg-card divide-y divide-border">{children}</tbody>,
          tr: ({ children }) => <tr className="hover:bg-muted/30 transition-colors">{children}</tr>,
          th: ({ children }) => (
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-3 text-sm text-foreground whitespace-nowrap">
              {children}
            </td>
          ),
          // Code blocks
          code: ({ children, className }) => {
            const isInline = !className;
            return isInline ? (
              <code className="bg-muted px-1 py-0.5 rounded text-xs">{children}</code>
            ) : (
              <code className={`${className} text-xs`}>{children}</code>
            );
          },
          // Strong/bold text
          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
        }}
      >
        {block.content}
      </ReactMarkdown>
    </div>
  );
}
