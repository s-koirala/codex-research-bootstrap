---
title: Data Use Agreement — <<DATASET_NAME>>
date: <<DATE>>
type: dua
dataset: <<DATASET_NAME>>
provider: <<DATA_PROVIDER>>
recipient: <<RECIPIENT>>
effective_date: <<EFFECTIVE_DATE>>
expiration_date: <<EXPIRATION_DATE>>
---

# Data Use Agreement — <<DATASET_NAME>>

## 1. Parties

- **Provider:** <<DATA_PROVIDER>> (custodian)
- **Recipient:** <<RECIPIENT>>
- **Effective period:** <<EFFECTIVE_DATE>> to <<EXPIRATION_DATE>>

## 2. Dataset description

<<TODO: 1-paragraph description. Identify the dataset by:
- Title
- Version / snapshot date
- Approximate size (rows, columns)
- Sensitivity classification (e.g., HIPAA Limited Data Set, fully de-identified, identified PHI)>>

Per HIPAA Safe Harbor §164.514(b)(2)(i), the dataset's status with respect to the 18 identifier categories must be declared:

| # | Identifier category | Present? | Treatment |
|---|---|---|---|
| 1 | Names | <<Y/N>> | <<removed / hashed / retained>> |
| 2 | Geographic subdivisions < state (ZIP > 3 digits, city, county, precinct) | <<Y/N>> | <<>> |
| 3 | Dates (except year) | <<Y/N>> | <<offset / year-only / retained>> |
| 4 | Phone numbers | <<Y/N>> | <<>> |
| 5 | Fax numbers | <<Y/N>> | <<>> |
| 6 | Email addresses | <<Y/N>> | <<>> |
| 7 | Social Security Numbers | <<Y/N>> | <<>> |
| 8 | Medical record numbers | <<Y/N>> | <<>> |
| 9 | Health plan beneficiary numbers | <<Y/N>> | <<>> |
| 10 | Account numbers | <<Y/N>> | <<>> |
| 11 | Certificate / license numbers | <<Y/N>> | <<>> |
| 12 | Vehicle identifiers (license plate, VIN) | <<Y/N>> | <<>> |
| 13 | Device identifiers (serial number, IMEI) | <<Y/N>> | <<>> |
| 14 | URLs | <<Y/N>> | <<>> |
| 15 | IP addresses | <<Y/N>> | <<>> |
| 16 | Biometric identifiers | <<Y/N>> | <<>> |
| 17 | Full-face photos | <<Y/N>> | <<>> |
| 18 | Any other unique identifying number / characteristic | <<Y/N>> | <<>> |

## 3. Permitted uses

<<TODO: enumerate specific permitted research activities>>

## 4. Prohibited uses

- Re-identification of any individual.
- Linkage with any other dataset that could enable re-identification.
- Disclosure to any party not listed in §1.
- Commercial use beyond what is specified in the DUA.

## 5. Security safeguards

Per 45 CFR §46.111 [^1] (Criteria for IRB approval) and HIPAA Security Rule:

- [ ] Data stored only under the project's `data/` directory; never copied elsewhere.
- [ ] Project-level `pre_write_phi_guard.py` hook blocks writes containing HIPAA Safe Harbor 18 identifiers.
- [ ] Project's `.gitignore` excludes `data/raw/`, `data/interim/`, `data/processed/` from commit.
- [ ] Data manifest (`data/_manifest.json` per the data-manifest schema) records SHA-256 + license per file.

## 6. IRB approval

- IRB protocol number: <<IRB_NUMBER>>
- IRB body: <<IRB_NAME>>
- Approval date: <<APPROVAL_DATE>>
- Expiration date: <<APPROVAL_EXPIRY>>
- Renewal procedure: <<TODO>>

## 7. Retention and destruction

- Retention period: <<RETENTION_PERIOD>>
- Destruction method on expiration: <<METHOD>>
- Destruction verification: <<who certifies, by when>>

## 8. Incident reporting

In the event of a suspected or actual disclosure outside the permitted scope:

1. Cease processing immediately.
2. Notify the data steward (`<<STEWARD_EMAIL>>`) within 24 hours.
3. Document the incident in `logs/compliance/incident_<YYYY-MM-DD>.md` (separate from project audit trail).
4. Follow up per the IRB's incident-reporting procedure.

## 9. Signatures

<<TODO: digital or wet-ink signatures from provider + recipient>>

## References

[^1]: 45 CFR §46.111 — Criteria for IRB approval of research. https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-A/part-46/subpart-A/section-46.111
[^2]: HHS HIPAA Safe Harbor §164.514(b)(2). https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html
