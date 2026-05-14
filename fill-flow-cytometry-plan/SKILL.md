---
name: fill-flow-cytometry-plan
description: >
  Fills out a Flow Cytometry Experimental Plan DOCX template with the user's
  assay data, validation parameters, and approval information. Use this skill
  whenever someone wants to fill out, complete, populate, or generate a flow
  cytometry experimental plan — whether they call it an "FC plan", "flow cyto
  template", "assay validation plan", "fit-for-purpose plan", or any similar
  phrase. Also trigger when someone provides flow cytometry assay details and
  asks you to "put them in the template", "write up the plan", or "create the
  document". The skill enforces section-specific validation (antibody panel
  completeness, viability constraints, date formats, L/M/H risk ratings) and
  computes ALL statistics (CV%, LOB/LOD/LOQ, linearity regression) in Python
  code — never by the LLM. The output is a ready-to-use filled DOCX.
---

# Fill Flow Cytometry Experimental Plan

You fill out the Flow Cytometry Experimental Plan template by:
1. Collecting the user's data
2. Writing it to a JSON file
3. Running `calc_stats.py` to validate and compute all statistics
4. Running `fill_template.py` to produce the filled DOCX

The template is at:
`C:\Users\AlanBarber\Downloads\flow_cytometry_experimental_plan_template.docx`

Both scripts are in the `scripts/` directory next to this SKILL.md.

---

## Critical rule: no LLM arithmetic

Every numeric result that appears in the document — CV%, LOB, LOD, LOQ,
regression slope, R², Poisson CV — must come from the Python scripts, not
from your own calculation. If you catch yourself computing a percentage or
mean in your head, stop and put the numbers into the JSON for the script to
handle.

---

## Step 1 — Collect data

If the user has not supplied their data up front, ask for it section by
section. Use the structure below as your checklist. Mark fields optional
where noted; required fields must be non-empty before you proceed.

### Cover page (all required)
- `study_protocol_number` — e.g. "PROT-2024-001"
- `assay_name_version` — e.g. "CD4/CD8 T-cell Panel v1.0"
- `intended_use_statement` — full §2 statement
- `assay_classification` — **must be exactly one of**: Quantitative, Semi-quantitative, Qualitative
- `regulatory_tier` — **must be exactly one of**: Research, Fit-for-purpose (GCLP), CLIA LDT, IVD
- `sample_matrix` — **must be exactly one of**: Whole blood, PBMC, BM aspirate, Apheresis, CSF, Other
- `sponsor_department` — e.g. "Accendero Biosciences"
- `authors` — e.g. "Jane Smith"
- `reviewers` — e.g. "Bob Jones"
- `approvers` — e.g. "QA Director, Lab Director"
- `effective_date` — YYYY-MM-DD
- `document_version` — default "v0.1"

### §3.1 PBMC specimen specs (`pbmc_specs` object — all required)
- `isolation_method` — e.g. "Ficoll-Paque density gradient"
- `cryopreservation_medium` — e.g. "90% FBS / 10% DMSO"
- `container_type` — e.g. "2 mL cryovial"
- `min_cells_at_freeze` — e.g. "≥ 5 × 10⁶ viable cells per vial"
- `min_viability_at_freeze` — numeric %, 0–100
- `min_viability_post_thaw` — numeric %, must be ≤ freeze viability
- `min_recovery_post_thaw` — numeric %, 0–100

### §3.2 Antibody panel (`antibodies` array — at least 1 row required)
Each entry:
- `marker` — e.g. "CD3"
- `fluorochrome` — e.g. "FITC"
- `clone` — e.g. "OKT3"
- `vendor_cat` — e.g. "BioLegend 300406"
- `lot` — e.g. "B12345"
- `volume_dilution` — e.g. "5 µL/test"

### §4.6 Cytometers (`cytometers` array — at least 1 required)
Each entry:
- `make_model_serial` — e.g. "BD FACSCanto II / SN-12345"
- `site_location` — e.g. "Building A, Room 201"
- `qualification_status` — e.g. "IQ ✓ / OQ ✓ / PQ ✓"
- `last_pq_date` — YYYY-MM-DD
- `reference_docs` — e.g. "IQ-001; OQ-002; PQ-003"

`bridging_study_report_id` — string (optional; e.g. "BSR-2024-01")

### §5.2 Accuracy (`accuracy_specimen_count` — integer)
For the acceptance criteria table entry. The script validates ≥ 20.

### §5.3 Precision (optional — provide if you have replicate data)
`precision.intra_assay.low/mid/high` — arrays of floats (≥ 10 each)
`precision.inter_assay.low/mid/high` — arrays of floats

### §5.4 Sensitivity / LOB / LOD / LOQ (optional)
`sensitivity`:
- `blank_measurements` — list of ≥ 60 floats (analyte-negative samples)
- `low_level_measurements` — list of floats (near-LOB spike/admix)
- `lloq_spike_levels` — list of `{concentration, replicates: [floats], assigned_value}`
- `lloq_cv_threshold_pct` — number (e.g. 30)
- `lloq_bias_threshold_pct` — number (e.g. 30)
- `minimum_events_required` — integer (for Poisson CV — optional)

### §5.6 Linearity (optional)
`linearity.levels` — list of `{concentration, replicates: [≥3 floats]}`
(need ≥ 5 levels)

### §5.11 Acceptance criteria (`acceptance_criteria` object)
Free-text fields for each parameter. If left empty, the script auto-fills
them with the computed values from §5.3/5.4/5.6.
- `accuracy`, `repeatability`, `repeatability_target`, `intermediate_precision`,
  `precision_target`, `lob_lod_loq`, `specificity`, `linearity_amr`,
  `robustness`, `stability`, `carryover`

### §8.3 Approvals (`approvals` object — optional but recommended)
Each role: `{name, date}` (date in YYYY-MM-DD; signature is left blank)
- `author`, `lab_director`, `medical_director`, `quality_assurance`, `sponsor_rep`

### §9.1 Risk ratings (`risks` array — 9 entries matching template order)
Order: post_thaw_viability, post_thaw_recovery, poisson_floor, tandem_dye,
cytometer_drift, reference_pbmc_lot, analyst_drift, software_update, pt_eqa
Each entry: `{likelihood: L/M/H, impact: L/M/H}`

### §9.2 Deviation SOP
`deviation_sop_id` — e.g. "SOP-DEV-001"

### Output path
Ask for the desired output file path, or default to:
`C:\Users\AlanBarber\Downloads\<study_protocol_number>_fc_plan_filled.docx`

---

## Step 2 — Write the input JSON

Once you have all required fields, write them to a temp file, e.g.:
`C:\Users\AlanBarber\Downloads\fc_plan_input.json`

---

## Step 3 — Run calc_stats.py

```
python <skill_dir>/scripts/calc_stats.py fc_plan_input.json fc_plan_computed.json
```

- If it exits non-zero, parse the validation/computation errors from stderr
  and report them to the user. Fix the JSON and retry.
- On success, `fc_plan_computed.json` contains all validated data plus
  computed statistics embedded under `_computed`.

---

## Step 4 — Run fill_template.py

```
python <skill_dir>/scripts/fill_template.py \
  fc_plan_computed.json \
  "C:\Users\AlanBarber\Downloads\flow_cytometry_experimental_plan_template.docx" \
  "<output_path>"
```

`<skill_dir>` is the directory containing this SKILL.md file.

---

## Step 5 — Report to user

Tell the user:
- The output file path
- Any computed values worth calling out (e.g. "LOB = 0.0023, LOD = 0.0051,
  LOQ = 0.01; intra-assay CV: low 8.3%, mid 5.1%, high 4.9%")
- Any fields that were left at their template defaults (so the user knows
  what still needs manual attention)

---

## Validation quick-reference

| Field | Rule |
|---|---|
| assay_classification | Exactly: Quantitative, Semi-quantitative, or Qualitative |
| regulatory_tier | Exactly: Research, Fit-for-purpose (GCLP), CLIA LDT, or IVD |
| sample_matrix | Exactly: Whole blood, PBMC, BM aspirate, Apheresis, CSF, or Other |
| effective_date / pq_date / approval dates | YYYY-MM-DD |
| min_viability_post_thaw | Must be ≤ min_viability_at_freeze |
| antibodies | ≥1 row; all 6 fields non-empty |
| cytometers | ≥1 row |
| blank_measurements (LOB) | ≥60 values |
| linearity levels | ≥5 levels, ≥3 replicates each |
| risk likelihood/impact | L, M, or H only |
| accuracy_specimen_count | ≥20 (CLSI H62) |

---

## Example minimal input JSON

```json
{
  "study_protocol_number": "PROT-2024-001",
  "assay_name_version": "CD4/CD8 Panel v1.0",
  "intended_use_statement": "This assay enumerates CD4+ and CD8+ T cells in cryopreserved PBMC from adult oncology patients to support secondary efficacy endpoints in protocol PROT-2024-001.",
  "assay_classification": "Semi-quantitative",
  "regulatory_tier": "Fit-for-purpose (GCLP)",
  "sample_matrix": "PBMC",
  "sponsor_department": "Accendero Biosciences",
  "authors": "Jane Smith",
  "reviewers": "Bob Jones",
  "approvers": "QA Director",
  "effective_date": "2024-06-01",
  "document_version": "v1.0",
  "pbmc_specs": {
    "isolation_method": "Ficoll-Paque density gradient",
    "cryopreservation_medium": "90% FBS / 10% DMSO",
    "container_type": "2 mL cryovial",
    "min_cells_at_freeze": "≥ 5 × 10⁶ viable cells per vial",
    "min_viability_at_freeze": 90,
    "min_viability_post_thaw": 70,
    "min_recovery_post_thaw": 50
  },
  "antibodies": [
    {"marker": "CD3",  "fluorochrome": "FITC",  "clone": "OKT3",  "vendor_cat": "BioLegend 300406", "lot": "B12345", "volume_dilution": "5 µL/test"},
    {"marker": "CD4",  "fluorochrome": "PE",    "clone": "RPA-T4","vendor_cat": "BioLegend 300507", "lot": "B23456", "volume_dilution": "5 µL/test"},
    {"marker": "CD8",  "fluorochrome": "APC",   "clone": "SK1",   "vendor_cat": "BioLegend 344721", "lot": "B34567", "volume_dilution": "5 µL/test"},
    {"marker": "CD45", "fluorochrome": "BV421", "clone": "2B11",  "vendor_cat": "BioLegend 304032", "lot": "B45678", "volume_dilution": "3 µL/test"},
    {"marker": "Viability", "fluorochrome": "7-AAD", "clone": "N/A", "vendor_cat": "BioLegend 420403", "lot": "B56789", "volume_dilution": "2 µL/test"}
  ],
  "cytometers": [
    {
      "make_model_serial": "BD FACSCanto II / SN-12345",
      "site_location": "Building A, Room 201",
      "qualification_status": "IQ ✓ / OQ ✓ / PQ ✓",
      "last_pq_date": "2024-03-15",
      "reference_docs": "IQ-001; OQ-002; PQ-003"
    }
  ],
  "bridging_study_report_id": "",
  "acceptance_criteria": {
    "accuracy": "Slope 0.9–1.1, bias ≤10% at decision threshold",
    "specificity": "No cross-reactivity observed"
  },
  "approvals": {
    "author": {"name": "Jane Smith", "date": "2024-06-01"},
    "lab_director": {"name": "Dr. R. Lee", "date": "2024-06-03"},
    "quality_assurance": {"name": "QA Team", "date": "2024-06-05"}
  },
  "risks": [
    {"likelihood": "M", "impact": "H"},
    {"likelihood": "M", "impact": "M"},
    {"likelihood": "L", "impact": "M"},
    {"likelihood": "M", "impact": "M"},
    {"likelihood": "L", "impact": "M"},
    {"likelihood": "L", "impact": "H"},
    {"likelihood": "M", "impact": "M"},
    {"likelihood": "L", "impact": "M"},
    {"likelihood": "L", "impact": "H"}
  ],
  "deviation_sop_id": "SOP-DEV-001"
}
```
