"""Standalone evaluation of the trained triage LoRA adapter: per-class
precision/recall/F1 and a confusion matrix on the held-out test split.

Run: python -m finetuning.evaluate
"""
from __future__ import annotations

import json
from pathlib import Path

import torch
from peft import PeftModel
from sklearn.metrics import classification_report, confusion_matrix
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from finetuning.prepare_dataset import LABELS
from finetuning.train_lora import BASE_MODEL, OUT_DIR


def load_model():
    tokenizer = AutoTokenizer.from_pretrained(OUT_DIR)
    base = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL, num_labels=len(LABELS)
    )
    model = PeftModel.from_pretrained(base, OUT_DIR)
    model.eval()
    return tokenizer, model


@torch.no_grad()
def predict_batch(tokenizer, model, texts: list[str]) -> list[int]:
    inputs = tokenizer(texts, truncation=True, padding=True, max_length=64, return_tensors="pt")
    logits = model(**inputs).logits
    return torch.argmax(logits, dim=-1).tolist()


def main():
    test_rows = [json.loads(l) for l in Path("finetuning/data/test.jsonl").read_text().splitlines() if l]
    label2id = {label: i for i, label in enumerate(LABELS)}

    tokenizer, model = load_model()

    texts = [r["text"] for r in test_rows]
    y_true = [label2id[r["label"]] for r in test_rows]
    y_pred = predict_batch(tokenizer, model, texts)

    print("Classification report (held-out test split, unseen sentence templates):\n")
    print(classification_report(y_true, y_pred, target_names=LABELS, zero_division=0))

    print("Confusion matrix (rows=true, cols=predicted):")
    print(LABELS)
    print(confusion_matrix(y_true, y_pred))


if __name__ == "__main__":
    main()
