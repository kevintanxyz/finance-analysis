/**
 * ChatMessageList - Scrollable list of chat messages
 */

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "./ChatMessage";
import { ChatTypingIndicator } from "./ChatTypingIndicator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "@/services/mcp-types";

interface ChatMessageListProps {
  messages: ChatMessageType[];
  isLoading?: boolean;
  streamingStatus?: string | null;
}

export function ChatMessageList({ messages, isLoading, streamingStatus }: ChatMessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive or status changes
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading, streamingStatus]);

  return (
    <ScrollArea className="flex-1 min-h-0 p-2 sm:p-4" ref={scrollRef}>
      <div className="space-y-4 max-w-full overflow-x-hidden">
        {messages.length === 0 && !isLoading && (
          <div className="flex h-full items-center justify-center text-center">
            <div className="max-w-md space-y-2">
              <h3 className="text-lg font-semibold">Welcome to WealthPoint</h3>
              <p className="text-sm text-muted-foreground">
                Start by uploading a portfolio PDF or asking a question about your investments.
              </p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {/* Show streaming status when tools are being called */}
        {streamingStatus && (
          <div className="flex w-full gap-3 mb-4 justify-start">
            {/* Avatar (left side for assistant) */}
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-primary">
                <Bot className="h-4 w-4 text-primary-foreground" />
              </AvatarFallback>
            </Avatar>

            {/* Status message */}
            <div className="flex items-center gap-2 px-3 py-2 bg-muted/50 border border-border rounded-lg text-sm text-muted-foreground animate-pulse">
              {streamingStatus}
            </div>
          </div>
        )}

        {isLoading && <ChatTypingIndicator />}
      </div>
    </ScrollArea>
  );
}
