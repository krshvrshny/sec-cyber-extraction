"""
NIST CSF 2.0 Cybersecurity Disclosure Scoring Pipeline
=======================================================
Computes per-filing:
  - Keyword counts k_f per NIST CSF function
  - Frequency weights w_f = k_f / sum(k_j)
  - Focus vector v in R^6
  - Balance Score B = 1 / sqrt(6 * sum(w_f^2))
  - Primary function (dominant thematic focus)

Dependencies: pip install pyarrow pandas openpyxl
"""

import re
import math
import pandas as pd
import numpy as np

# =============================================================================
# NIST CSF 2.0 KEYWORD DICTIONARY (~100-150 keywords per function)
# =============================================================================

NIST_KEYWORDS = {

    "GV": [  # GOVERN
        "governance", "board", "committee", "director", "oversight", "ciso",
        "chief information security", "chief security officer", "policy", "policies",
        "procedure", "procedures", "framework", "charter", "mandate", "accountability",
        "responsibility", "responsibilities", "reporting", "escalation", "delegation",
        "budget", "investment", "spending", "resource", "headcount", "cybersecurity budget",
        "security budget", "security investment", "program", "initiative",
        "third-party risk", "third party risk", "vendor risk", "supply chain risk",
        "supplier risk", "counterparty risk", "outsourcing risk", "vendor management",
        "third-party management", "due diligence", "vendor assessment",
        "risk management", "risk governance", "risk appetite", "risk tolerance",
        "risk strategy", "risk posture", "enterprise risk", "strategic risk",
        "risk committee", "audit committee", "risk officer", "compliance",
        "regulatory compliance", "legal compliance", "regulation", "regulatory",
        "sox", "gdpr", "ccpa", "hipaa", "pci", "nist", "iso 27001", "sec",
        "disclosure", "material", "materiality", "annual report",
        "cybersecurity program", "security program", "security strategy",
        "security governance", "information security governance",
        "management oversight", "executive oversight", "c-suite", "leadership",
        "security awareness", "culture", "training program", "security culture",
        "insurance", "cyber insurance", "cybersecurity insurance", "coverage",
        "indemnification", "liability", "legal risk", "reputational risk",
        "audit", "internal audit", "external audit", "assessment", "review",
        "certification", "accreditation", "attestation", "soc 2", "soc2",
        "information security policy", "acceptable use", "data governance",
        "data stewardship", "privacy policy", "privacy governance",
        "cyber risk management", "enterprise cybersecurity", "security roadmap",
        "security maturity", "capability maturity", "benchmarking",
        "board-level", "board level", "board reporting",
    ],

    "ID": [  # IDENTIFY
        "asset management", "asset inventory", "asset register", "it asset",
        "hardware inventory", "software inventory", "asset classification",
        "asset identification", "asset tracking", "configuration management",
        "cmdb", "configuration database", "software bill of materials", "sbom",
        "risk assessment", "risk analysis", "risk evaluation", "risk identification",
        "risk register", "risk framework", "inherent risk", "residual risk",
        "threat modeling", "threat assessment", "threat landscape", "threat actor",
        "threat intelligence", "cyber threat", "adversarial threat",
        "vulnerability management", "vulnerability assessment", "vulnerability scanning",
        "vulnerability identification", "cve", "cvss", "patch management",
        "penetration test", "penetration testing", "pentest", "red team",
        "ethical hacking", "bug bounty", "security testing",
        "attack surface", "attack surface management", "asm",
        "data classification", "data inventory", "data mapping", "data flow",
        "sensitive data", "pii", "personal information", "personal data",
        "intellectual property", "trade secret", "confidential information",
        "business impact analysis", "bia", "criticality assessment",
        "critical system", "critical asset", "crown jewel",
        "dependencies", "interdependencies", "system dependencies",
        "supply chain", "supply chain visibility", "third-party inventory",
        "exposure", "risk exposure", "digital footprint",
        "reconnaissance", "open source intelligence", "osint",
        "network mapping", "topology", "network diagram",
        "identity inventory", "privileged account", "account inventory",
        "cyber risk quantification", "risk quantification", "financial impact",
        "data breach impact", "breach cost", "loss estimation",
        "compliance gap", "gap analysis", "control gap",
        "risk prioritization", "risk ranking",
    ],

    "PR": [  # PROTECT
        "access control", "access management", "identity management", "iam",
        "identity and access management", "privileged access", "pam",
        "privileged access management", "least privilege", "zero trust",
        "zero-trust", "role-based access", "rbac", "attribute-based access",
        "multi-factor authentication", "mfa", "two-factor authentication", "2fa",
        "single sign-on", "sso", "authentication", "authorization",
        "password management", "password policy", "credential management",
        "encryption", "cryptography", "data encryption", "encryption at rest",
        "encryption in transit", "tls", "ssl", "aes", "rsa", "key management",
        "data loss prevention", "dlp", "data protection", "data security",
        "firewall", "next-generation firewall", "ngfw", "web application firewall",
        "waf", "network security", "network segmentation", "microsegmentation",
        "network isolation", "dmz", "perimeter security", "vpn",
        "virtual private network", "secure access", "secure remote access",
        "endpoint protection", "endpoint security", "edr",
        "endpoint detection and response", "antivirus", "anti-malware",
        "xdr", "extended detection and response", "mdm", "mobile device management",
        "patch", "patching", "software update", "firmware update", "vulnerability patch",
        "application security", "appsec", "secure coding", "sdlc",
        "secure software development", "code review", "static analysis", "sast",
        "dynamic analysis", "dast", "api security",
        "training", "security training", "awareness training", "phishing simulation",
        "user training", "employee training", "security education",
        "physical security", "badge access", "biometric", "cctv", "data center security",
        "cloud security", "cloud access security broker", "casb",
        "cloud configuration", "cloud posture", "cspm",
        "container security", "kubernetes security", "devsecops",
        "backup", "data backup", "immutable backup", "air gap",
        "secure configuration", "hardening", "system hardening", "baseline",
        "change management", "change control",
        "email security", "phishing protection", "spam filter",
        "web filtering", "dns security", "secure dns",
        "data masking", "tokenization", "anonymization", "pseudonymization",
    ],

    "DE": [  # DETECT
        "monitoring", "continuous monitoring", "security monitoring", "network monitoring",
        "siem", "security information and event management",
        "security operations center", "soc",
        "ids", "ips", "intrusion detection", "intrusion prevention",
        "threat detection", "anomaly detection", "behavioral analytics",
        "user behavior analytics", "ueba", "insider threat detection",
        "threat hunting", "proactive threat hunting", "hunt team",
        "log management", "log analysis", "log aggregation", "logging",
        "event correlation", "alert", "alerting",
        "threat intelligence", "intel feed", "ioc", "indicator of compromise",
        "ttp", "mitre att&ck", "mitre",
        "dark web monitoring", "brand monitoring", "external threat intelligence",
        "file integrity monitoring", "fim", "host-based detection",
        "network traffic analysis", "nta", "packet inspection", "deep packet inspection",
        "vulnerability scanning", "continuous scanning", "automated scanning",
        "security analytics", "machine learning detection",
        "ai detection", "artificial intelligence security",
        "managed detection", "mdr", "managed security service", "mssp",
        "cloud monitoring", "cloud detection", "cloud siem",
        "deception technology", "honeypot", "honeytrap",
        "fraud detection", "transaction monitoring",
        "endpoint telemetry", "telemetry",
        "real-time detection", "real time monitoring",
    ],

    "RS": [  # RESPOND
        "incident response", "incident management", "incident handling",
        "ir plan", "incident response plan", "response plan", "playbook",
        "runbook", "response procedure", "escalation procedure",
        "containment", "eradication", "remediation", "recovery action",
        "breach response", "breach notification", "data breach response",
        "forensics", "digital forensics", "forensic investigation",
        "root cause analysis", "post-incident", "lessons learned",
        "notification", "regulatory notification", "customer notification",
        "law enforcement", "fbi", "cisa", "regulatory reporting",
        "disclosure obligation", "material disclosure",
        "communication plan", "crisis communication", "public relations",
        "tabletop exercise", "red team exercise", "simulation",
        "incident drill", "cyber exercise", "wargame",
        "retainer", "ir retainer", "forensic retainer", "legal retainer",
        "external counsel", "outside counsel", "legal response",
        "ransom negotiation", "threat actor engagement",
        "coordination", "information sharing", "isac", "isao",
        "government coordination", "law enforcement coordination",
        "damage assessment", "impact assessment", "scope assessment",
        "chain of custody", "evidence preservation", "evidence collection",
        "incident classification", "severity classification", "triage",
        "mean time to respond", "mttr", "mean time to detect", "mttd",
    ],

    "RC": [  # RECOVER
        "recovery", "business continuity", "continuity plan", "bcp",
        "disaster recovery", "dr plan", "drp",
        "resilience", "cyber resilience", "operational resilience",
        "backup", "restore", "restoration", "system restore",
        "rto", "recovery time objective", "rpo", "recovery point objective",
        "failover", "fail over", "redundancy", "high availability",
        "geographic redundancy", "data center redundancy",
        "replication", "data replication", "geographic replication",
        "resumption", "service resumption", "operations resumption",
        "reconstitution", "system reconstitution",
        "rollback", "snapshot", "point-in-time recovery",
        "immutable storage", "offsite backup", "cloud backup",
        "recovery exercise", "recovery test", "dr test",
        "business impact", "recovery priority", "critical function",
        "recovery capability", "recovery strategy",
        "mean time to recover", "recovery metrics",
        "insurance recovery", "cyber insurance claim",
        "post-breach recovery", "after-incident recovery",
        "supply chain recovery", "vendor recovery",
        "recovery team", "crisis team", "recovery coordinator",
        "post-mortem", "after-action review",
    ],
}

FUNCTIONS = ["GV", "ID", "PR", "DE", "RS", "RC"]

# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def preprocess(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r'[-]', ' ', text)  # normalize hyphens: "zero-trust" -> "zero trust"
    text = re.sub(r'\s+', ' ', text)
    return text


def count_keywords(text: str, keywords: list) -> int:
    count = 0
    for kw in keywords:
        if ' ' in kw:
            count += text.count(kw)
        else:
            count += len(re.findall(r'\b' + re.escape(kw) + r'\b', text))
    return count


def compute_weights(text: str) -> tuple:
    """
    Returns (weights, counts).
      counts[f]  = raw keyword hits for function f  (k_f)
      weights[f] = w_f = k_f / sum(k_j)
    """
    processed = preprocess(text)
    counts    = {f: count_keywords(processed, NIST_KEYWORDS[f]) for f in FUNCTIONS}
    total     = sum(counts.values())
    weights   = {f: counts[f] / total if total > 0 else 0.0 for f in FUNCTIONS}
    return weights, counts


def compute_balance_score(weights: dict) -> float:
    """
    B = 1 / sqrt(6 * sum(w_f^2))
    Min ~0.408 (all weight on one function), Max 1.0 (perfectly uniform)
    """
    w      = np.array([weights[f] for f in FUNCTIONS])
    sum_sq = float(np.sum(w ** 2))
    return 0.0 if sum_sq == 0 else 1.0 / math.sqrt(6 * sum_sq)


# =============================================================================
# PIPELINE
# =============================================================================

def run_pipeline(
    parquet_path: str,
    text_col:     str = "combined_text",
    firm_col:     str = "company_name",
    output_path:  str = "nist_csf_scores.xlsx",
):
    print("=" * 60)
    print("NIST CSF 2.0 Cybersecurity Disclosure Scoring")
    print("=" * 60)

    # Load
    print(f"\n[1/4] Loading {parquet_path}")
    df = pd.read_parquet(parquet_path)
    print(f"      Shape   : {df.shape}")
    print(f"      Columns : {df.columns.tolist()}")

    # Composite firm+year label so each filing is uniquely identified
    if "year" in df.columns:
        df["_firm_year"] = df[firm_col].astype(str) + " (" + df["year"].astype(str) + ")"
        id_col = "_firm_year"
    else:
        id_col = firm_col

    df = df.dropna(subset=[text_col]).reset_index(drop=True)
    print(f"      Filings : {len(df)}")

    # Score each filing
    print(f"\n[2/4] Scoring filings...")
    rows = []
    for _, filing in df.iterrows():
        weights, counts = compute_weights(filing[text_col])
        balance         = compute_balance_score(weights)
        primary         = max(weights, key=weights.get) if any(weights.values()) else "N/A"

        row = {
            "firm_year":          filing[id_col],
            "ticker":             filing.get("ticker",       ""),
            "company_name":       filing.get("company_name", ""),
            "sector":             filing.get("sector",       ""),
            "year":               filing.get("year",         ""),
            "has_1c":             filing.get("has_1c",       ""),
            "total_keyword_hits": sum(counts.values()),
            "balance_score":      round(balance, 4),
            "balance_sufficient": balance >= 0.6,
            "primary_function":   primary,
        }
        for f in FUNCTIONS:
            row[f"w_{f}"] = round(weights[f], 4)
            row[f"k_{f}"] = counts[f]

        rows.append(row)

    results = pd.DataFrame(rows)

    # Enforce column order
    col_order = (
        ["firm_year", "ticker", "company_name", "sector", "year", "has_1c",
         "total_keyword_hits", "balance_score", "balance_sufficient", "primary_function"]
        + [f"w_{f}" for f in FUNCTIONS]
        + [f"k_{f}" for f in FUNCTIONS]
    )
    results = results[[c for c in col_order if c in results.columns]]

    # Save
    print(f"\n[3/4] Saving to {output_path}")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:

        # All scores
        results.to_excel(writer, sheet_name="Scores", index=False)

        # Focus vectors only — clean table ready for the paper
        focus_cols = (
            ["firm_year", "ticker", "company_name", "sector", "year"]
            + [f"w_{f}" for f in FUNCTIONS]
            + ["balance_score", "balance_sufficient", "primary_function"]
        )
        results[[c for c in focus_cols if c in results.columns]].to_excel(
            writer, sheet_name="Focus_Vectors", index=False
        )

        # Summary statistics across all filings
        stat_cols = [f"w_{f}" for f in FUNCTIONS] + ["balance_score", "total_keyword_hits"]
        results[stat_cols].describe().round(4).to_excel(writer, sheet_name="Summary_Stats")

    csv_path = output_path.replace(".xlsx", ".csv")
    results.to_csv(csv_path, index=False)

    # Console summary
    print(f"\n[4/4] Done\n")
    print(f"  {'Filing':<38} {'Balance':>7}  {'OK':>3}  {'Primary':>7}")
    print("  " + "-" * 60)
    for _, r in results.iterrows():
        ok = "Y" if r["balance_sufficient"] else "N"
        print(f"  {r['firm_year']:<38} {r['balance_score']:>7.4f}   {ok}   {r['primary_function']:>7}")

    n_ok = results["balance_sufficient"].sum()
    print(f"\n  Balance >= 0.6 : {n_ok}/{len(results)} filings pass threshold")
    print(f"\n  Saved : {output_path}")
    print(f"  Saved : {csv_path}")

    return results


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":

    PARQUET_PATH = "filings.parquet"
    TEXT_COL     = "combined_text"
    FIRM_COL     = "company_name"
    OUTPUT_PATH  = "nist_csf_scores.xlsx"

    results = run_pipeline(
        parquet_path=PARQUET_PATH,
        text_col=TEXT_COL,
        firm_col=FIRM_COL,
        output_path=OUTPUT_PATH,
    )