import { Stethoscope, User } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { TriageBanner } from "@/components/chat/triage-banner";
import { SourceCitations } from "@/components/chat/source-citations";
import { MarkdownAnswer } from "@/components/chat/markdown-answer";
import type { ChatMessage } from "@/lib/types";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <Avatar className="h-8 w-8 shrink-0 mt-0.5">
        <AvatarFallback className={isUser ? "bg-secondary" : "bg-primary text-primary-foreground"}>
          {isUser ? <User className="h-4 w-4" /> : <Stethoscope className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      <div className={`flex max-w-[85%] flex-col gap-2 sm:max-w-[75%] ${isUser ? "items-end" : "items-start"}`}>
        {!isUser && message.triage && <TriageBanner triage={message.triage} />}

        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm whitespace-pre-wrap"
              : "bg-card border rounded-tl-sm"
          }`}
        >
          {isUser ? message.content : <MarkdownAnswer content={message.content} />}
        </div>

        {!isUser && message.sources && <SourceCitations sources={message.sources} />}
      </div>
    </div>
  );
}
