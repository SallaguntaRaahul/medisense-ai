"""Builds a synthetic symptom-urgency triage dataset (4 classes).

This is a template-generated demo dataset, NOT a clinically validated
triage tool -- it exists to give the finetuning step a real, concrete task
(classify a described symptom into emergency / urgent / routine / self_care)
with a genuine train/test split. Train and test draw from disjoint sentence
templates so held-out accuracy reflects generalization to unseen phrasing,
not memorization.

Labels:
  emergency  - call emergency services / go to ER right now
  urgent     - see a clinician same-day / within hours
  routine    - schedule a regular appointment, not time-critical
  self_care  - manageable at home with OTC measures
"""
from __future__ import annotations

import json
import random
from pathlib import Path

random.seed(42)

LABELS = ["emergency", "urgent", "routine", "self_care"]

SYMPTOMS = {
    "emergency": [
        "crushing chest pain radiating to my left arm",
        "sudden difficulty breathing and I'm gasping for air",
        "one side of my face is drooping and my speech is slurred",
        "I'm bleeding heavily and it won't stop after ten minutes",
        "I passed out and just regained consciousness confused",
        "my lips and throat are swelling up and I can barely swallow after eating peanuts",
        "the worst headache of my life that came on all of a sudden",
        "a sudden severe headache along with confusion and blurred vision",
        "a headache that started after hitting my head hard and I feel drowsy",
        "I'm vomiting blood",
        "I have thoughts of ending my life right now",
        "my child swallowed a bottle of pills",
        "severe abdominal pain and I can't stand up straight",
        "I think I'm having a heart attack",
        "sudden weakness on one side of my body",
        "I was in a car accident and my leg looks deformed",
        "a seizure that has lasted more than five minutes",
    ],
    "urgent": [
        "a fever of 103 that has lasted three days",
        "I twisted my ankle and it's swelling fast, maybe broken",
        "persistent vomiting and diarrhea and I feel very dehydrated",
        "a deep cut on my hand that probably needs stitches",
        "an eye injury after something splashed into it",
        "a dog bit me and broke the skin",
        "worsening pain from what I think is a kidney stone",
        "a rash that's spreading fast with a fever",
        "I ran out of my insulin and my blood sugar readings are very high",
        "my asthma inhaler isn't helping and I'm still wheezing",
        "a urinary tract infection with fever and back pain",
        "chest tightness that started after exercise but isn't severe",
        "sudden severe ear pain with hearing loss",
    ],
    "routine": [
        "mild joint stiffness in the mornings for the past few weeks",
        "I'd like to schedule my annual checkup",
        "a small skin rash that isn't spreading or itching much",
        "occasional mild acid reflux after meals",
        "I want to discuss adjusting my blood pressure medication",
        "recurring mild headaches a couple times a month",
        "migraines with light sensitivity that happen every few weeks and respond to my usual medication",
        "a throbbing headache with nausea and light sensitivity that I get occasionally",
        "a bad headache and I am sensitive to light, but I get this every month before my period",
        "a bad headache with sensitivity to light that lines up with my usual migraine pattern",
        "a mole I'd like a doctor to take a look at eventually",
        "ongoing lower back stiffness after sitting all day",
        "I'd like a referral for a routine eye exam",
        "mild seasonal allergies that come back every spring",
        "I want to ask about starting a new exercise routine safely",
        "follow-up on my cholesterol test results from last month",
    ],
    "self_care": [
        "a runny nose and mild sore throat, feels like a common cold",
        "a small paper cut on my finger",
        "mild muscle soreness after a workout yesterday",
        "a slight headache after a long day at the computer",
        "a headache with mild light sensitivity that gets better after resting in a dark room",
        "a bad headache and I am sensitive to light, but resting in a quiet dark room usually helps",
        "a bad headache with sensitivity to light after a stressful day, nothing like before",
        "a minor sunburn on my shoulders",
        "occasional mild heartburn after spicy food",
        "a little bit of dry, itchy skin in winter",
        "mild hiccups that started an hour ago",
        "a stuffy nose from seasonal pollen",
        "slight fatigue after a poor night's sleep",
        "a small bruise from bumping into a table",
        "mild constipation after traveling",
    ],
}

TEMPLATES_TRAIN = [
    "I have {s}.",
    "I'm dealing with {s}.",
    "I've been experiencing {s}.",
    "For the past hour I've had {s}.",
    "My symptom is {s}.",
    "Lately I've noticed {s}.",
    "I woke up with {s}.",
    "Right now I have {s}.",
]

TEMPLATES_TEST = [
    "Is it serious that I have {s}?",
    "What should I do about {s}?",
    "I'm worried because I have {s}.",
    "Should I see someone about {s}?",
    "Just started having {s}, any advice?",
]


def _generate(templates: list[str]) -> list[dict]:
    rows = []
    for label, phrases in SYMPTOMS.items():
        for phrase in phrases:
            for template in templates:
                rows.append({"text": template.format(s=phrase), "label": label})
    random.shuffle(rows)
    return rows


def build_dataset(out_dir: str = "finetuning/data") -> tuple[list[dict], list[dict]]:
    train_rows = _generate(TEMPLATES_TRAIN)
    test_rows = _generate(TEMPLATES_TEST)

    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "train.jsonl").write_text("\n".join(json.dumps(r) for r in train_rows))
    (path / "test.jsonl").write_text("\n".join(json.dumps(r) for r in test_rows))
    return train_rows, test_rows


if __name__ == "__main__":
    train_rows, test_rows = build_dataset()
    print(f"train examples: {len(train_rows)}")
    print(f"test examples: {len(test_rows)}")
    for label in LABELS:
        n_train = sum(1 for r in train_rows if r["label"] == label)
        n_test = sum(1 for r in test_rows if r["label"] == label)
        print(f"  {label}: train={n_train} test={n_test}")
