import { ExternalLink } from 'lucide-react';
import type { NewsBlock as NewsBlockType } from '../../types/messageBlocks';

interface NewsBlockProps {
  block: NewsBlockType;
}

export function NewsBlock({ block }: NewsBlockProps) {
  return (
    <div className="space-y-3 overflow-hidden">
      {block.items.map((item, idx) => (
        <a
          key={idx}
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="block p-3 sm:p-4 bg-card border border-border rounded-lg hover:border-primary hover:shadow-md transition-all overflow-hidden"
        >
          <div className="flex items-start gap-3 w-full">
            <div className="flex-1 min-w-0 overflow-hidden">
              <h3 className="font-semibold text-sm sm:text-base text-foreground mb-1 flex items-start gap-2 break-words">
                <span className="flex-1 break-words">{item.title}</span>
                <ExternalLink className="w-3 h-3 sm:w-4 sm:h-4 text-muted-foreground flex-shrink-0 mt-0.5" />
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground mb-2 break-words line-clamp-3">{item.summary}</p>
              <div className="flex items-center gap-2 sm:gap-3 text-xs text-muted-foreground flex-wrap">
                {item.source && <span className="font-medium">{item.source}</span>}
                {item.date && <span>{item.date}</span>}
              </div>
            </div>
          </div>
        </a>
      ))}
    </div>
  );
}
