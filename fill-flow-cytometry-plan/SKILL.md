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
- `intended_use_statement` — full §2 statement (also used in cover page summary)
- `assay_classification` — **must be exactly one of**: Quantitative, Semi-quantitative, Qualitative
- `regulatory_tier` — **must be exactly one of**: Research, Fit-for-purpose (GCLP), CLIA LDT, IVD
- `sample_matrix` — **must be exactly one of**: Whole blood, PBMC, BM aspirate, Apheresis, CSF, Other
- `sponsor_department` — e.g. "Accendero Biosciences"
- `authors` — e.g. "Jane Smith"
- `reviewers` — e.g. "Bob Jones"
- `approvers` — e.g. "QA Director, Lab Director"
- `effective_date` — YYYY-MM-DD
- `document_version` — default "v0.1"

### §1.1 / §2.1 Intended use details (`intended_use` object — optional; fills inline template sentences)
- `assay_name` — short name used in the §1.1 purpose sentence (defaults to `assay_name_version`)
- `action_verb` — e.g. "enumerate", "detect", "monitor" (§1.1 purpose paragraph)
- `action_verb_present` — e.g. "enumerates", "detects", "monitors" (§2.1 statement)
- `population` — e.g. "adult oncology patients" (§1.1)
- `matrix` — e.g. "cryopreserved PBMC" (§1.1; defaults to `sample_matrix`)
- `measurand` — e.g. "CD4+ T cells, CD19+ CAR-T cells, MRD blasts" (§2.1)
- `matrix_description` — e.g. "K2-EDTA whole blood" (§2.1)
- `population_description` — e.g. "adult patients receiving CAR-T therapy" (§2.1)
- `result_units` — e.g. "% of parent gate / cells per µL" (§2.1)
- `decision_use` — e.g. "primary efficacy endpoint" or "safety monitoring / patient eligibility" (§2.1)

### §2.4 Reporting endpoints (`reporting` object — optional)
- `primary_results` — e.g. "% CD4+ of CD3+, absolute count per µL"
- `precision` — e.g. "one decimal place; two significant figures"
- `decision_thresholds` — e.g. "≥10 CAR-T/µL = engraftment; MRD ≥0.01% = positive"
- `turnaround_time` — e.g. "result reported within 24 h of collection"

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

### §3.4 Software systems (`software_systems` object — optional)
Seven sub-objects, each with the fields shown:

| Key | Rows filled | Fields |
|-----|-------------|--------|
| `acquisition` | Cytometer acquisition software | `vendor_version`, `qualification`, `part11_features`, `doc_id` |
| `analysis` | Analysis software (FlowJo etc.) | `vendor_version`, `validation_status`, `part11_features`, `doc_id` |
| `lims` | LIMS / data management | `vendor_version`, `validation_status`, `part11_features`, `doc_id` |
| `fcs_storage` | FCS file archive system | `system_version`, `location`, `integrity_features`, `doc_id` |
| `eln` | Electronic lab notebook | `vendor_version`, `validation_status`, `part11_features`, `doc_id` |
| `sample_manifest` | Sample manifest / chain-of-custody | `vendor_version`, `validation_status`, `part11_features`, `doc_id` |
| (top-level) | Pre-analytical handling SOP | `pre_analytical_sop` |

Examples:
- `acquisition.vendor_version`: "BD FACSDiva 9.0"
- `acquisition.qualification`: "IQ/OQ/PQ complete; 2024-01-15"
- `acquisition.part11_features`: "Audit trail / e-signature / access control"
- `fcs_storage.system_version`: "LabArchives v4.2"
- `fcs_storage.location`: "Validated network share \\server\fcs"
- `pre_analytical_sop`: "SOP-PRE-001"

### §5.2 Accuracy
`accuracy_specimen_count` — integer, ≥ 20 (CLSI H62)

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

### §6.5 Data records table (`data_records` object — optional)
Eight sub-objects, one per row. Each has: `system`, `duration`, `audit_trail`, `sop_id`.

| Key | Record type |
|-----|-------------|
| `raw_fcs_files` | Raw FCS files |
| `analysis_workspaces` | Analysis workspaces / templates |
| `gating_audit` | Gating audit / reviewer concordance |
| `reportable_results` | Reportable results / case report forms |
| `instrument_qc` | Instrument QC records |
| `reagent_lot_qual` | Reagent lot qualification records |
| `deviation_capa` | Deviation / CAPA records |
| `training_competency` | Training / competency records |

Example for `raw_fcs_files`:
```json
"raw_fcs_files": {
  "system": "\\\\fileserver\\fcs_archive",
  "duration": "≥15 years (GCLP)",
  "audit_trail": "Yes – versioned storage",
  "sop_id": "SOP-DM-001"
}
```

### §6.5 Retention paragraph (`data_retention` object — optional)
- `fcs_retention_period` — e.g. "15 years"
- `fcs_storage_location` — e.g. "validated network archive"
- `chain_of_custody_owner` — e.g. "Lab Director"

### §7 QC SOP references (`qc_sops` object — optional)
Fields map to specific table rows. All are SOP ID strings unless noted.

**§7.1 Instrument QC:**
- `instrument_cst` — CS&T / setup beads SOP ID
- `instrument_levey_jennings_westgard` — Westgard rule specification (text, not SOP)
- `instrument_levey_jennings` — Levey-Jennings tracking SOP ID
- `instrument_laser_fluidic` — Laser/fluidic check SOP ID

**§7.2 Assay-level QC:**
- `assay_reference_pbmc` — Reference PBMC (mid-level) SOP ID
- `assay_reference_pbmc_lloq` — Reference PBMC (near-LLOQ) SOP ID
- `assay_rare_antigen` — Rare-antigen control SOP ID
- `assay_compensation` — Compensation/unmixing verification SOP ID

**§7.3 Reagent lot qualification:**
- `reagent_antibody_bridging` — Antibody lot bridging SOP ID
- `reagent_tandem_dye` — Tandem dye degradation check SOP ID
- `reagent_viability_acceptance` — Acceptance criteria text (e.g. "≥70% viability")
- `reagent_viability_fixation` — Viability/fixation qualification SOP ID

**§7.4 External quality assessment / proficiency testing:**
- `eqa_scheme` — e.g. "CAP FL / UK NEQAS LI"
- `eqa_frequency` — e.g. "Biannual per CLIA"
- `eqa_enrollment_id` — e.g. "CAP-12345; SOP-EQA-001"
- `eqa_alternative_plan` — e.g. "Inter-lab comparison / split-sample plan"
- `eqa_alternative_sop` — SOP ID for alternative assessment

**§7.5 Personnel:**
- `personnel_training_sop` — Training SOP / record ID
- `personnel_competency_sop` — Competency SOP / record ID

**§7.6 Change control (5 SOPs consumed in document order):**
- `change_control_clone` — Antibody clone change SOP ID
- `change_control_fluorochrome` — Fluorochrome/panel change SOP ID
- `change_control_buffer` — Buffer/kit change SOP ID
- `change_control_instrument` — Instrument model change SOP ID
- `change_control_software` — Software/gating change SOP ID
- `transfer_plan_id` — New-site transfer plan ID

### §8.3 Approvals (`approvals` object — optional but recommended)
Each role: `{name, date}` (date in YYYY-MM-DD; signature is left blank)
- `author`, `lab_director`, `medical_director`, `quality_assurance`, `sponsor_rep`

### §9.1 Risk ratings (`risks` array — 9 entries matching template order)
Order: post_thaw_viability, post_thaw_recovery, poisson_floor, tandem_dye,
cytometer_drift, reference_pbmc_lot, analyst_drift, software_update, pt_eqa
Each entry: `{likelihood: L/M/H, impact: L/M/H}`

### §9.1 Risk SOP IDs (`risk_sops` object — optional)
Named SOP/plan IDs for the mitigations column of each risk row:
- `thaw_sop` — Post-thaw viability mitigation SOP
- `validation_report_sop` — Validation report / SOP ID
- `reagent_qc_sop` — Reagent QC SOP ID
- `daily_qc_sop` — Daily QC SOP ID
- `reference_material_sop` — Reference material SOP ID
- `competency_sop` — Competency SOP ID
- `change_control_sop` — Change control SOP ID
- `capa_sop` — CAPA SOP ID
- `pre_analytical_plan_id` — Pre-analytical handling plan ID (also fills §7.6)

### Numeric acceptance thresholds (`thresholds` object — optional)
The template uses `[X]`, `[Y]`, and `[N]` as generic numeric placeholders in
descriptive text throughout §4–§7 and §9. Provide these once and they fill
everywhere:

- `tolerance_pct` — integer or decimal; fills all `[X]` positions (default: `"20"`)
  Used for: cocktail ±X%, cross-cytometer ±X%, linearity ±X%, stability ±X%,
  carryover ≤X%, ref-PBMC QC ±X%, antibody bridging ±X%, tandem dye ±X%,
  software concordance ≥X%, accuracy intercept ±X
- `accuracy_bias_pct` — fills the single `[Y]` position in §5.2 accuracy metric (default: `"10"`)
  Used for: "bias ≤Y% at decision threshold"
- `reference_pbmc_reserve_vials` — fills the single `[N]` in §9.1 PBMC risk row (default: `"10"`)
  Used for: "Maintain ≥N vials reserve"

Example:
```json
"thresholds": {
  "tolerance_pct": "20",
  "accuracy_bias_pct": "10",
  "reference_pbmc_reserve_vials": "15"
}
```

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
  "intended_use": {
    "assay_name": "CD4/CD8 Panel",
    "action_verb": "enumerate",
    "action_verb_present": "enumerates",
    "population": "adult oncology patients",
    "matrix": "cryopreserved PBMC",
    "measurand": "CD4+ and CD8+ T cells",
    "matrix_description": "cryopreserved PBMC (K2-EDTA whole blood source)",
    "population_description": "adult patients enrolled in protocol PROT-2024-001",
    "result_units": "% of CD3+ parent gate and absolute cells per µL",
    "decision_use": "secondary efficacy endpoint"
  },
  "reporting": {
    "primary_results": "% CD4+ of CD3+, % CD8+ of CD3+, absolute count per µL",
    "precision": "one decimal place",
    "decision_thresholds": "CD4 < 200 cells/µL = immunosuppression flag",
    "turnaround_time": "result reported within 24 h of collection"
  },
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
  "software_systems": {
    "acquisition": {
      "vendor_version": "BD FACSDiva 9.0",
      "qualification": "IQ/OQ/PQ complete; 2024-01-15",
      "part11_features": "Audit trail / e-signature / access control",
      "doc_id": "SOP-SW-001"
    },
    "analysis": {
      "vendor_version": "FlowJo v10.9",
      "validation_status": "Validated",
      "part11_features": "Audit trail / version lock",
      "doc_id": "SOP-SW-002"
    },
    "lims": {
      "vendor_version": "LabVantage 8.7",
      "validation_status": "Validated (CSV-0012)",
      "part11_features": "Access control / audit / e-sig",
      "doc_id": "CSV-0012"
    },
    "fcs_storage": {
      "system_version": "Network archive v2",
      "location": "Validated network share",
      "integrity_features": "Integrity check / 15-year retention",
      "doc_id": "SOP-DM-001"
    },
    "eln": {
      "vendor_version": "LabArchives v4.2",
      "validation_status": "Qualified",
      "part11_features": "Audit trail / e-sig",
      "doc_id": "SOP-ELN-001"
    },
    "sample_manifest": {
      "vendor_version": "In-house Excel v3",
      "validation_status": "Qualified",
      "part11_features": "Audit trail",
      "doc_id": "SOP-SM-001"
    },
    "pre_analytical_sop": "SOP-PRE-001"
  },
  "data_records": {
    "raw_fcs_files": {
      "system": "\\\\fileserver\\fcs_archive",
      "duration": "≥15 years (GCLP)",
      "audit_trail": "Yes – versioned storage",
      "sop_id": "SOP-DM-001"
    },
    "analysis_workspaces": {
      "system": "FlowJo v10.9",
      "duration": "≥15 years",
      "audit_trail": "Yes – FlowJo audit log",
      "sop_id": "SOP-DM-002"
    },
    "gating_audit": {
      "system": "LIMS",
      "duration": "≥15 years",
      "audit_trail": "Yes – LIMS",
      "sop_id": "SOP-QC-005"
    },
    "reportable_results": {
      "system": "LIMS / eCRF",
      "duration": "Per sponsor",
      "audit_trail": "Yes – LIMS",
      "sop_id": "SOP-DM-003"
    },
    "instrument_qc": {
      "system": "LIMS",
      "duration": "≥15 years",
      "audit_trail": "Yes – LIMS",
      "sop_id": "SOP-QC-001"
    },
    "reagent_lot_qual": {
      "system": "LIMS",
      "duration": "≥15 years",
      "audit_trail": "Yes – LIMS",
      "sop_id": "SOP-QC-002"
    },
    "deviation_capa": {
      "system": "QMS",
      "duration": "≥15 years",
      "audit_trail": "Yes – QMS",
      "sop_id": "SOP-DEV-001"
    },
    "training_competency": {
      "system": "HR / LMS",
      "duration": "Employment + 5 years",
      "audit_trail": "Yes – LMS",
      "sop_id": "SOP-HR-001"
    }
  },
  "data_retention": {
    "fcs_retention_period": "15 years",
    "fcs_storage_location": "validated network archive",
    "chain_of_custody_owner": "Lab Director"
  },
  "qc_sops": {
    "instrument_cst": "SOP-QC-010",
    "instrument_levey_jennings_westgard": "13s/22s/R4s",
    "instrument_levey_jennings": "SOP-QC-011",
    "instrument_laser_fluidic": "SOP-QC-012",
    "assay_reference_pbmc": "SOP-QC-020",
    "assay_reference_pbmc_lloq": "SOP-QC-021",
    "assay_rare_antigen": "SOP-QC-022",
    "assay_compensation": "SOP-QC-023",
    "reagent_antibody_bridging": "SOP-QC-030",
    "reagent_tandem_dye": "SOP-QC-031",
    "reagent_viability_acceptance": "≥70% viability post-thaw",
    "reagent_viability_fixation": "SOP-QC-032",
    "eqa_scheme": "CAP FL",
    "eqa_frequency": "Biannual per CLIA",
    "eqa_enrollment_id": "CAP-12345; SOP-EQA-001",
    "eqa_alternative_plan": "Inter-lab split-sample comparison",
    "eqa_alternative_sop": "SOP-EQA-002",
    "personnel_training_sop": "SOP-HR-010",
    "personnel_competency_sop": "SOP-HR-011",
    "change_control_clone": "SOP-CC-001",
    "change_control_fluorochrome": "SOP-CC-001",
    "change_control_buffer": "SOP-CC-001",
    "change_control_instrument": "SOP-CC-001",
    "change_control_software": "SOP-CC-001",
    "transfer_plan_id": "TP-2024-001"
  },
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
  "risk_sops": {
    "thaw_sop": "SOP-PRE-002",
    "validation_report_sop": "VAL-2024-001",
    "reagent_qc_sop": "SOP-QC-030",
    "daily_qc_sop": "SOP-QC-010",
    "reference_material_sop": "SOP-QC-020",
    "competency_sop": "SOP-HR-011",
    "change_control_sop": "SOP-CC-001",
    "capa_sop": "SOP-DEV-002",
    "pre_analytical_plan_id": "TP-2024-001"
  },
  "deviation_sop_id": "SOP-DEV-001",
  "thresholds": {
    "tolerance_pct": "20",
    "accuracy_bias_pct": "10",
    "reference_pbmc_reserve_vials": "10"
  }
}
```
