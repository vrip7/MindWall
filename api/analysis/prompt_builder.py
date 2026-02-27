"""
MindWall — LLM Prompt Construction
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Constructs structured prompts for the fine-tuned LLM to analyze emails
for psychological manipulation tactics.
"""

SYSTEM_PROMPT = """
You are MindWall, a cybersecurity analysis engine specialized in detecting
psychological manipulation tactics in business communications. You analyze
emails and messages with clinical precision, identifying social engineering
patterns used by attackers to manipulate recipients into unsafe actions.

You always respond with a valid JSON object and nothing else.
""".strip()


def build_analysis_prompt(
    email_body: str,
    sender_email: str,
    sender_display_name: str,
    subject: str,
    received_hour: int,
    baseline: dict | None,
    prefilter_signals: list[str],
) -> str:
    """
    Build a structured analysis prompt for the LLM.

    Args:
        email_body: Plain-text email body content (truncated to 4000 chars).
        sender_email: Sender's email address.
        sender_display_name: Sender's display name.
        subject: Email subject line.
        received_hour: Hour (UTC) when the email was received.
        baseline: Historical sender behavioral baseline data, or None.
        prefilter_signals: List of pre-filter signal strings detected.

    Returns:
        Formatted prompt string for the LLM.
    """
    baseline_context = ""
    if baseline:
        baseline_context = f"""
SENDER BEHAVIORAL BASELINE (historical communication pattern):
- Average word count per email: {baseline['avg_word_count']:.0f}
- Average sentence length: {baseline['avg_sentence_length']:.1f} words
- Typical send hours (UTC): {baseline['typical_hours']}
- Formality score (0=casual, 1=formal): {baseline['formality_score']:.2f}
- This email's send hour: {received_hour}
- Word count deviation: {baseline.get('word_count_deviation', 'N/A')}
"""

    prefilter_context = ""
    if prefilter_signals:
        prefilter_context = f"\nFAST-FILTER PRE-SIGNALS DETECTED: {', '.join(prefilter_signals)}"

    return f"""
Analyze the following email for psychological manipulation tactics.
{prefilter_context}
{baseline_context}

EMAIL METADATA:
- Sender: {sender_display_name} <{sender_email}>
- Subject: {subject}
- Received Hour (UTC): {received_hour}

EMAIL BODY:
---
{email_body[:4000]}
---

Score each of the following 12 manipulation dimensions from 0 to 100:
- artificial_urgency: manufactured time pressure or deadline
- authority_impersonation: falsely claiming or implying authority
- fear_threat_induction: using threats, consequences, or fear
- reciprocity_exploitation: leveraging past favors or obligations
- scarcity_tactics: creating false scarcity of time, resource, or opportunity
- social_proof_manipulation: fabricating consensus or peer behavior
- sender_behavioral_deviation: deviation from this sender's typical communication style
- cross_channel_coordination: evidence of coordinated multi-channel attack
- emotional_escalation: escalating emotional intensity to override rational thinking
- request_context_mismatch: the request is inconsistent with the stated context
- unusual_action_requested: requesting actions atypical for legitimate business communication
- timing_anomaly: suspicious timing relative to sender's typical patterns

Respond ONLY with this JSON structure:
{{
    "dimension_scores": {{
        "artificial_urgency": <0-100>,
        "authority_impersonation": <0-100>,
        "fear_threat_induction": <0-100>,
        "reciprocity_exploitation": <0-100>,
        "scarcity_tactics": <0-100>,
        "social_proof_manipulation": <0-100>,
        "sender_behavioral_deviation": <0-100>,
        "cross_channel_coordination": <0-100>,
        "emotional_escalation": <0-100>,
        "request_context_mismatch": <0-100>,
        "unusual_action_requested": <0-100>,
        "timing_anomaly": <0-100>
    }},
    "primary_tactic": "<name of highest-scoring dimension>",
    "explanation": "<1-2 sentence plain English explanation of what manipulation is occurring, written to warn a non-technical employee>",
    "recommended_action": "<proceed|verify|block>",
    "confidence": <0-100>
}}
"""
