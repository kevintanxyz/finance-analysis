/**
 * ChatContainer - Main chat layout
 * Combines message list and input
 */

import { Card } from "@/components/ui/card";
import { ChatMessageList } from "./ChatMessageList";
import { ChatInput } from "./ChatInput";
import type { ChatMessage } from "@/services/mcp-types";

interface ChatContainerProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  streamingStatus?: string | null;
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatContainer({
  messages,
  isLoading = false,
  streamingStatus,
  onSendMessage,
  disabled = false,
  placeholder,
}: ChatContainerProps) {
  return (
    <Card className="flex h-[calc(100vh-120px)] max-h-[calc(100vh-120px)] flex-col overflow-hidden">
      <ChatMessageList messages={messages} isLoading={isLoading} streamingStatus={streamingStatus} />
      <ChatInput
        onSend={onSendMessage}
        disabled={disabled || isLoading}
        placeholder={placeholder}
      />
    </Card>
  );
}
