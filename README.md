# MediSense AI

A medical information chatbot I built to cover a full applied-AI stack in
one project: RAG, an LLM orchestrated with LangGraph, a LoRA-finetuned
classifier alongside the LLM (not just another prompt), tests, an eval
harness that hits the real model, medical-safety guardrails, and a proper
split frontend/backend deploy instead of one server rendering everything.

Quick disclaimer up front since the domain calls for it: **this is a
portfolio project, not a real clinical tool.** It won't give you a
diagnosis or a drug dosage, and every answer carries a line pointing you to
an actual clinician or emergency services. More on that at the bottom.

## Why LangGraph

My last RAG project, [ragsentry](https://github.com/SallaguntaRaahul/ragsentry),
hand-rolled the whole agent loop as one function with a bunch of ifs inside
it. This time I wanted the request flow to actually be a graph, with a
branch that means something:

```
classify_triage ──conditional──▶ emergency_shortcut ──▶ output_guardrail ──▶ END
                 \─────────────▶ retrieve ──▶ generate ──▶ output_guardrail ──▶ END
```

If the triage classifier comes back "emergency" with decent confidence, the
graph skips retrieval and generation completely and returns a fixed safe
response — the LLM never even sees that input. That's a real branch in
`app/graph.py`, not an if-statement buried three levels deep in a handler
where nobody will notice it during a review.

## How it's put together

```
Next.js frontend (Vercel)                     FastAPI backend (Render)
  chat UI, triage banner,                       │
  citation chips                    ┌───────────┴───────────┐
        │                           │                       │
  app/api/chat/route.ts   ──────▶  LangGraph pipeline (app/graph.py)
  (proxies to the backend           │
   so the API key stays    classify_triage ──▶ retrieve ──▶ generate ──▶ output_guardrail
   server-side)              (LoRA        (FAISS +      (ChatGroq +   (dosage/diagnosis
                              classifier)   fastembed)    LangChain)    rewrite + disclaimer)
```

The knowledge base is MedlinePlus health-topic summaries, pulled through
their public webservices API (`app/ingestion.py`). I picked that over one
of the usual medical QA datasets on purpose — a lot of them strip the
actual answer text for anything that isn't a US-government source, for
copyright reasons, and I didn't want to deal with that. MedlinePlus content
is a government work, so it's public domain and the licensing question just
doesn't come up.

## The finetuning part, and a bug I ran into

`finetuning/train_lora.py` LoRA-finetunes `distilbert-base-uncased` into a
4-way symptom-urgency classifier — emergency, urgent, routine, or
self-care. The dataset is synthetic and template-generated (there isn't a
ready-made public dataset for this that I trusted), but the train and test
splits are built from different sentence templates on purpose, so the
accuracy number actually reflects generalizing to new phrasing rather than
the model just memorizing my templates.

```bash
python -m finetuning.prepare_dataset
python -m finetuning.train_lora        # ~70-85s on CPU
python -m finetuning.evaluate          # precision/recall/F1, confusion matrix
```

It lands at 97.4% on the held-out set, and looking at the confusion matrix,
every mistake it makes is in the cautious direction — no true emergency
case ever gets predicted as routine or self-care. Given what this
classifier gates, that's the direction you want the errors to fall in.

Here's the bug, because I think it's more interesting than the accuracy
number: partway through training runs, I typed in "I have a bad headache
and I am sensitive to light, what could this be?" — a pretty textbook
migraine — and the classifier called it an emergency. Turned out my
training data only had headaches described that way ("sudden," "severe,"
"with confusion") under the emergency label, and nothing under any other
label used the words "headache" or "light sensitivity" at all, so the
model just learned that combination of words meant the worst category. I
added a handful of examples using that exact same wording under routine and
self-care, which helped — that specific query's emergency confidence
dropped from 0.97 to 0.84 — but it still crosses the emergency threshold on
that exact phrasing with zero context about how long it's been happening.
I decided that's a limitation worth writing down rather than a bug worth
chasing further: a headache described with no history at all, in a system
that has to guess, erring toward "go get this checked" isn't unreasonable.
Give it the same symptom with "this happens every month before my period"
attached and it correctly comes back routine.

## Security

API key + per-IP rate limiting on `/api/chat`. Retrieved content gets
scanned for prompt-injection patterns and wrapped with an explicit "this is
data, not instructions" fence before it goes anywhere near the LLM prompt —
same approach I used in ragsentry. On top of that there are guardrails
specific to this being a medical bot: a regex pass that catches and
rewrites definitive-diagnosis language ("you have diabetes") and specific
drug dosages ("500mg every 6 hours"), and the disclaimer gets appended to
every response no matter what the model said, not just the ones that look
risky. Combined with the emergency short-circuit, genuinely dangerous input
never even reaches the generation step. CORS is locked to the deployed
frontend origin, and the backend's API key only ever lives in the Next.js
server route — it's never in anything that ships to the browser. Chat
history goes into SQLite for demo continuity, no real patient data
involved, obviously.

## Tests vs. evals

pytest (44 tests, all offline, LLM calls mocked) is checking the code:
guardrail regex behavior, rate-limit math, the XML parsing in ingestion,
both branches of the LangGraph routing, auth. Writing these actually caught
two real bugs in the guardrail regex — one where the character class for
matching a diagnosis pattern didn't allow digits, so it missed "type 2
diabetes" entirely, and a second where the pattern required filler words
between "have" and the disease name, so "you have diabetes for sure" sailed
through unrewritten.

`evals/run_evals.py` is a different thing — it checks the whole system,
real Groq calls and the actual trained classifier, against an 11-case
dataset: does the answer actually use the retrieved facts, does it avoid
leaking a dosage or diagnosis, does it route chest pain and stroke symptoms
and self-harm language to the emergency response, does a prompt injection
smuggled into a retrieved chunk get caught and ignored. It's at 11/11 right
now.

```bash
pytest                    # backend/, fully offline
python -m evals.run_evals # backend/, needs a real GROQ_API_KEY
```

## Running it locally

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GROQ_API_KEY, free tier at console.groq.com/keys
pytest
uvicorn app.main:app --reload   # http://localhost:8000

# Frontend, separate terminal
cd frontend
npm install
cp .env.example .env.local   # MEDISENSE_BACKEND_URL + MEDISENSE_API_KEY (match backend's APP_API_KEY)
npm run dev                  # http://localhost:3000
```

## API

- `POST /api/chat` `{message, session_id?}` — runs the LangGraph pipeline, rate-limited per IP
- `GET /api/chat/{session_id}/history`
- `GET /health`

## Deploying

Backend on Render (Docker), frontend on Vercel.

1. Push to GitHub.
2. Render → New → Blueprint, connect the repo. `render.yaml` at the root
   points it at `backend/`. Set `GROQ_API_KEY`, `APP_API_KEY`, and
   `CORS_ORIGINS` in the dashboard.
3. Vercel → New Project, import the repo, root directory `frontend`. Set
   `MEDISENSE_BACKEND_URL` (the Render URL) and `MEDISENSE_API_KEY`
   (matching `APP_API_KEY`).

One thing worth flagging honestly: the backend image ships with torch and
transformers for the triage classifier, which is a real chunk of RAM
against Render's free 512MB limit. If it starts OOMing under any real
load, bumping to their paid Starter tier is the straightforward fix.

## Stack

Python, FastAPI, LangChain, LangGraph, Groq, FAISS, fastembed, Hugging Face
transformers + peft for the LoRA finetuning, scikit-learn, pytest, Docker,
Next.js 16, React 19, Tailwind v4, shadcn/ui, deployed on Render and
Vercel.

## Disclaimer

MediSense AI is a demo project, not a licensed medical device. It doesn't
provide medical advice and shouldn't be used for real clinical decisions.
If you're having a medical emergency, call your local emergency number.
