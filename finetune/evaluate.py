"""
MindWall — Model Evaluation Script
Evaluates the fine-tuned model against a held-out test set.
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

import yaml
import torch
import numpy as np
from unsloth import FastLanguageModel
from datasets import load_from_disk
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from tqdm import tqdm

# ── Configuration ────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "configs" / "qlora_config.yaml"

DIMENSIONS = [
    "artificial_urgency", "authority_impersonation", "fear_threat_induction",
    "reciprocity_exploitation", "scarcity_tactics", "social_proof_manipulation",
    "sender_behavioral_deviation", "cross_channel_coordination",
    "emotional_escalation", "request_context_mismatch",
    "unusual_action_requested", "timing_anomaly",
]

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


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def extract_json_from_text(text: str) -> dict | None:
    """Extract JSON object from model output text."""
    # Try to find JSON block
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def extract_ground_truth(sample_text: str) -> dict | None:
    """Extract the ground truth response from a formatted training sample."""
    # The assistant response is between the last header and eot_id
    match = re.search(
        r'<\|start_header_id\|>assistant<\|end_header_id\|>\s*\n\n([\s\S]*?)<\|eot_id\|>',
        sample_text
    )
    if match:
        return extract_json_from_text(match.group(1))
    return None


def extract_user_prompt(sample_text: str) -> str:
    """Extract the user prompt from a formatted training sample."""
    match = re.search(
        r'<\|start_header_id\|>user<\|end_header_id\|>\s*\n\n([\s\S]*?)<\|eot_id\|>',
        sample_text
    )
    return match.group(1) if match else ""


def severity_from_scores(scores: dict) -> str:
    """Determine severity from dimension scores."""
    if not scores:
        return "low"
    # Weighted aggregate
    weights = {
        "artificial_urgency": 0.12, "authority_impersonation": 0.15,
        "fear_threat_induction": 0.12, "reciprocity_exploitation": 0.07,
        "scarcity_tactics": 0.07, "social_proof_manipulation": 0.06,
        "sender_behavioral_deviation": 0.12, "cross_channel_coordination": 0.08,
        "emotional_escalation": 0.07, "request_context_mismatch": 0.06,
        "unusual_action_requested": 0.05, "timing_anomaly": 0.03,
    }
    agg = sum(scores.get(d, 0) * weights.get(d, 0) for d in DIMENSIONS)
    if agg >= 80: return "critical"
    if agg >= 60: return "high"
    if agg >= 35: return "medium"
    return "low"


def main():
    config = load_config()

    print("=" * 60)
    print("  MindWall — Model Evaluation")
    print("=" * 60)

    # ── 1. Load model ────────────────────────────────────────────────────
    print("\n[1/3] Loading fine-tuned model...")
    merged_dir = config["merged_output_dir"]

    if not Path(merged_dir).exists():
        print(f"  ❌ Merged model not found at {merged_dir}")
        print("  Run train.py first.")
        sys.exit(1)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=merged_dir,
        max_seq_length=config["max_seq_length"],
        dtype=None,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)

    # ── 2. Load eval dataset ─────────────────────────────────────────────
    print("[2/3] Loading evaluation dataset...")
    eval_path = config.get("eval_dataset_dir", "./datasets/processed/mindwall_eval")
    if not Path(eval_path).exists():
        print(f"  ❌ Eval dataset not found at {eval_path}")
        print("  Run prepare_dataset.py first.")
        sys.exit(1)

    eval_dataset = load_from_disk(eval_path)
    print(f"  Eval samples: {len(eval_dataset)}")

    # Limit for interactive evaluation (full eval can be slow)
    max_eval = min(500, len(eval_dataset))
    eval_subset = eval_dataset.select(range(max_eval))

    # ── 3. Run evaluation ────────────────────────────────────────────────
    print(f"[3/3] Evaluating {max_eval} samples...")

    gt_scores = defaultdict(list)  # dimension -> list of ground truth scores
    pred_scores = defaultdict(list)  # dimension -> list of predicted scores
    gt_actions = []
    pred_actions = []
    gt_severities = []
    pred_severities = []
    parse_failures = 0

    for i, sample in enumerate(tqdm(eval_subset, desc="Evaluating")):
        text = sample["text"]
        ground_truth = extract_ground_truth(text)
        if not ground_truth or "dimension_scores" not in ground_truth:
            continue

        user_prompt = extract_user_prompt(text)
        if not user_prompt:
            continue

        # Generate prediction
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs,
                max_new_tokens=1024,
                temperature=0.1,
                do_sample=False,
            )

        decoded = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        prediction = extract_json_from_text(decoded)

        if not prediction or "dimension_scores" not in prediction:
            parse_failures += 1
            continue

        # Collect dimension-level scores
        gt_dims = ground_truth["dimension_scores"]
        pred_dims = prediction["dimension_scores"]

        for dim in DIMENSIONS:
            if dim in gt_dims and dim in pred_dims:
                gt_scores[dim].append(float(gt_dims[dim]))
                pred_scores[dim].append(float(pred_dims[dim]))

        # Collect action and severity
        gt_actions.append(ground_truth.get("recommended_action", "proceed"))
        pred_actions.append(prediction.get("recommended_action", "proceed"))

        gt_severities.append(severity_from_scores(gt_dims))
        pred_severities.append(severity_from_scores(pred_dims))

    # ── 4. Compute metrics ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  EVALUATION RESULTS")
    print("=" * 60)

    print(f"\n  Samples evaluated: {max_eval}")
    print(f"  JSON parse failures: {parse_failures} ({100 * parse_failures / max_eval:.1f}%)")

    # Dimension-level MAE
    print("\n  Per-Dimension Mean Absolute Error:")
    print(f"  {'Dimension':<35} {'MAE':>8} {'RMSE':>8} {'Samples':>8}")
    print("  " + "-" * 61)

    all_gt = []
    all_pred = []
    for dim in DIMENSIONS:
        if gt_scores[dim]:
            gt = np.array(gt_scores[dim])
            pred = np.array(pred_scores[dim])
            mae = mean_absolute_error(gt, pred)
            rmse = np.sqrt(mean_squared_error(gt, pred))
            print(f"  {dim:<35} {mae:>8.2f} {rmse:>8.2f} {len(gt):>8}")
            all_gt.extend(gt.tolist())
            all_pred.extend(pred.tolist())

    if all_gt:
        overall_mae = mean_absolute_error(all_gt, all_pred)
        overall_rmse = np.sqrt(mean_squared_error(all_gt, all_pred))
        print("  " + "-" * 61)
        print(f"  {'OVERALL':<35} {overall_mae:>8.2f} {overall_rmse:>8.2f} {len(all_gt):>8}")

    # Action accuracy
    if gt_actions and pred_actions:
        action_acc = accuracy_score(gt_actions, pred_actions)
        print(f"\n  Action Recommendation Accuracy: {action_acc:.2%}")
        print("\n  Action Classification Report:")
        print(classification_report(gt_actions, pred_actions, zero_division=0))

    # Severity accuracy
    if gt_severities and pred_severities:
        sev_acc = accuracy_score(gt_severities, pred_severities)
        print(f"  Severity Classification Accuracy: {sev_acc:.2%}")
        print("\n  Severity Classification Report:")
        print(classification_report(gt_severities, pred_severities, zero_division=0))

    # ── 5. Save results ──────────────────────────────────────────────────
    results = {
        "samples_evaluated": max_eval,
        "parse_failures": parse_failures,
        "overall_mae": overall_mae if all_gt else None,
        "overall_rmse": overall_rmse if all_gt else None,
        "action_accuracy": float(accuracy_score(gt_actions, pred_actions)) if gt_actions else None,
        "severity_accuracy": float(accuracy_score(gt_severities, pred_severities)) if gt_severities else None,
        "per_dimension_mae": {
            dim: float(mean_absolute_error(gt_scores[dim], pred_scores[dim]))
            for dim in DIMENSIONS if gt_scores[dim]
        },
        "evaluated_at": str(Path(merged_dir).resolve()),
    }

    results_path = Path(config["output_dir"]) / "eval_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n  Results saved to: {results_path}")
    print("✅ Evaluation complete!")


if __name__ == "__main__":
    main()
