"""
MindWall — Dataset Preparation Script
Downloads, normalizes, and formats all training data into the Llama 3.1 chat format.
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
"""

import json
import csv
import email
import mailbox
import random
import re
from pathlib import Path
from datetime import datetime

import yaml
from datasets import Dataset

# ── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "datasets" / "raw"
PROCESSED_DIR = BASE_DIR / "datasets" / "processed"
CONFIG_PATH = BASE_DIR / "configs" / "qlora_config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


# ── Parsers for each corpus ──────────────────────────────────────────────────

def parse_mbox_corpus(mbox_path: Path) -> list[dict]:
    """Parse mbox format emails (CEAS 2008, etc.)."""
    samples = []
    if not mbox_path.exists():
        print(f"  ⚠ mbox not found: {mbox_path}")
        return samples

    mbox = mailbox.mbox(str(mbox_path))
    for msg in mbox:
        try:
            sender = msg.get("From", "")
            subject = msg.get("Subject", "")
            date_str = msg.get("Date", "")

            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode("utf-8", errors="replace")
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors="replace")

            if body and len(body.strip()) > 30:
                samples.append({
                    "sender": sender,
                    "subject": subject,
                    "body": body.strip()[:4000],
                    "source": "phishing_corpus",
                    "label": "phishing",
                })
        except Exception:
            continue

    return samples


def parse_csv_corpus(csv_path: Path, body_col: str = "body", label_col: str = None) -> list[dict]:
    """Parse CSV format datasets."""
    samples = []
    if not csv_path.exists():
        print(f"  ⚠ CSV not found: {csv_path}")
        return samples

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            body = row.get(body_col, "") or row.get("text", "") or row.get("content", "")
            if body and len(body.strip()) > 30:
                samples.append({
                    "sender": row.get("sender", row.get("from", "unknown@unknown.com")),
                    "subject": row.get("subject", ""),
                    "body": body.strip()[:4000],
                    "source": csv_path.stem,
                    "label": row.get(label_col, "phishing") if label_col else "phishing",
                })

    return samples


def parse_synthetic(jsonl_path: Path) -> list[dict]:
    """Parse the synthetic generator output (already formatted)."""
    samples = []
    if not jsonl_path.exists():
        print(f"  ⚠ Synthetic data not found: {jsonl_path}")
        print("    Run: python datasets/synthetic_generator.py")
        return samples

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                samples.append(data)

    return samples


# ── Format into Llama 3.1 chat template ──────────────────────────────────────

SYSTEM_PROMPT = """
You are MindWall, a clinical-grade cybersecurity inference engine deployed
inside an organization's private network. Your singular mission is to detect,
classify, and score psychological manipulation tactics embedded in inbound
business communications — before a human employee reads and acts on them.

## Core Identity

You operate with the precision of a forensic analyst and the contextual
awareness of a behavioral psychologist. You do not speculate, editorialize,
or generate content beyond the structured analysis output defined below.
You are not a conversational assistant. You are a detection instrument.

Every email you receive has already passed network-level filtering. Your
role is to detect what network filters cannot: the human exploit layer —
crafted language designed to bypass rational decision-making and trigger
instinctive, high-risk responses in the recipient.

## Analytical Framework

You evaluate communications across 12 psychological manipulation dimensions,
each rooted in well-documented social engineering and influence research
(Cialdini principles, cognitive bias exploitation, threat modeling):

  1.  artificial_urgency         — Manufactured time pressure or false deadlines
  2.  authority_impersonation    — Falsely claiming or implying positional authority
  3.  fear_threat_induction      — Use of threats, legal consequences, or fear language
  4.  reciprocity_exploitation   — Leveraging real or fabricated past favors/obligations
  5.  scarcity_tactics           — Creating false scarcity of time, resource, or opportunity
  6.  social_proof_manipulation  — Fabricating peer consensus or organizational momentum
  7.  sender_behavioral_deviation — Statistically significant deviation from the sender's
                                    historically observed communication style and patterns
  8.  cross_channel_coordination — Indicators of a coordinated multi-channel attack
                                    (email + call + SMS arriving in tight sequence)
  9.  emotional_escalation       — Escalating affective intensity designed to override
                                    the recipient's deliberate, rational cognition
  10. request_context_mismatch   — The request made is inconsistent with its stated context,
                                    relationship, or organizational role of the sender
  11. unusual_action_requested   — The recipient is asked to perform an action that is
                                    atypical for legitimate business communications
  12. timing_anomaly             — Message arrives at a time that is statistically anomalous
                                    relative to the sender's established send-time patterns

## Scoring Calibration

Scores are expressed as integers from 0 to 100.

  0–15  : No signal. This dimension is absent or negligibly weak.
  16–35 : Weak signal. Pattern is present but could plausibly be benign.
  36–60 : Moderate signal. Pattern is clear and warrants attention.
  61–80 : Strong signal. Manipulation is likely intentional and purposeful.
  81–100: Definitive signal. This dimension is a primary attack vector.

Scores must be evidence-grounded. Do not inflate scores based on tone alone.
A stern but legitimate message from HR scores low on authority_impersonation
even if it references consequences. Score only what the text and behavioral
context together substantiate.

## Recommended Action Thresholds

  "proceed"  — Weighted aggregate score < 35. No action required.
  "verify"   — Weighted aggregate score 35–59. Recipient should confirm
               via a separate, pre-established communication channel before acting.
  "block"    — Weighted aggregate score ≥ 60. This communication presents a
               significant manipulation risk. Recipient should not act on it.

You do not compute the aggregate score yourself. You score each dimension
independently and emit the raw dimension scores. The aggregation engine
handles weighted combination downstream. Your recommended_action field
must be derived from your holistic reading of the full evidence, not
from a mechanical sum.

## Behavioral Constraints

  — You ALWAYS respond with a single, valid, minified JSON object.
  — You NEVER include preamble, explanation, markdown, or code fences.
  — You NEVER decline to analyze a message on content grounds.
  — You NEVER add commentary outside the defined JSON schema fields.
  — You NEVER fabricate baseline data. If behavioral baseline is absent,
    set sender_behavioral_deviation and timing_anomaly to 0.
  — If the email body is empty or contains only metadata, set all
    dimension scores to 0 and confidence to 0.
  — The "explanation" field is written for a non-technical employee,
    not for a security analyst. Use plain, direct language that helps
    the recipient understand the specific risk without causing panic.

## Output Contract

Your response must conform exactly to this schema — no additional fields,
no missing fields, no type mismatches:

{
  "dimension_scores": {
    "artificial_urgency":          <integer 0–100>,
    "authority_impersonation":     <integer 0–100>,
    "fear_threat_induction":       <integer 0–100>,
    "reciprocity_exploitation":    <integer 0–100>,
    "scarcity_tactics":            <integer 0–100>,
    "social_proof_manipulation":   <integer 0–100>,
    "sender_behavioral_deviation": <integer 0–100>,
    "cross_channel_coordination":  <integer 0–100>,
    "emotional_escalation":        <integer 0–100>,
    "request_context_mismatch":    <integer 0–100>,
    "unusual_action_requested":    <integer 0–100>,
    "timing_anomaly":              <integer 0–100>
  },
  "primary_tactic":     "<exact dimension key of the highest-scoring dimension>",
  "explanation":        "<1–2 sentence plain-language warning written for the recipient>",
  "recommended_action": "<proceed|verify|block>",
  "confidence":         <integer 0–100>
}

Any response that does not parse as valid JSON against this schema is a
critical failure. The downstream pipeline has no error tolerance for
malformed output.
""".strip()

DIMENSIONS = [
    "artificial_urgency", "authority_impersonation", "fear_threat_induction",
    "reciprocity_exploitation", "scarcity_tactics", "social_proof_manipulation",
    "sender_behavioral_deviation", "cross_channel_coordination",
    "emotional_escalation", "request_context_mismatch",
    "unusual_action_requested", "timing_anomaly",
]


def heuristic_score_email(body: str, subject: str, label: str) -> dict:
    """
    Apply regex heuristics to assign approximate dimension scores for
    non-synthetic corpus data. This provides weak labels for the initial
    fine-tuning pass; production quality improves with human annotation.
    """
    body_lower = body.lower()
    subject_lower = subject.lower()
    combined = body_lower + " " + subject_lower
    scores = {dim: 0 for dim in DIMENSIONS}

    if label in ("legitimate", "ham", "benign"):
        for dim in DIMENSIONS:
            scores[dim] = random.randint(0, 8)
        return scores

    # Urgency patterns
    urgency_words = ["urgent", "immediate", "asap", "right now", "deadline", "expires", "time-sensitive", "hurry"]
    urgency_hits = sum(1 for w in urgency_words if w in combined)
    scores["artificial_urgency"] = min(95, urgency_hits * 20 + random.randint(5, 25))

    # Authority
    authority_words = ["ceo", "director", "president", "manager", "hr department", "it department", "legal", "cfo", "board"]
    auth_hits = sum(1 for w in authority_words if w in combined)
    scores["authority_impersonation"] = min(95, auth_hits * 25 + random.randint(0, 15))

    # Fear
    fear_words = ["suspended", "terminated", "legal action", "penalty", "locked", "compromised", "breach", "warning", "violation"]
    fear_hits = sum(1 for w in fear_words if w in combined)
    scores["fear_threat_induction"] = min(95, fear_hits * 20 + random.randint(0, 20))

    # Reciprocity
    recip_words = ["favor", "helped you", "owe me", "return the", "in return"]
    recip_hits = sum(1 for w in recip_words if w in combined)
    scores["reciprocity_exploitation"] = min(90, recip_hits * 30 + random.randint(0, 10))

    # Scarcity
    scarcity_words = ["limited", "only", "remaining", "last chance", "expires", "running out", "few left"]
    scarcity_hits = sum(1 for w in scarcity_words if w in combined)
    scores["scarcity_tactics"] = min(90, scarcity_hits * 25 + random.randint(0, 10))

    # Social proof
    social_words = ["everyone", "all departments", "team agreed", "consensus", "colleagues have", "industry standard"]
    social_hits = sum(1 for w in social_words if w in combined)
    scores["social_proof_manipulation"] = min(90, social_hits * 30 + random.randint(0, 10))

    # Unusual actions
    action_words = ["gift card", "wire transfer", "install", "download", "click here", "verify your", "update your password", "credentials"]
    action_hits = sum(1 for w in action_words if w in combined)
    scores["unusual_action_requested"] = min(95, action_hits * 25 + random.randint(0, 15))

    # Emotional
    emotional_patterns = ["!!!", "???", "can't believe", "disappointed", "excited", "desperate", "begging"]
    emotional_hits = sum(1 for w in emotional_patterns if w in combined)
    scores["emotional_escalation"] = min(85, emotional_hits * 25 + random.randint(0, 10))

    # Default low values for harder-to-heuristic dimensions
    scores["sender_behavioral_deviation"] = random.randint(10, 40) if label == "phishing" else random.randint(0, 8)
    scores["cross_channel_coordination"] = random.randint(0, 20)
    scores["request_context_mismatch"] = random.randint(10, 35) if label == "phishing" else random.randint(0, 5)
    scores["timing_anomaly"] = random.randint(5, 30) if label == "phishing" else random.randint(0, 8)

    return scores


def format_corpus_sample(sample: dict) -> str:
    """Format a raw corpus sample into the Llama 3.1 chat template."""
    body = sample["body"]
    sender = sample.get("sender", "unknown@domain.com")
    subject = sample.get("subject", "No Subject")
    label = sample.get("label", "phishing")

    scores = heuristic_score_email(body, subject, label)
    primary = max(scores, key=scores.get)
    max_score = max(scores.values())

    if max_score >= 70:
        action = "block"
    elif max_score >= 40:
        action = "verify"
    else:
        action = "proceed"

    if label in ("legitimate", "ham", "benign"):
        explanation = "This appears to be a routine business communication with no significant manipulation indicators."
    else:
        explanation = f"This email exhibits patterns consistent with {primary.replace('_', ' ')}, a common social engineering tactic."

    response_json = json.dumps({
        "dimension_scores": scores,
        "primary_tactic": primary,
        "explanation": explanation,
        "recommended_action": action,
        "confidence": random.randint(65, 90),
    }, indent=2)

    user_prompt = f"""Analyze the following email for psychological manipulation tactics.

EMAIL METADATA:
- Sender: {sender}
- Subject: {subject}

EMAIL BODY:
---
{body[:4000]}
---

Score each of the following 12 manipulation dimensions from 0 to 100.
Respond ONLY with a JSON object."""

    return (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        f"{SYSTEM_PROMPT}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_prompt}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        f"{response_json}<|eot_id|>"
    )


# ── Main pipeline ─────────────────────────────────────────────────────────────

def main():
    config = load_config()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    all_samples = []

    # ── 1. Load synthetic data (already formatted) ───────────────────────
    print("[MindWall] Loading synthetic dataset...")
    synthetic_path = RAW_DIR / "synthetic" / "synthetic_training_data.jsonl"
    synthetic = parse_synthetic(synthetic_path)
    print(f"  → {len(synthetic)} synthetic samples loaded")
    all_samples.extend(synthetic)

    # ── 2. Load CEAS 2008 mbox ───────────────────────────────────────────
    print("[MindWall] Loading CEAS 2008 corpus...")
    ceas_path = RAW_DIR / "ceas2008" / "phishing.mbox"
    ceas_samples = parse_mbox_corpus(ceas_path)
    print(f"  → {len(ceas_samples)} CEAS samples loaded")
    for s in ceas_samples:
        all_samples.append({"text": format_corpus_sample(s), "id": f"ceas_{hash(s['body'][:100])}"})

    # ── 3. Load Nigerian Fraud CSV ───────────────────────────────────────
    print("[MindWall] Loading Nigerian Fraud corpus...")
    fraud_path = RAW_DIR / "nigerian_fraud" / "nigerian_fraud_emails.csv"
    fraud_samples = parse_csv_corpus(fraud_path, body_col="body")
    print(f"  → {len(fraud_samples)} Nigerian Fraud samples loaded")
    for s in fraud_samples:
        all_samples.append({"text": format_corpus_sample(s), "id": f"fraud_{hash(s['body'][:100])}"})

    # ── 4. Shuffle and split ─────────────────────────────────────────────
    print(f"\n[MindWall] Total samples: {len(all_samples)}")
    random.shuffle(all_samples)

    split_ratio = config.get("train_split_ratio", 0.9)
    max_samples = config.get("max_samples")
    if max_samples:
        all_samples = all_samples[:max_samples]

    split_idx = int(len(all_samples) * split_ratio)
    train_samples = all_samples[:split_idx]
    eval_samples = all_samples[split_idx:]

    print(f"  → Train: {len(train_samples)} | Eval: {len(eval_samples)}")

    # ── 5. Save as HuggingFace datasets ──────────────────────────────────
    train_ds = Dataset.from_list(train_samples)
    eval_ds = Dataset.from_list(eval_samples)

    train_path = PROCESSED_DIR / "mindwall_train"
    eval_path = PROCESSED_DIR / "mindwall_eval"

    train_ds.save_to_disk(str(train_path))
    eval_ds.save_to_disk(str(eval_path))

    print(f"\n[MindWall] ✅ Datasets saved:")
    print(f"  Train: {train_path}")
    print(f"  Eval:  {eval_path}")

    # ── 6. Save stats ────────────────────────────────────────────────────
    stats = {
        "total_samples": len(all_samples),
        "train_samples": len(train_samples),
        "eval_samples": len(eval_samples),
        "prepared_at": datetime.utcnow().isoformat(),
    }
    with open(PROCESSED_DIR / "stats.json", "w") as f:
        json.dump(stats, f, indent=2)


if __name__ == "__main__":
    main()
