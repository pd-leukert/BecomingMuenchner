# BecomingMünchner

## Inspiration
Germany's new citizenship law (StAG 2024) has triggered a historic surge in applications. In Munich alone, thousands of people are waiting to become citizens. The bottleneck isn't the law. It's the manual verification process. Case workers spend hours on the complex detective work required for every application: verifying each person’s full residency history, checking the legal basis for their stay, and confirming whether they earn enough to support themselves. 
We wanted to build a "Digital Fast Lane": A system that doesn't just digitize documents, but forensically verifies and logically understands them. Our goal was to provide a semantic deep check of submitted documents to ensure consistency within each other and the regulatory requirements.

## What it does
BecomingMünchner is an AI-powered verification pipeline for naturalization applications. It performs three layers of deep analysis:

🛡️ Forensic Integrity Scan: Before reading a single word, the deployed TruFor (Transformer for Forgery) model scans documents for invisible pixel manipulations (splicing, copy-move attacks). It generates a heatmap revealing if a salary number or date has been photoshopped.

👁️ Semantic Extraction (VLM): We use State-of-the-Art Vision-Language Models (Qwen2-VL) to extract structured data from complex German documents (Passports, eAT, Payslips, language certificates, etc.). It handles multi-page PDFs and messy scans.

🕸️ Knowledge Graph Consistency: Instead of simple rule-checks, we build a **Dynamic Knowledge Graph**. We map every extracted fact (Person, Address, Income) as a node. The system then runs graph traversal algorithms to find contradictions:
- Does the address on the payslip match the rent contract?
- Is the residence timeline gapless for 5 years?
- Is the disposable income (Netto - Warmmiete) above the SGB II threshold?

## How we built it
We built BecomingMünchner to be a seamless extension of a modern web portal.

Frontend: We used Svelte to create a clean, accessible, and reassuring user interface.

The Brain (Verification Unit):
- Perception Layer: Extracts structured data using VLM (Qwen) and advanced "Spatial Prompting" for forensic checks. TruFor is also used for manipulation detection.
- Knowledge Graph Layer: Maps extracted entities into a NetworkX graph to query relationships between documents (e.g., checking if rent contract and payslip dates overlap).
- Logic Engine Layer: A deterministic Python module enforces the StAG 2024 law, handling legal rules and livelihood calculations.
The system combines AI for data extraction with rule-based logic for legal checks, ensuring accuracy and compliance *without relying entirely on AI for critical decisions*.

Backend: A Node and Python server handle the logic, managing the session state between the form and the pre-check results.

Validation Logic: We implemented specific algorithms to handle German naming conventions and Munich-specific income thresholds.

## Challenges we ran into
Document Variety: Real-world documents are messy. Handling different layouts of German Gehaltsabrechnungen (salary slips) and varying image qualities (scans vs. phone photos) was difficult for the OCR.

Hallucinations vs. Accuracy: Adjusting the "temperature" of the AI models was crucial. We needed the AI to be conservative, it is better to flag a potential error than to let a wrong application slip through.

Privacy Concerns: ensuring that we treated the data securely during the hackathon, even though we were using mock data for the demo.

## Accomplishments that we're proud of
UX Flow: Creating a UI that feels like a part of the official munich websites. 

Societal Impact: Building something that doesn't just look cool, but addresses a very real, very current bureaucratic bottleneck in Germany.

## What we learned
Bureaucracy is Logic: We learned that bureaucratic rules, while complex, are actually very programmable. They are essentially a series of giant if/else statements that AI is surprisingly good at navigating.

The Power of Feedback: We realized that the value isn't just in the checking, but in when the checking happens. Moving the validation to the user side empowers the applicant.

## What's next for BecomingMünchner
Multi-Language Support: Adding explanations in English, Turkish, Arabic, and Ukrainian to help applicants who are still learning German understand why their document was flagged.

Deeper Legal Checks: Integrating checks for residence history (calculating exact days spent in Germany).
