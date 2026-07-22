"use client";

import { useRef, type KeyboardEvent } from "react";
import { ArrowUp } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export function ChatInput({ value, onChange, onSubmit, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    onChange(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) onSubmit();
    }
  }

  return (
    <div className="flex items-end gap-2 border-t bg-background p-3">
      <Textarea
        ref={textareaRef}
        value={value}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        placeholder="Describe your symptom or ask a health question..."
        rows={1}
        disabled={disabled}
        className="max-h-40 min-h-10 flex-1 resize-none rounded-xl"
      />
      <Button
        size="icon"
        className="h-10 w-10 shrink-0 rounded-xl"
        disabled={disabled || !value.trim()}
        onClick={onSubmit}
      >
        <ArrowUp className="h-4 w-4" />
      </Button>
    </div>
  );
}
