"""Loads the real trained LoRA adapter (local checkpoint, no network) and
checks a couple of unambiguous cases. The full precision/recall/F1 report
lives in finetuning/evaluate.py -- this is just a smoke test that the
committed artifact still loads and behaves sanely."""
from app.triage_classifier import get_triage_classifier


def test_clear_emergency_case_classified_as_emergency():
    clf = get_triage_classifier("finetuning/artifacts/triage-lora", "distilbert-base-uncased")
    result = clf.classify("crushing chest pain radiating to my left arm and I can't breathe")
    assert result.label == "emergency"
    assert result.confidence > 0.5


def test_clear_self_care_case_not_classified_as_emergency():
    clf = get_triage_classifier("finetuning/artifacts/triage-lora", "distilbert-base-uncased")
    result = clf.classify("a mild runny nose and slight sore throat, feels like a common cold")
    assert result.label != "emergency"
