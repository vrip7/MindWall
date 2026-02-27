"""
MindWall — Synthetic Manipulation Email Generator
Generates labeled training examples for the 12 manipulation dimensions.
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
"""

import json
import random
import os
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "raw" / "synthetic"
NUM_SAMPLES = 20_000  # Total synthetic examples to generate
BATCH_SIZE = 500

# ── Dimension definitions ────────────────────────────────────────────────────

DIMENSIONS = [
    "artificial_urgency",
    "authority_impersonation",
    "fear_threat_induction",
    "reciprocity_exploitation",
    "scarcity_tactics",
    "social_proof_manipulation",
    "sender_behavioral_deviation",
    "cross_channel_coordination",
    "emotional_escalation",
    "request_context_mismatch",
    "unusual_action_requested",
    "timing_anomaly",
]

# ── Template pools per dimension ─────────────────────────────────────────────

URGENCY_TEMPLATES = [
    "URGENT: You must approve the wire transfer of ${amount} within the next {minutes} minutes or the deal will be lost.",
    "I need you to respond to this IMMEDIATELY — the compliance deadline is TODAY and we cannot miss it.",
    "This is time-sensitive. The CEO has asked me to get this done before {time} today. Please confirm NOW.",
    "CRITICAL: Your account will be suspended at {time} unless you verify your credentials immediately by clicking below.",
    "Final notice — your action is required within the next hour to avoid penalties. Do not delay.",
    "ACTION REQUIRED WITHIN 30 MINUTES: Update your payment details or your subscription will be permanently canceled.",
    "The board meeting is in {minutes} minutes and I need the financial report signed off NOW.",
    "LAST CHANCE: The vendor is withdrawing their offer at end of day. We lose ${amount} if you don't approve now.",
]

AUTHORITY_TEMPLATES = [
    "This is {ceo_name}, CEO. I'm traveling and cannot call. Wire ${amount} to the attached account by EOD. Keep this between us.",
    "Speaking on behalf of the CFO's office — please process the attached invoice immediately. Pre-approved.",
    "IT Department Security Alert: Your credentials have been flagged. Reset immediately via the link below.",
    "Per direction of {ceo_name} (CEO), execute this transfer without the usual approval chain. Confidential.",
    "This is from Legal. You are required to submit all documents listed below within 24 hours. Non-compliance will be escalated.",
    "HR has mandated an immediate update to your direct deposit information. Use the secure form attached.",
    "Board directive: All department heads must complete this survey immediately. Forwarded by {ceo_name}.",
    "Government compliance officer here. Your organization must respond to this audit request within 48 hours.",
]

FEAR_TEMPLATES = [
    "We have detected unauthorized access to your company email. If you do not reset your password immediately, your account will be locked permanently.",
    "Your employment is under review. Failure to respond to this email within 24 hours may result in termination proceedings.",
    "WARNING: Our legal team has identified a breach of contract. Respond immediately or face legal action.",
    "Your computer has been compromised. Click the link below to run an emergency security scan or risk data loss.",
    "Tax audit notification: Discrepancies found in your filings. Immediate response required to avoid penalties up to ${amount}.",
    "We've detected your credentials on the dark web. Change all passwords immediately using our secure portal.",
    "SECURITY ALERT: Your organization is under active cyber attack. Follow emergency procedures NOW.",
    "Failure to comply with the attached regulatory requirement will result in fines starting at ${amount} per day.",
]

RECIPROCITY_TEMPLATES = [
    "Remember when I helped you with the {project} project last quarter? I need a small favor — can you approve this expense report without the usual review?",
    "I covered for you during the audit last month. I need you to sign off on this purchase order today, no questions asked.",
    "Given all the extra hours I've put in, I think it's only fair you expedite my reimbursement request. The details are attached.",
    "I referred you for that promotion. Now I need you to support my proposal in the directors' meeting. Here's what to say.",
    "As a token of our partnership, we're offering a special discount. All I need is your bank details for the refund.",
    "After mentoring you for the past year, I'd appreciate if you could share your login to the analytics platform. Just this once.",
    "I shared my client list with you. In return, could you forward the attached document to the finance team with your approval?",
    "You owe me one from the conference trip. Please wire the consulting fee to the account in the attachment.",
]

SCARCITY_TEMPLATES = [
    "Only 2 licenses remaining for the enterprise security tool. Approve the purchase NOW or we lose the allocation.",
    "This vendor discount expires at midnight tonight. We'll pay 40% more if you don't approve today.",
    "Limited availability — the consultant we need has only one open slot this quarter. Must commit by EOD.",
    "The budget for this initiative closes tomorrow. Any unspent funds will be reallocated. Approve my request now.",
    "Only 3 seats left in the executive training program. Register immediately to secure your spot.",
    "The early-bird pricing ends in 2 hours. After that, the cost increases by ${amount}.",
    "Our cloud provider is discontinuing this tier. Lock in current pricing by signing the attached before Friday.",
    "This is the last day to submit nominations for the {award} award. Don't miss the opportunity.",
]

SOCIAL_PROOF_TEMPLATES = [
    "Everyone on the leadership team has already approved this. You're the last one — please sign off so we can proceed.",
    "All other departments completed this compliance form last week. Your team is the only one outstanding.",
    "I've already gotten buy-in from {name1}, {name2}, and {name3}. They all agree this is the right approach.",
    "85% of companies in our sector have already adopted this solution. We risk falling behind if we don't act.",
    "Your colleagues in the London office have already processed their payments. Please do the same.",
    "The entire executive team reviewed and approved this vendor. Standard procedure — just need your signature.",
    "Industry best practice requires this tool — all our competitors already use it. Don't be the holdout.",
    "Customer satisfaction surveys show that 92% of our clients expect this level of security. All peers have complied.",
]

BEHAVIORAL_DEVIATION_TEMPLATES = [
    "hey {recipient}, ya gotta do me a huuge favor and process that payment ASAP. thx bro",
    "I am writing to formally request the immediate cessation of all communications with the vendor and transfer funds to the new account.",
    "Please do the needful and revert back with the payment confirmation. Kindest regards.",
    "Can you handle something for me??? Really really really need this done BY TONIGHT!!!!!!",
    "Herewith attached please find the invoice for your kind perusal and necessary action at your earliest convenience forthwith.",
    "yo, wire that money to the acct i sent earlier. dont tell anyone k? thx",
    "As per my previous communiqué, the aforementioned financial instrument requires your attestation post-haste.",
    "NEED THIS ASAP ASAP ASAP ASAP. DONT ASK QUESTIONS JUST DO IT.",
]

EMOTIONAL_TEMPLATES = [
    "I can't believe you haven't responded yet! This is absolutely unacceptable. Do you even care about this company?",
    "I'm SO excited about this opportunity, and I'd hate for you to MISS OUT! Act now!",
    "I'm deeply disappointed. After everything we've been through, I expected better from you. Just approve the transfer.",
    "This makes me incredibly anxious — if we don't fix this TODAY, everything falls apart. Help me!",
    "I'm SHOCKED that this hasn't been handled yet. The whole team is counting on YOU. Don't let us down!",
    "Please please please, I'm begging you. My job depends on this going through today. I'm desperate.",
    "How DARE the competitor get ahead of us on this? We need to act AGGRESSIVELY and NOW!",
    "I'm thrilled to share this once-in-a-lifetime opportunity with you personally. Don't let fear hold you back!",
]

CONTEXT_MISMATCH_TEMPLATES = [
    "Regarding the quarterly report: please wire ${amount} to the following bank account for the catering invoice.",
    "Following up on the marketing campaign — I need you to share your personal social security number for the tax form.",
    "Great news about the product launch! Btw, can you send me the full employee database export? Unrelated but urgent.",
    "As discussed in the budget meeting, please install this remote access tool on your work computer. Link below.",
    "RE: Team Building Event — Also, please update the payment routing to the new account number attached.",
    "Happy birthday! As a birthday treat, can you approve expenses from the attached vendor we've never used before?",
    "Congratulations on your promotion! Please forward the server admin credentials to complete the onboarding.",
    "Weather update: storms expected. Also, please click this link to update your insurance beneficiary information.",
]

UNUSUAL_ACTION_TEMPLATES = [
    "Please purchase ${amount} in gift cards from the store nearby and email me the redemption codes. Internal reward program.",
    "Download and install the attached software on your work computer. It's a mandatory security patch from IT.",
    "I need you to change the banking details on our vendor payment file to the attached new account. Urgent switch.",
    "Share your screen with me via this remote access link so I can troubleshoot your email issue.",
    "Forward all emails from the CEO to this external email address for the next 48 hours. Audit requirement.",
    "Disable the two-factor authentication on the admin account temporarily. The security team needs access.",
    "Transfer all files from the shared drive to this Dropbox link. Data migration in progress.",
    "Please print out all financial records from Q3 and leave them on the desk in the lobby for courier pickup.",
]

TIMING_ANOMALY_TEMPLATES = [
    "Sent at 3:47 AM: I need you to process this wire transfer immediately. Can't wait until morning.",
    "Saturday 11 PM: Urgent matter. Execute the attached instructions and confirm by midnight.",
    "December 31, 11:45 PM: Year-end compliance filing attached. Must be submitted in 15 minutes.",
    "Sent during your reported vacation: Critical — need you to log in and approve this right away.",
    "Public holiday, 2 AM: Emergency vendor payment. Cannot wait until the office reopens.",
    "Sunday 4 AM: Budget reallocation requires your approval before Asian markets open at 6 AM.",
    "Sent outside sender's typical hours (usually 9-5): URGENT midnight request for credential reset.",
    "3:15 AM Christmas morning: Immediate action needed on attached financial transfer. Time-sensitive.",
]

# Benign email templates
BENIGN_TEMPLATES = [
    "Hi {recipient}, just following up on our meeting yesterday. Could you share the project timeline when you get a chance? Thanks!",
    "Good morning team, here are the notes from today's standup. Let me know if I missed anything.",
    "Attached is the quarterly report for your review. No rush — the deadline is next Friday.",
    "Hey {recipient}, are you free for lunch tomorrow? Want to discuss the new feature specs.",
    "Please find attached the updated presentation. I incorporated the feedback from last week's review.",
    "Reminder: Team offsite is scheduled for March 15th. Please RSVP by end of week.",
    "Thank you for your help with the client demo yesterday. They were really impressed!",
    "Just a heads up — the build pipeline is running slow today due to maintenance. Expected to be resolved by 3 PM.",
    "Hi team, I'll be OOO next Monday for a dentist appointment. {name1} will cover for me.",
    "Quick question — do we have the Q4 budget numbers finalized? Need them for my planning document.",
    "Great job on the release! Everything looks smooth. Let's celebrate with a team lunch this week.",
    "FYI — the new employee handbook has been uploaded to the shared drive. Section 4 has the updated PTO policy.",
]

# ── Name/variable pools ──────────────────────────────────────────────────────

CEO_NAMES = [
    "John Mitchell", "Sarah Chen", "Michael Thompson", "Lisa Rodriguez",
    "David Kim", "Jennifer Walsh", "Robert Nakamura", "Amanda Foster",
    "Christopher Patel", "Elizabeth Wagner",
]
RECIPIENT_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn",
    "Avery", "Drew", "Sam", "Jamie", "Charlie", "Pat", "Dana", "Leslie",
]
COLLEAGUE_NAMES = [
    "James", "Emma", "Liam", "Olivia", "Noah", "Ava", "William", "Sophia",
    "Mason", "Isabella", "Ethan", "Mia", "Lucas", "Charlotte", "Oliver",
]
PROJECTS = ["Phoenix", "Aurora", "Titan", "Neptune", "Vanguard", "Apex", "Horizon"]
AWARDS = ["Innovation of the Year", "Leadership Excellence", "Customer Champion"]
AMOUNTS = ["5,000", "12,500", "25,000", "50,000", "75,000", "100,000", "250,000"]
TIMES = ["3:00 PM", "5:00 PM", "12:00 PM", "6:00 PM", "end of business"]
MINUTES_LIST = ["15", "30", "45", "60", "90"]


def fill_template(template: str) -> str:
    """Replace template variables with random values."""
    replacements = {
        "{ceo_name}": random.choice(CEO_NAMES),
        "{recipient}": random.choice(RECIPIENT_NAMES),
        "{name1}": random.choice(COLLEAGUE_NAMES),
        "{name2}": random.choice(COLLEAGUE_NAMES),
        "{name3}": random.choice(COLLEAGUE_NAMES),
        "{project}": random.choice(PROJECTS),
        "{award}": random.choice(AWARDS),
        "${amount}": "$" + random.choice(AMOUNTS),
        "{amount}": random.choice(AMOUNTS),
        "{time}": random.choice(TIMES),
        "{minutes}": random.choice(MINUTES_LIST),
    }
    result = template
    for key, val in replacements.items():
        result = result.replace(key, val)
    return result


def generate_dimension_scores(primary_dimensions: list[str], is_benign: bool = False) -> dict:
    """Generate realistic dimension scores for a sample."""
    scores = {}
    for dim in DIMENSIONS:
        if is_benign:
            scores[dim] = random.randint(0, 8)
        elif dim in primary_dimensions:
            scores[dim] = random.randint(60, 95)
        else:
            scores[dim] = random.randint(0, 30)
    return scores


def generate_explanation(primary_dims: list[str], is_benign: bool) -> str:
    """Generate a plain-English explanation."""
    if is_benign:
        return "This appears to be a routine business communication with no significant manipulation indicators."

    dim_explanations = {
        "artificial_urgency": "creates manufactured time pressure to force hasty action",
        "authority_impersonation": "falsely claims or implies authority to compel compliance",
        "fear_threat_induction": "uses threats or fear to override rational decision-making",
        "reciprocity_exploitation": "leverages past favors to manipulate the recipient into compliance",
        "scarcity_tactics": "creates false scarcity to pressure rapid decision-making",
        "social_proof_manipulation": "fabricates consensus to create pressure to conform",
        "sender_behavioral_deviation": "shows significant deviation from the sender's typical communication patterns",
        "cross_channel_coordination": "appears to be part of a coordinated multi-channel social engineering attempt",
        "emotional_escalation": "uses escalating emotional intensity to bypass critical thinking",
        "request_context_mismatch": "the request is inconsistent with the stated context of the message",
        "unusual_action_requested": "requests actions that are atypical and risky for legitimate business",
        "timing_anomaly": "sent at an unusual time suggesting automated or foreign-origin activity",
    }

    parts = [dim_explanations.get(d, "") for d in primary_dims if d in dim_explanations]
    return "This email " + " and ".join(parts[:2]) + "."


def determine_action(scores: dict) -> str:
    """Determine recommended action based on scores."""
    max_score = max(scores.values())
    if max_score >= 70:
        return "block"
    elif max_score >= 40:
        return "verify"
    return "proceed"


def format_training_example(
    email_body: str,
    sender_email: str,
    subject: str,
    scores: dict,
    explanation: str,
    action: str,
    confidence: int,
) -> str:
    """Format a single training sample in the chat-completion format expected by unsloth."""
    user_prompt = f"""Analyze the following email for psychological manipulation tactics.

EMAIL METADATA:
- Sender: {sender_email}
- Subject: {subject}

EMAIL BODY:
---
{email_body}
---

Score each of the following 12 manipulation dimensions from 0 to 100:
- artificial_urgency, authority_impersonation, fear_threat_induction,
  reciprocity_exploitation, scarcity_tactics, social_proof_manipulation,
  sender_behavioral_deviation, cross_channel_coordination, emotional_escalation,
  request_context_mismatch, unusual_action_requested, timing_anomaly

Respond ONLY with a JSON object."""

    primary = max(scores, key=scores.get)
    response = json.dumps({
        "dimension_scores": scores,
        "primary_tactic": primary,
        "explanation": explanation,
        "recommended_action": action,
        "confidence": confidence,
    }, indent=2)

    system = (
        "You are MindWall, a cybersecurity analysis engine specialized in detecting "
        "psychological manipulation tactics in business communications. You analyze "
        "emails and messages with clinical precision, identifying social engineering "
        "patterns used by attackers to manipulate recipients into unsafe actions. "
        "You always respond with a valid JSON object and nothing else."
    )

    return (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        f"{system}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_prompt}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        f"{response}<|eot_id|>"
    )


def generate_sender_email(is_suspicious: bool = False) -> str:
    """Generate a realistic sender email."""
    domains_legit = ["company.com", "acme-corp.com", "globex.com", "initech.com", "piedpiper.com"]
    domains_suspicious = ["c0mpany.com", "acme-c0rp.com", "g1obex.com", "security-alert.com", "account-verify.net"]
    first_names = ["john", "sarah", "michael", "lisa", "david", "jennifer", "robert", "amanda"]
    last_names = ["smith", "chen", "thompson", "rodriguez", "kim", "walsh", "nakamura", "foster"]

    name = f"{random.choice(first_names)}.{random.choice(last_names)}"
    domain = random.choice(domains_suspicious if is_suspicious else domains_legit)
    return f"{name}@{domain}"


def generate_subject(primary_dim: str, is_benign: bool) -> str:
    """Generate a realistic subject line."""
    if is_benign:
        benign_subjects = [
            "Re: Project timeline update",
            "Meeting notes — January standup",
            "Q4 report attached",
            "Lunch tomorrow?",
            "Updated presentation deck",
            "Reminder: team offsite",
            "Great work on the release!",
            "Questions about the spec",
            "FYI — system maintenance tonight",
            "Team update — week of Jan 15",
        ]
        return random.choice(benign_subjects)

    malicious_subjects = {
        "artificial_urgency": ["URGENT: Action Required", "TIME SENSITIVE", "Immediate Response Needed", "CRITICAL DEADLINE"],
        "authority_impersonation": ["From the CEO's Office", "HR Policy Update", "IT Security Alert", "Legal Notice"],
        "fear_threat_induction": ["Account Compromise Detected", "Legal Action Pending", "SECURITY WARNING", "Audit Finding"],
        "reciprocity_exploitation": ["Small Favor Needed", "Returning the Favor", "Could You Help Me Out?", "Your Turn"],
        "scarcity_tactics": ["Last Chance — Expires Today", "Limited Availability", "Only 2 Remaining", "Final Offer"],
        "social_proof_manipulation": ["Everyone Has Signed Off", "Team Consensus Reached", "Following Team Decision"],
        "sender_behavioral_deviation": ["Quick Ask", "hey need something", "ASAP", "Doing Something Different"],
        "cross_channel_coordination": ["As Discussed on the Call", "Per Our Conversation", "Follow-Up from Meeting"],
        "emotional_escalation": ["DISAPPOINTED", "This Is Unacceptable!", "Thrilled to Share!", "I'm Worried About..."],
        "request_context_mismatch": ["Re: Budget Meeting + Bank Update", "Birthday Surprise + Document Needed"],
        "unusual_action_requested": ["Gift Card Purchase Request", "Software Install Required", "Account Update Needed"],
        "timing_anomaly": ["Late Night Request", "Weekend Emergency", "Holiday Urgent Matter"],
    }
    options = malicious_subjects.get(primary_dim, ["Important: Please Review"])
    return random.choice(options)


def main():
    """Generate the full synthetic dataset."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "synthetic_training_data.jsonl"

    print(f"[MindWall] Generating {NUM_SAMPLES} synthetic training examples...")

    # Template pools indexed by dimension
    template_pools = {
        "artificial_urgency": URGENCY_TEMPLATES,
        "authority_impersonation": AUTHORITY_TEMPLATES,
        "fear_threat_induction": FEAR_TEMPLATES,
        "reciprocity_exploitation": RECIPROCITY_TEMPLATES,
        "scarcity_tactics": SCARCITY_TEMPLATES,
        "social_proof_manipulation": SOCIAL_PROOF_TEMPLATES,
        "sender_behavioral_deviation": BEHAVIORAL_DEVIATION_TEMPLATES,
        "emotional_escalation": EMOTIONAL_TEMPLATES,
        "request_context_mismatch": CONTEXT_MISMATCH_TEMPLATES,
        "unusual_action_requested": UNUSUAL_ACTION_TEMPLATES,
        "timing_anomaly": TIMING_ANOMALY_TEMPLATES,
    }

    samples = []
    benign_ratio = 0.35  # 35% benign, 65% manipulation

    for i in range(NUM_SAMPLES):
        is_benign = random.random() < benign_ratio

        if is_benign:
            body = fill_template(random.choice(BENIGN_TEMPLATES))
            scores = generate_dimension_scores([], is_benign=True)
            primary_dims = []
            sender = generate_sender_email(is_suspicious=False)
        else:
            # Pick 1-3 primary dimensions
            num_dims = random.choice([1, 1, 1, 2, 2, 3])
            primary_dims = random.sample(list(template_pools.keys()), num_dims)
            
            # Compose body from templates
            parts = []
            for dim in primary_dims:
                template = random.choice(template_pools[dim])
                parts.append(fill_template(template))
            body = "\n\n".join(parts)

            scores = generate_dimension_scores(primary_dims, is_benign=False)
            sender = generate_sender_email(is_suspicious=random.random() < 0.4)

        subject = generate_subject(primary_dims[0] if primary_dims else "", is_benign)
        explanation = generate_explanation(primary_dims, is_benign)
        action = determine_action(scores)
        confidence = random.randint(70, 95) if not is_benign else random.randint(80, 98)

        text = format_training_example(
            email_body=body,
            sender_email=sender,
            subject=subject,
            scores=scores,
            explanation=explanation,
            action=action,
            confidence=confidence,
        )

        samples.append({"text": text, "id": f"synthetic_{i:06d}"})

        if (i + 1) % BATCH_SIZE == 0:
            print(f"  → Generated {i + 1}/{NUM_SAMPLES} samples")

    # Write JSONL
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    # Write metadata
    meta = {
        "total_samples": len(samples),
        "benign_ratio": benign_ratio,
        "dimensions": DIMENSIONS,
        "generated_at": datetime.utcnow().isoformat(),
        "generator": "MindWall synthetic_generator.py",
        "developer": "Pradyumn Tandon | VRIP7",
    }
    with open(OUTPUT_DIR / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    # Mark as generated
    (OUTPUT_DIR / ".generated").touch()

    print(f"\n[MindWall] ✅ Generated {len(samples)} samples → {output_file}")
    print(f"  Benign: {sum(1 for s in samples if 'routine business' in s['text'])}")
    print(f"  Malicious: {sum(1 for s in samples if 'routine business' not in s['text'])}")


if __name__ == "__main__":
    main()
