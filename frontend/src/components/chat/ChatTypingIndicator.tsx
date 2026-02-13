/**
 * ChatTypingIndicator - Animated loading indicator
 */

export function ChatTypingIndicator() {
  return (
    <div className="flex items-center gap-1 p-4">
      <div className="flex gap-1">
        <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground" />
      </div>
      <span className="ml-2 text-sm text-muted-foreground">
        Analyzing...
      </span>
    </div>
  );
}
