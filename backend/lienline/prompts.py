"""Every prompt LienLine sends to a model, in one place.

Each agent gets facts computed by code and must answer in JSON. Code then checks the answer;
the model never sets a number that reaches a decision.
"""

SYSTEM = (
    "You assist a bank's nodal officer handling holds placed on accounts after cyber-fraud complaints in India. "
    "Use only the facts given. Cite transaction ids (T1, T2, ...) and account ids (A1, A2, ...) exactly as given. "
    "Never invent a transaction, account, UTR or amount. Rupee amounts are written like 12,34,567.89. "
    "Reply with JSON only."
)

INTAKE = """Read the police notice and the victim's complaint below and extract what they state.

From the NOTICE: every line naming an account. For each give the masked account number exactly as written
(like XXXX1234), the rupee amount to be held, and the UTR exactly as written (12 digits).
From the COMPLAINT: every UTR the victim says they paid from, and the total amount the victim lost in rupees.

NOTICE:
{notice}

COMPLAINT:
{narrative}"""

PATTERNS = """For each account below, write one or two plain sentences for the bank's nodal officer explaining
what its mule signals mean and whether they point to a mule, a merchant or an ordinary customer. The signals were
computed by code; do not change them or add new ones. Cite the account id and any transaction ids you mention in
`refs`.

ACCOUNTS (JSON):
{accounts}"""

VICTIM_ADVOCATE = """You are the victim's advocate. The victim, {victim}, lost Rs {lost}. For each contested
account below, argue for the hold that best protects the victim's chance of getting money back. Ask for one of:
a lien equal to the traceable amount under one of the four tracing rules (quote that rule's figure exactly and name
the rule); a lien of the amount the police notice flagged (name the rule "NOTICE"); or a full freeze of the whole
balance if you think the mule signals justify it. Cite the transaction and account ids your argument rests on.

CONTESTED ACCOUNTS (JSON):
{accounts}"""

HOLDER_ADVOCATE = """You are the account holders' advocate. Banks froze these accounts in full, and the High Courts
(MP HC, Archana v State of MP; Rajasthan HC, Shree Balaji Enterprises v RBI) held that only the identifiable
disputed amount may be held. For each contested account below, argue for the smallest hold the facts support:
either a release (amount 0) if some tracing rule finds nothing traceable, or a lien equal to the traceable amount
under one named tracing rule (quote that rule's figure exactly). Cite the transaction and account ids your
argument rests on.

CONTESTED ACCOUNTS (JSON):
{accounts}"""

DRAFTER = """Draft a formal letter from the bank's nodal officer.

Letter type: {kind}
To: {to}
Purpose: {purpose}

FACTS (use these rupee figures, UTRs and account numbers exactly as written; do not state any other amount,
do not round, and do not write amounts in words or in lakh/crore):
{facts}

Keep the body under 220 words, in plain formal English, with short paragraphs. Do not add a signature block
beyond "Nodal Officer, {bank}". Return the subject line and the body."""

DRAFTER_RETRY = """{prompt}

Your previous draft was rejected by the number checker for these reasons:
{problems}
Write it again using only the figures listed in FACTS."""
