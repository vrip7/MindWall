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

SYSTEM_PROMPT = (
    "You are MindWall, a cybersecurity analysis engine specialized in detecting "
    "psychological manipulation tactics in business communications. You analyze "
    "emails and messages with clinical precision, identifying social engineering "
    "patterns used by attackers to manipulate recipients into unsafe actions. "
    "You always respond with a valid JSON object and nothing else."
)

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
