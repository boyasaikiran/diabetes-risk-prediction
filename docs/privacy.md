# Privacy

- No names, IDs, emails or contact details are requested.
- Inputs are processed in the app's server process only; nothing is sent to third-party services. (Dataset download from OpenML happens at training time and sends no user data.)
- No database. Prediction history lives in Streamlit session memory and disappears when the session ends; "Clear history" deletes it earlier.
- Reports are built in memory and delivered to the user's browser; nothing is written to server disk.
- Logs record event types and exception class names, not health values.
- When hosted on a shared platform, the host's infrastructure still handles the HTTP traffic; deploy only on infrastructure you trust and use HTTPS.
- If persistent storage is added later it must be opt-in, minimal, deletable and access-controlled; document retention first.
- No claim of HIPAA/GDPR or other regulatory compliance is made; that needs a proper legal and technical assessment.
- Do not enter real patient data in public demos.
