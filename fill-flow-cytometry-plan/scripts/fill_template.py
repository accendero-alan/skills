#!/usr/bin/env python3
"""
Fill the Flow Cytometry Experimental Plan template DOCX.

Usage:
    python fill_template.py <data.json> <template.docx> <output.docx>

The data.json must be produced by calc_stats.py (which validates fields and
computes all statistical values). This script only handles XML manipulation.

Covers ALL 92 unique placeholder token types across the template:
  Cover page, §1.1 purpose paragraph, §2.1 intended-use statement,
  §2.4 reporting endpoints, §3.1 PBMC specs, §3.2 antibody panel,
  §3.4 software systems, §4.6 cytometers, §5.11 acceptance criteria,
  §6.5 data records table + retention paragraph, §7.1-7.6 QC SOP tables,
  §8.3 approvals, §9.1 risks (L/M/H + unique SOPs), §9.2 deviations.
  Includes [X] tolerance %, [Y] bias %, [N] reserve-vial count tokens.
"""
import json
import re
import sys
import zipfile
from pathlib import Path


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def xe(s):
    """Escape a value for insertion into XML text content."""
    s = str(s) if s is not None else ""
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    return s


def make_cell(text, width):
    """Generate a table cell XML matching the template's formatting style."""
    return (
        f'<w:tc>\n'
        f'          <w:tcPr>\n'
        f'            <w:tcW w:type="dxa" w:w="{width}"/>\n'
        f'            <w:tcBorders>\n'
        f'              <w:top w:val="single" w:color="BFBFBF" w:sz="4"/>\n'
        f'              <w:left w:val="single" w:color="BFBFBF" w:sz="4"/>\n'
        f'              <w:bottom w:val="single" w:color="BFBFBF" w:sz="4"/>\n'
        f'              <w:right w:val="single" w:color="BFBFBF" w:sz="4"/>\n'
        f'            </w:tcBorders>\n'
        f'            <w:tcMar>\n'
        f'              <w:top w:type="dxa" w:w="100"/>\n'
        f'              <w:left w:type="dxa" w:w="140"/>\n'
        f'              <w:bottom w:type="dxa" w:w="100"/>\n'
        f'              <w:right w:type="dxa" w:w="140"/>\n'
        f'            </w:tcMar>\n'
        f'          </w:tcPr>\n'
        f'          <w:p>\n'
        f'            <w:pPr>\n'
        f'              <w:spacing w:after="40" w:line="280"/>\n'
        f'            </w:pPr>\n'
        f'            <w:r>\n'
        f'              <w:rPr>\n'
        f'                <w:b w:val="false"/>\n'
        f'                <w:bCs w:val="false"/>\n'
        f'                <w:sz w:val="20"/>\n'
        f'                <w:szCs w:val="20"/>\n'
        f'              </w:rPr>\n'
        f'              <w:t xml:space="preserve">{xe(text)}</w:t>\n'
        f'            </w:r>\n'
        f'          </w:p>\n'
        f'        </w:tc>'
    )


def make_antibody_row(n, marker, fluorochrome, clone, vendor_cat, lot, volume):
    """Generate one antibody panel table row."""
    cells = (
        make_cell(n,           600)  + "\n        " +
        make_cell(marker,      1400) + "\n        " +
        make_cell(fluorochrome,1400) + "\n        " +
        make_cell(clone,       1500) + "\n        " +
        make_cell(vendor_cat,  1300) + "\n        " +
        make_cell(lot,         1300) + "\n        " +
        make_cell(volume,      1860)
    )
    return f"<w:tr>\n        {cells}\n      </w:tr>"


# ---------------------------------------------------------------------------
# nth-occurrence replacement (used for [Enter] tokens)
# ---------------------------------------------------------------------------

def nth_replace(text, old, new, n):
    """Replace only the nth occurrence of 'old' with 'new'. Returns unchanged
    text if there are fewer than n occurrences."""
    pos = 0
    count = 0
    while True:
        pos = text.find(old, pos)
        if pos == -1:
            return text
        count += 1
        if count == n:
            return text[:pos] + new + text[pos + len(old):]
        pos += len(old)


# ---------------------------------------------------------------------------
# Row-level helper for the approvals table
# ---------------------------------------------------------------------------

def fill_approval_row(xml, role_text, name, date):
    """
    Find the <w:tr> that contains role_text, then replace the two empty
    <w:t xml:space="preserve"/> runs (Name and Date cells) with real values.
    Signature cell is left blank for manual signing.
    """
    # Find the row that has this exact role
    pattern = re.compile(
        r'(<w:tr>(?:(?!<w:tr>).)*?' +
        re.escape(f'<w:t xml:space="preserve">{role_text}</w:t>') +
        r'.*?</w:tr>)',
        re.DOTALL
    )
    m = pattern.search(xml)
    if not m:
        return xml  # role not found – skip silently

    row_xml = m.group(1)

    # Within the row, replace the 1st empty <w:t.../> with the name
    # and the 3rd empty <w:t.../> with the date (2nd is signature – skip)
    # The original DOCX stores empty cells as open/close <w:t></w:t>, not self-closing
    empty_t = '<w:t xml:space="preserve"></w:t>'

    def fill_nth_empty(row, n, value):
        return nth_replace(row, empty_t,
                           f'<w:t xml:space="preserve">{xe(value)}</w:t>', n)

    new_row = fill_nth_empty(row_xml, 1, name)   # Name cell (1st empty)
    # Signature (was 2nd, now 1st remaining) stays empty — for manual signing
    new_row = fill_nth_empty(new_row, 2, date)   # Date cell (was 3rd, now 2nd remaining)

    return xml[:m.start()] + new_row + xml[m.end():]


# ---------------------------------------------------------------------------
# Main fill function
# ---------------------------------------------------------------------------

def fill(data: dict, template_path: str, output_path: str):
    # Read template DOCX (zip) into memory
    with zipfile.ZipFile(template_path, "r") as zin:
        file_map = {name: zin.read(name) for name in zin.namelist()}

    doc = file_map["word/document.xml"].decode("utf-8")

    # -----------------------------------------------------------------------
    # §1 COVER PAGE
    # [Enter] positions 1-7 (document order):
    #   1=Study/Protocol Number  2=Assay Name/Version  3=Sponsor/Department
    #   4=Authors  5=Reviewers  6=Approvers  7=Effective Date
    # -----------------------------------------------------------------------
    cover_fields = [
        data.get("study_protocol_number", ""),
        data.get("assay_name_version", ""),
        data.get("sponsor_department", ""),
        data.get("authors", ""),
        data.get("reviewers", ""),
        data.get("approvers", ""),
        data.get("effective_date", ""),
    ]
    for val in cover_fields:
        doc = nth_replace(doc, "[Enter]", xe(val), 1)

    # Unique cover-page placeholders
    doc = doc.replace("[Enter — see §2]",
                      xe(data.get("intended_use_statement", "")))
    doc = doc.replace("[Quantitative / Semi-quantitative / Qualitative]",
                      xe(data.get("assay_classification", "")))
    doc = doc.replace("[Research / Fit-for-purpose (GCLP) / CLIA LDT / IVD]",
                      xe(data.get("regulatory_tier", "")))
    doc = doc.replace("[Whole blood / PBMC / BM aspirate / Apheresis / CSF / Other]",
                      xe(data.get("sample_matrix", "")))
    doc = doc.replace("[v0.1]",
                      xe(data.get("document_version", "v0.1")))

    # -----------------------------------------------------------------------
    # §1.1 PURPOSE PARAGRAPH — inline unique tokens
    # "...for the [assay name] flow cytometry assay, to be used to
    #  [enumerate / detect / monitor] [population] in [matrix] from subjects
    #  enrolled in protocol [XXX]."
    # -----------------------------------------------------------------------
    iu = data.get("intended_use", {})
    doc = doc.replace("[assay name]",
                      xe(iu.get("assay_name",
                                data.get("assay_name_version", ""))))
    doc = doc.replace("[enumerate / detect / monitor]",
                      xe(iu.get("action_verb", "")))
    # [population] and [matrix] are 1× each in §1.1
    doc = doc.replace("[population]",
                      xe(iu.get("population", "")))
    doc = doc.replace("[matrix]",
                      xe(iu.get("matrix",
                                data.get("sample_matrix", ""))))
    doc = doc.replace("[XXX]",
                      xe(data.get("study_protocol_number", "")))

    # -----------------------------------------------------------------------
    # §2.1 INTENDED USE STATEMENT — template sentence
    # "This assay [enumerates / detects / monitors]
    #  [measurand: e.g., CD4+ T cells…] in [matrix: e.g., K2-EDTA whole blood]
    #  from [population: e.g., adult patients…].
    #  Results are reported as [units: % of parent / cells per µL…]"
    # -----------------------------------------------------------------------
    doc = doc.replace("[enumerates / detects / monitors]",
                      xe(iu.get("action_verb_present", "")))
    doc = doc.replace(
        "[measurand: e.g., CD4+ T cells, CD19+ CAR-T cells, MRD blasts]",
        xe(iu.get("measurand", "")))
    doc = doc.replace("[matrix: e.g., K2-EDTA whole blood]",
                      xe(iu.get("matrix_description", "")))
    doc = doc.replace(
        "[population: e.g., adult patients receiving X therapy]",
        xe(iu.get("population_description", "")))
    doc = doc.replace(
        "[units: % of parent / cells per µL / positive vs. negative]",
        xe(iu.get("result_units", "")))
    doc = doc.replace(
        "[decision: primary efficacy endpoint / safety monitoring / patient eligibility / dose adjustment]",
        xe(iu.get("decision_use", "")))

    # -----------------------------------------------------------------------
    # §2.4 DECISION USE AND REPORTING ENDPOINTS — inline tokens
    # -----------------------------------------------------------------------
    rep = data.get("reporting", {})
    doc = doc.replace("[e.g., % CD4+ of CD3+, absolute count per µL]",
                      xe(rep.get("primary_results", "")))
    doc = doc.replace("[e.g., one decimal place; two significant figures]",
                      xe(rep.get("precision", "")))
    doc = doc.replace(
        "[e.g., ≥10 CAR-T/µL = engraftment; MRD ≥0.01% = positive]",
        xe(rep.get("decision_thresholds", "")))
    doc = doc.replace("[e.g., result reported within 24 h of collection]",
                      xe(rep.get("turnaround_time", "")))

    # -----------------------------------------------------------------------
    # §3.1 PBMC SPECIMEN SPECS — unique placeholder per cell
    # -----------------------------------------------------------------------
    pbmc = data.get("pbmc_specs", {})
    doc = doc.replace("[Ficoll-Paque / SepMate / other — specify]",
                      xe(pbmc.get("isolation_method", "")))
    doc = doc.replace("[e.g., 90% FBS / 10% DMSO; CryoStor CS10 — specify]",
                      xe(pbmc.get("cryopreservation_medium", "")))
    doc = doc.replace("[Cryovial type, volume — specify]",
                      xe(pbmc.get("container_type", "")))
    doc = doc.replace(
        "[e.g., ≥ 5 × 10⁶ viable cells per vial — specify]",
        xe(pbmc.get("min_cells_at_freeze", "")))
    doc = doc.replace(
        "[e.g., ≥ 90% by trypan blue or AOPI — specify]",
        xe(pbmc.get("min_viability_at_freeze", "")))
    doc = doc.replace("[e.g., ≥ 70% — specify]",
                      xe(pbmc.get("min_viability_post_thaw", "")))
    doc = doc.replace(
        "[e.g., ≥ 50% of frozen cell number — specify]",
        xe(pbmc.get("min_recovery_post_thaw", "")))

    # -----------------------------------------------------------------------
    # §3.2 ANTIBODY PANEL — replace all template rows with user data
    # -----------------------------------------------------------------------
    antibodies = data.get("antibodies", [])
    if antibodies:
        first_marker_pos = doc.find("[Marker]")
        if first_marker_pos != -1:
            first_tr_start = doc.rfind("<w:tr>", 0, first_marker_pos)
            pos = first_tr_start
            for _ in range(6):
                next_end = doc.find("</w:tr>", pos)
                if next_end == -1:
                    break
                pos = next_end + len("</w:tr>")
            last_tr_end = pos
            new_rows = "\n      ".join(
                make_antibody_row(
                    i + 1,
                    ab.get("marker", ""),
                    ab.get("fluorochrome", ""),
                    ab.get("clone", ""),
                    ab.get("vendor_cat", ""),
                    ab.get("lot", ""),
                    ab.get("volume_dilution", ""),
                )
                for i, ab in enumerate(antibodies)
            )
            doc = doc[:first_tr_start] + new_rows + doc[last_tr_end:]

    # -----------------------------------------------------------------------
    # §4.6 CYTOMETER QUALIFICATION TABLE (template has 3 rows; user: 1–3)
    # One replacement per token per cytometer row — no doubling
    # -----------------------------------------------------------------------
    cytometers = data.get("cytometers", [])
    for cyt in cytometers:
        doc = nth_replace(doc, "[Make / Model / Serial]",
                          xe(cyt.get("make_model_serial", "")), 1)
        doc = nth_replace(doc, "[Site / room]",
                          xe(cyt.get("site_location", "")), 1)
        doc = nth_replace(doc, "[IQ ✓ / OQ ✓ / PQ ✓]",
                          xe(cyt.get("qualification_status", "")), 1)
        doc = nth_replace(doc, "[YYYY-MM-DD]",
                          xe(cyt.get("last_pq_date", "")), 1)
        doc = nth_replace(doc, "[IQ/OQ/PQ report ID; daily QC SOP ID]",
                          xe(cyt.get("reference_docs", "")), 1)

    # §4.6 cross-cytometer bridging bullet — [Enter] position 8
    doc = nth_replace(doc, "[Enter]",
                      xe(data.get("bridging_study_report_id", "")), 1)

    # -----------------------------------------------------------------------
    # §3.4 SOFTWARE AND DATA SYSTEMS TABLE (was §4.7 in prior template version)
    # Document order of rows: acquisition → analysis → LIMS → FCS storage →
    # ELN → sample manifest → pre-analytical
    #
    # Positional tokens consumed here (after §4.6 has consumed its share):
    #   [Vendor / version] ×5   (rows 1,2,3,5,6)
    #   [Validation status] ×3  (rows 3,5,6)
    #   [System / version]  ×1  (row 4; 2nd occurrence is in §6)
    #   [Doc ID / link]     ×6  (rows 1–6)
    #   Plus 8 unique tokens (one each)
    # -----------------------------------------------------------------------
    sw  = data.get("software_systems", {})
    acq = sw.get("acquisition",    {})
    anl = sw.get("analysis",       {})
    lim = sw.get("lims",           {})
    fcs = sw.get("fcs_storage",    {})
    eln = sw.get("eln",            {})
    smf = sw.get("sample_manifest",{})

    # Row 1 — Cytometer acquisition software
    doc = nth_replace(doc, "[Vendor / version]",
                      xe(acq.get("vendor_version", "")), 1)
    doc = doc.replace("[IQ/OQ/PQ complete; date]",
                      xe(acq.get("qualification", "")))
    doc = doc.replace("[Audit trail / e-signature / access ctrl]",
                      xe(acq.get("part11_features", "")))
    doc = nth_replace(doc, "[Doc ID / link]",
                      xe(acq.get("doc_id", "")), 1)

    # Row 2 — Analysis software
    doc = nth_replace(doc, "[Vendor / version]",
                      xe(anl.get("vendor_version", "")), 1)
    doc = doc.replace("[Validated / qualified]",
                      xe(anl.get("validation_status", "")))
    doc = doc.replace("[Audit trail / version lock]",
                      xe(anl.get("part11_features", "")))
    doc = nth_replace(doc, "[Doc ID / link]",
                      xe(anl.get("doc_id", "")), 1)

    # Row 3 — LIMS / data management
    doc = nth_replace(doc, "[Vendor / version]",
                      xe(lim.get("vendor_version", "")), 1)
    doc = nth_replace(doc, "[Validation status]",
                      xe(lim.get("validation_status", "")), 1)
    doc = doc.replace("[Access ctrl / audit / e-sig]",
                      xe(lim.get("part11_features", "")))
    doc = nth_replace(doc, "[Doc ID / link]",
                      xe(lim.get("doc_id", "")), 1)

    # Row 4 — FCS file storage / archive
    doc = nth_replace(doc, "[System / version]",
                      xe(fcs.get("system_version", "")), 1)
    doc = doc.replace("[Qualified location]",
                      xe(fcs.get("location", "")))
    doc = doc.replace("[Integrity / retention enforcement]",
                      xe(fcs.get("integrity_features", "")))
    doc = nth_replace(doc, "[Doc ID / link]",
                      xe(fcs.get("doc_id", "")), 1)

    # Row 5 — Electronic lab notebook (if used)
    doc = nth_replace(doc, "[Vendor / version]",
                      xe(eln.get("vendor_version", "")), 1)
    doc = nth_replace(doc, "[Validation status]",
                      xe(eln.get("validation_status", "")), 1)
    doc = doc.replace("[Audit trail / e-sig]",
                      xe(eln.get("part11_features", "")))
    doc = nth_replace(doc, "[Doc ID / link]",
                      xe(eln.get("doc_id", "")), 1)

    # Row 6 — Sample manifest / chain-of-custody system
    doc = nth_replace(doc, "[Vendor / version]",
                      xe(smf.get("vendor_version", "")), 1)
    doc = nth_replace(doc, "[Validation status]",
                      xe(smf.get("validation_status", "")), 1)
    doc = doc.replace("[Audit trail]",
                      xe(smf.get("part11_features", "")))
    doc = nth_replace(doc, "[Doc ID / link]",
                      xe(smf.get("doc_id", "")), 1)

    # Row 7 — Pre-analytical handling (upstream SOP reference)
    doc = doc.replace("[Pre-analytical plan / SOP ID]",
                      xe(sw.get("pre_analytical_sop", "")))

    # -----------------------------------------------------------------------
    # §5.11 ACCEPTANCE CRITERIA TABLE
    # [Enter] positions 9–16 (continuing from cover ×7 + bridging ×1):
    #   9=Accuracy  10=Repeatability  11=Intermediate precision  12=LOB/LOD/LOQ
    #   13=Specificity  14=Linearity/AMR  15=Robustness  16=Carryover
    # -----------------------------------------------------------------------
    ac = data.get("acceptance_criteria", {})
    for val in [
        ac.get("accuracy", ""),
        ac.get("repeatability", ""),
        ac.get("intermediate_precision", ""),
        ac.get("lob_lod_loq", ""),
        ac.get("specificity", ""),
        ac.get("linearity_amr", ""),
        ac.get("robustness", ""),
        ac.get("carryover", ""),
    ]:
        doc = nth_replace(doc, "[Enter]", xe(val), 1)

    doc = doc.replace("[Enter — typical ±15–20%]",
                      xe(ac.get("stability", "")))

    # -----------------------------------------------------------------------
    # §6.5 DATA MANAGEMENT — RECORDS RETENTION TABLE
    # 8 fixed rows; columns: system | retention | audit trail | SOP ref
    #
    # Positional token order (document order within §6.5):
    #   [System / location]  ×1  row 1 (unique)
    #   [Duration]           ×8  rows 1–8
    #   [Yes / system]       ×8  rows 1–8
    #   [Policy / SOP ID]    ×3  rows 1, 2, 4
    #   [System / version]   ×1  row 2 (2nd doc occurrence; 1st was §3.4)
    #   [System]             ×4  rows 3, 5, 6, 8
    #   [SOP ID]             ×3  rows 3, 5, 6  (positions 1–3 of 14 total)
    #   [LIMS / system]      ×1  row 4 (unique)
    #   [QMS]                ×1  row 7 (unique)
    #   [QMS SOP ID]         ×1  row 7 (unique)
    #   [HR / QMS SOP ID]    ×1  row 8 (unique)
    # -----------------------------------------------------------------------
    dr = data.get("data_records", {})

    def _r(key):
        return dr.get(key, {})

    r1 = _r("raw_fcs_files")
    r2 = _r("analysis_workspaces")
    r3 = _r("gating_audit")
    r4 = _r("reportable_results")
    r5 = _r("instrument_qc")
    r6 = _r("reagent_lot_qual")
    r7 = _r("deviation_capa")
    r8 = _r("training_competency")

    # Row 1 — Raw FCS files
    doc = doc.replace("[System / location]",
                      xe(r1.get("system", "")))
    doc = nth_replace(doc, "[Duration]",
                      xe(r1.get("duration", "")),     1)
    doc = nth_replace(doc, "[Yes / system]",
                      xe(r1.get("audit_trail", "")),  1)
    doc = nth_replace(doc, "[Policy / SOP ID]",
                      xe(r1.get("sop_id", "")),       1)

    # Row 2 — Analysis workspaces / templates
    doc = nth_replace(doc, "[System / version]",
                      xe(r2.get("system", "")),       1)
    doc = nth_replace(doc, "[Duration]",
                      xe(r2.get("duration", "")),     1)
    doc = nth_replace(doc, "[Yes / system]",
                      xe(r2.get("audit_trail", "")),  1)
    doc = nth_replace(doc, "[Policy / SOP ID]",
                      xe(r2.get("sop_id", "")),       1)

    # Row 3 — Gating audit (reviewer concordance)
    doc = nth_replace(doc, "[System]",
                      xe(r3.get("system", "")),       1)
    doc = nth_replace(doc, "[Duration]",
                      xe(r3.get("duration", "")),     1)
    doc = nth_replace(doc, "[Yes / system]",
                      xe(r3.get("audit_trail", "")),  1)
    doc = nth_replace(doc, "[SOP ID]",
                      xe(r3.get("sop_id", "")),       1)

    # Row 4 — Reportable results / case reports
    doc = doc.replace("[LIMS / system]",
                      xe(r4.get("system", "")))
    doc = nth_replace(doc, "[Duration]",
                      xe(r4.get("duration", "")),     1)
    doc = nth_replace(doc, "[Yes / system]",
                      xe(r4.get("audit_trail", "")),  1)
    doc = nth_replace(doc, "[Policy / SOP ID]",
                      xe(r4.get("sop_id", "")),       1)

    # Row 5 — Instrument QC records
    doc = nth_replace(doc, "[System]",
                      xe(r5.get("system", "")),       1)
    doc = nth_replace(doc, "[Duration]",
                      xe(r5.get("duration", "")),     1)
    doc = nth_replace(doc, "[Yes / system]",
                      xe(r5.get("audit_trail", "")),  1)
    doc = nth_replace(doc, "[SOP ID]",
                      xe(r5.get("sop_id", "")),       1)

    # Row 6 — Reagent lot qualification records
    doc = nth_replace(doc, "[System]",
                      xe(r6.get("system", "")),       1)
    doc = nth_replace(doc, "[Duration]",
                      xe(r6.get("duration", "")),     1)
    doc = nth_replace(doc, "[Yes / system]",
                      xe(r6.get("audit_trail", "")),  1)
    doc = nth_replace(doc, "[SOP ID]",
                      xe(r6.get("sop_id", "")),       1)

    # Row 7 — Deviation / CAPA records
    doc = doc.replace("[QMS]",
                      xe(r7.get("system", "")))
    doc = nth_replace(doc, "[Duration]",
                      xe(r7.get("duration", "")),     1)
    doc = nth_replace(doc, "[Yes / system]",
                      xe(r7.get("audit_trail", "")),  1)
    doc = doc.replace("[QMS SOP ID]",
                      xe(r7.get("sop_id", "")))

    # Row 8 — Training / competency records
    doc = nth_replace(doc, "[System]",
                      xe(r8.get("system", "")),       1)
    doc = nth_replace(doc, "[Duration]",
                      xe(r8.get("duration", "")),     1)
    doc = nth_replace(doc, "[Yes / system]",
                      xe(r8.get("audit_trail", "")),  1)
    doc = doc.replace("[HR / QMS SOP ID]",
                      xe(r8.get("sop_id", "")))

    # §6.5 retention paragraph — lowercase tokens are unique (1× each)
    dret = data.get("data_retention", {})
    doc = doc.replace("[duration]",
                      xe(dret.get("fcs_retention_period", "")))
    doc = doc.replace("[system]",
                      xe(dret.get("fcs_storage_location", "")))
    doc = doc.replace("[role]",
                      xe(dret.get("chain_of_custody_owner", "")))

    # -----------------------------------------------------------------------
    # §7 ONGOING QC — SOP REFERENCES
    # [SOP ID] positions 4–14 (positions 1–3 consumed in §6 above):
    #   4  = §7.1 Instrument: CS&T / setup beads
    #   5  = §7.1 Instrument: Levey-Jennings  (also: [specify] for rules)
    #   6  = §7.1 Instrument: laser/fluidic check
    #   7  = §7.2 Assay: reference PBMC (mid-level)
    #   8  = §7.2 Assay: reference PBMC (near-LLOQ)
    #   9  = §7.2 Assay: rare-antigen control
    #  10  = §7.2 Assay: compensation/unmixing verification
    #  11  = §7.3 Reagent: antibody lot bridging
    #  12  = §7.3 Reagent: tandem dye degradation check
    #  13  = §7.3 Reagent: viability/fixation qualification
    #  14  = §7.4 EQA: alternative assessment
    # -----------------------------------------------------------------------
    qc = data.get("qc_sops", {})

    # §7.1 Instrument QC
    doc = nth_replace(doc, "[SOP ID]",
                      xe(qc.get("instrument_cst", "")),                1)
    doc = doc.replace("[specify]",
                      xe(qc.get("instrument_levey_jennings_westgard", "")))
    doc = nth_replace(doc, "[SOP ID]",
                      xe(qc.get("instrument_levey_jennings", "")),     1)
    doc = nth_replace(doc, "[SOP ID]",
                      xe(qc.get("instrument_laser_fluidic", "")),      1)

    # §7.2 Assay-level QC
    doc = nth_replace(doc, "[SOP ID]",
                      xe(qc.get("assay_reference_pbmc", "")),          1)
    doc = nth_replace(doc, "[SOP ID]",
                      xe(qc.get("assay_reference_pbmc_lloq", "")),     1)
    doc = nth_replace(doc, "[SOP ID]",
                      xe(qc.get("assay_rare_antigen", "")),            1)
    doc = nth_replace(doc, "[SOP ID]",
                      xe(qc.get("assay_compensation", "")),            1)

    # §7.3 Reagent lot qualification
    doc = nth_replace(doc, "[SOP ID]",
                      xe(qc.get("reagent_antibody_bridging", "")),     1)
    doc = nth_replace(doc, "[SOP ID]",
                      xe(qc.get("reagent_tandem_dye", "")),            1)
    doc = doc.replace("[Defined per reagent]",
                      xe(qc.get("reagent_viability_acceptance", "")))
    doc = nth_replace(doc, "[SOP ID]",
                      xe(qc.get("reagent_viability_fixation", "")),    1)

    # §7.4 External quality assessment / proficiency testing
    doc = doc.replace("[CAP FL / UK NEQAS LI / other scheme]",
                      xe(qc.get("eqa_scheme", "")))
    doc = doc.replace("[Per scheme; biannual minimum for CLIA]",
                      xe(qc.get("eqa_frequency", "")))
    doc = doc.replace("[Enrollment ID; SOP ID]",
                      xe(qc.get("eqa_enrollment_id", "")))
    doc = doc.replace("[Inter-lab comparison / split-sample plan]",
                      xe(qc.get("eqa_alternative_plan", "")))
    doc = nth_replace(doc, "[SOP ID]",
                      xe(qc.get("eqa_alternative_sop", "")),           1)

    # §7.5 Personnel competency
    doc = doc.replace("[Training SOP / record ID]",
                      xe(qc.get("personnel_training_sop", "")))
    doc = doc.replace("[Competency SOP / record ID]",
                      xe(qc.get("personnel_competency_sop", "")))

    # §7.6 Change control — [QMS / change SOP ID] ×5 in document order:
    #   1=clone change  2=fluorochrome change  3=buffer/kit change
    #   4=instrument model change  5=software/gating change
    for key in ["change_control_clone", "change_control_fluorochrome",
                "change_control_buffer", "change_control_instrument",
                "change_control_software"]:
        doc = nth_replace(doc, "[QMS / change SOP ID]",
                          xe(qc.get(key, "")), 1)

    # §7.6 new-site introduction — transfer plan ID (after all 5 QMS SOPs)
    doc = doc.replace("[Transfer plan ID]",
                      xe(qc.get("transfer_plan_id", "")))

    # -----------------------------------------------------------------------
    # §8.3 APPROVALS TABLE
    # -----------------------------------------------------------------------
    approvals = data.get("approvals", {})
    approval_roles = [
        ("Author",
         approvals.get("author", {})),
        ("Lab Director / Tech Supervisor",
         approvals.get("lab_director", {})),
        ("Medical Director (if clinical)",
         approvals.get("medical_director", {})),
        ("Quality Assurance",
         approvals.get("quality_assurance", {})),
        ("Sponsor representative (if applicable)",
         approvals.get("sponsor_rep", {})),
    ]
    for role_text, info in approval_roles:
        name = info.get("name", "")
        date = info.get("date", "")
        if name or date:
            doc = fill_approval_row(doc, role_text, name, date)

    # -----------------------------------------------------------------------
    # §9.1 RISKS TABLE
    # 9 rows × 2 [L/M/H] (likelihood then impact), document order:
    #   1-2: post-thaw viability   3-4: post-thaw recovery
    #   5-6: Poisson floor         7-8: tandem dye
    #   9-10: cytometer drift      11-12: reference PBMC lot
    #   13-14: analyst drift       15-16: software update
    #   17-18: PT/EQA failure
    #
    # Each risk row also has a unique named SOP-ID token (1× each):
    # -----------------------------------------------------------------------
    risks = data.get("risks", [])
    for risk in risks:
        doc = nth_replace(doc, "[L/M/H]",
                          xe(risk.get("likelihood", "M")), 1)
        doc = nth_replace(doc, "[L/M/H]",
                          xe(risk.get("impact", "M")),     1)

    # Unique risk-row SOP IDs (replace all occurrences — each token is 1×,
    # except [Pre-analytical plan ID] which appears in §7.6 too: both get
    # the same plan ID, which is correct).
    rsops = data.get("risk_sops", {})
    doc = doc.replace("[Thaw SOP ID]",
                      xe(rsops.get("thaw_sop", "")))
    doc = doc.replace("[Validation report / SOP ID]",
                      xe(rsops.get("validation_report_sop", "")))
    doc = doc.replace("[Reagent QC SOP ID]",
                      xe(rsops.get("reagent_qc_sop", "")))
    doc = doc.replace("[Daily QC SOP ID]",
                      xe(rsops.get("daily_qc_sop", "")))
    doc = doc.replace("[Reference material SOP ID]",
                      xe(rsops.get("reference_material_sop", "")))
    doc = doc.replace("[Competency SOP ID]",
                      xe(rsops.get("competency_sop", "")))
    doc = doc.replace("[Change control SOP ID]",
                      xe(rsops.get("change_control_sop", "")))
    doc = doc.replace("[CAPA SOP ID]",
                      xe(rsops.get("capa_sop", "")))
    # [Pre-analytical plan ID] appears 2×: §7.6 new-site row + §9.1 cryo risk
    doc = doc.replace("[Pre-analytical plan ID]",
                      xe(rsops.get("pre_analytical_plan_id", "")))

    # -----------------------------------------------------------------------
    # §9.2 DEVIATIONS — SOP reference
    # -----------------------------------------------------------------------
    doc = doc.replace("[Enter ID]",
                      xe(data.get("deviation_sop_id", "")))

    # -----------------------------------------------------------------------
    # NUMERIC THRESHOLD TOKENS — [X], [Y], [N]
    # These appear throughout the template in descriptive/example text cells
    # to indicate user-specified acceptance thresholds:
    #
    #   [X] ×10 — percentage tolerance threshold used across multiple sections:
    #     §4.4 cocktail ±[X]%, §4.6 cross-cytometer ±[X]%, §5.2 accuracy
    #     intercept ±[X], §5.6 linearity ±[X]%, §5.8 stability ±[X]%,
    #     §5.10 carryover ≤[X]%, §7.2 ref-PBMC mid ±[X]%, §7.2 near-LLOQ
    #     CV ≤[X]%, §7.3 antibody bridging ±[X]%, §7.3 tandem dye ±[X]%,
    #     §7.6 software concordance ≥[X]%
    #   [Y] ×1  — accuracy bias threshold: §5.2 "bias ≤[Y]% at decision threshold"
    #   [N] ×1  — reference PBMC reserve vials: §9.1 "Maintain ≥[N] vials reserve"
    #
    # Using doc.replace() because every [X] gets the same tolerance value,
    # every [Y] gets the same bias value, [N] is unique.
    # -----------------------------------------------------------------------
    thresholds = data.get("thresholds", {})
    doc = doc.replace("[X]",
                      xe(str(thresholds.get("tolerance_pct", "20"))))
    doc = doc.replace("[Y]",
                      xe(str(thresholds.get("accuracy_bias_pct", "10"))))
    doc = doc.replace("[N]",
                      xe(str(thresholds.get("reference_pbmc_reserve_vials", "10"))))

    # -----------------------------------------------------------------------
    # Write output DOCX
    # -----------------------------------------------------------------------
    file_map["word/document.xml"] = doc.encode("utf-8")
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data_bytes in file_map.items():
            zout.writestr(name, data_bytes)

    print(f"Output written to: {output_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: fill_template.py <data.json> <template.docx> <output.docx>",
              file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        d = json.load(f)

    fill(d, sys.argv[2], sys.argv[3])
