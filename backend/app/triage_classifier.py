"""Loads the LoRA-finetuned triage classifier (see finetuning/train_lora.py)
and exposes a single `classify` call used by the LangGraph `classify_triage` node.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer


@dataclass
class TriageResult:
    label: str
    confidence: float


class TriageClassifier:
    def __init__(self, adapter_path: str, base_model: str):
        label_map = json.loads(Path(adapter_path, "label_map.json").read_text())
        self.id2label = {int(k): v for k, v in label_map["id2label"].items()}

        self.tokenizer = AutoTokenizer.from_pretrained(adapter_path)
        base = AutoModelForSequenceClassification.from_pretrained(
            base_model, num_labels=len(self.id2label)
        )
        self.model = PeftModel.from_pretrained(base, adapter_path)
        self.model.eval()

    @torch.no_grad()
    def classify(self, text: str) -> TriageResult:
        inputs = self.tokenizer(text, truncation=True, padding=True, max_length=64, return_tensors="pt")
        logits = self.model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]
        idx = int(torch.argmax(probs).item())
        return TriageResult(label=self.id2label[idx], confidence=float(probs[idx].item()))


@lru_cache
def get_triage_classifier(adapter_path: str, base_model: str) -> TriageClassifier:
    return TriageClassifier(adapter_path, base_model)
