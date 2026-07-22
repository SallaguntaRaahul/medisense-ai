import { Stethoscope } from "lucide-react";

const EXAMPLE_PROMPTS = [
  "What are common symptoms of type 2 diabetes?",
  "What triggers migraines?",
  "How is seasonal allergy different from a cold?",
  "What should I do about a mild sunburn?",
];

export function EmptyState({ onSelectPrompt }: { onSelectPrompt: (prompt: string) => void }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 px-4 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
        <Stethoscope className="h-7 w-7 text-primary" />
      </div>
      <div className="space-y-1.5">
        <h2 className="text-lg font-semibold">Ask MediSense a health question</h2>
        <p className="max-w-sm text-sm text-muted-foreground">
          General health information grounded in MedlinePlus, with a triage
          check and source citations on every answer.
        </p>
      </div>
      <div className="flex max-w-xl flex-wrap justify-center gap-2">
        {EXAMPLE_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            onClick={() => onSelectPrompt(prompt)}
            className="rounded-full border bg-card px-3.5 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
