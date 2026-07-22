"""LoRA finetune of a small encoder (distilbert-base-uncased) for 4-class
symptom-urgency triage classification. CPU/MPS-feasible: ~416 train examples,
a handful of epochs, minutes not hours.

Run: python -m finetuning.train_lora
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

from finetuning.prepare_dataset import LABELS, build_dataset

BASE_MODEL = "distilbert-base-uncased"
OUT_DIR = "finetuning/artifacts/triage-lora"
LABEL2ID = {label: i for i, label in enumerate(LABELS)}
ID2LABEL = {i: label for label, i in LABEL2ID.items()}


def _load_or_build_rows():
    train_path = Path("finetuning/data/train.jsonl")
    test_path = Path("finetuning/data/test.jsonl")
    if train_path.exists() and test_path.exists():
        train_rows = [json.loads(l) for l in train_path.read_text().splitlines() if l]
        test_rows = [json.loads(l) for l in test_path.read_text().splitlines() if l]
    else:
        train_rows, test_rows = build_dataset()
    return train_rows, test_rows


def _to_hf_dataset(rows: list[dict], tokenizer) -> Dataset:
    ds = Dataset.from_list([{"text": r["text"], "label": LABEL2ID[r["label"]]} for r in rows])
    return ds.map(lambda ex: tokenizer(ex["text"], truncation=True, padding="max_length", max_length=64), batched=True)


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="macro", zero_division=0)
    return {"accuracy": accuracy_score(labels, preds), "precision": precision, "recall": recall, "f1": f1}


def main():
    train_rows, test_rows = _load_or_build_rows()

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    train_ds = _to_hf_dataset(train_rows, tokenizer)
    test_ds = _to_hf_dataset(test_rows, tokenizer)

    base_model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL, num_labels=len(LABELS), id2label=ID2LABEL, label2id=LABEL2ID
    )

    lora_config = LoraConfig(
        task_type=TaskType.SEQ_CLS,
        r=8,
        lora_alpha=16,
        lora_dropout=0.1,
        target_modules=["q_lin", "v_lin"],
    )
    model = get_peft_model(base_model, lora_config)
    model.print_trainable_parameters()

    args = TrainingArguments(
        output_dir="finetuning/checkpoints",
        num_train_epochs=6,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        learning_rate=2e-4,
        eval_strategy="epoch",
        save_strategy="no",
        logging_steps=10,
        report_to=[],
        use_cpu=not torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=test_ds,
        compute_metrics=compute_metrics,
    )
    trainer.train()

    final_metrics = trainer.evaluate()
    print("Final held-out metrics:", final_metrics)

    Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(OUT_DIR)
    tokenizer.save_pretrained(OUT_DIR)
    Path(OUT_DIR, "label_map.json").write_text(json.dumps({"id2label": ID2LABEL, "label2id": LABEL2ID}))
    print(f"Saved LoRA adapter to {OUT_DIR}")


if __name__ == "__main__":
    main()
