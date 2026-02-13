/**
 * ChatMessage - Message bubble component
 * Displays user or assistant messages with tool results
 */

import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { User, Bot } from "lucide-react";
import { ChatToolResult } from "./ChatToolResult";
import { MessageRenderer } from "@/components/MessageBlocks";
import type { ChatMessage as ChatMessageType } from "@/services/mcp-types";

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  // Don't render empty assistant messages (they'll show via streaming status instead)
  if (!isUser && !message.content.trim()) {
    return null;
  }

  return (
    <div
      className={cn(
        "flex w-full gap-3 mb-4",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      {/* Avatar (left side for assistant, hidden for user) */}
      {!isUser && (
        <Avatar className="h-8 w-8">
          <AvatarFallback className="bg-primary">
            <Bot className="h-4 w-4 text-primary-foreground" />
          </AvatarFallback>
        </Avatar>
      )}

      {/* Message content */}
      <div className={cn(
        "flex flex-col gap-2",
        isUser ? "items-end max-w-[85%] sm:max-w-[75%] md:max-w-[65%]" : "items-start max-w-[98%] sm:max-w-[96%] md:max-w-[94%]"
      )}>
        {/* Message bubble */}
        <Card
          className={cn(
            "p-3",
            isUser
              ? "bg-primary text-primary-foreground overflow-hidden"
              : "bg-muted w-full overflow-x-auto overflow-y-hidden",
          )}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <MessageRenderer content={message.content} />
          )}
        </Card>

        {/* Tool results (only for assistant messages) */}
        {!isUser && message.toolResults && message.toolResults.length > 0 && (
          <div className="w-full space-y-2">
            {message.toolResults.map((result, idx) => (
              <div key={idx}>
                <p className="text-xs text-muted-foreground mb-1">
                  Tool: {result.toolName}
                </p>
                <ChatToolResult result={result} />
              </div>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <span className="text-xs text-muted-foreground">
          {message.timestamp.toLocaleTimeString("fr-FR", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      {/* Avatar (right side for user) */}
      {isUser && (
        <Avatar className="h-8 w-8">
          <AvatarFallback className="bg-secondary">
            <User className="h-4 w-4 text-secondary-foreground" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}
