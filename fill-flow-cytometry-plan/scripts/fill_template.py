#!/usr/bin/env python3
"""
Fill the Flow Cytometry Experimental Plan template DOCX.

Usage:
    python fill_template.py <data.json> <template.docx> <output.docx>

The data.json must be produced by calc_stats.py (which validates fields and
computes all statistical values). This script only handles XML manipulation.
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
    # COVER PAGE
    # [Enter] positions 1-7 (in document order):
    #   1 = Study/Protocol Number
    #   2 = Assay Name/Version
    #   3 = Sponsor/Department
    #   4 = Authors
    #   5 = Reviewers
    #   6 = Approvers
    #   7 = Effective Date
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

    # Unique cover placeholders
    doc = doc.replace("[Enter — see §2]",
                      xe(data.get("intended_use_statement", "")))
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
    # §3.1 PBMC specimen specs (unique placeholder text per row)
    # -----------------------------------------------------------------------
    pbmc = data.get("pbmc_specs", {})
    doc = doc.replace("[Ficoll-Paque / SepMate / other — specify]",
                      xe(pbmc.get("isolation_method", "")))
    doc = doc.replace("[Ficoll-Paque / SepMate / other — specify]",
                      xe(pbmc.get("isolation_method", "")))
    doc = doc.replace("[e.g., 90% FBS / 10% DMSO; CryoStor CS10 — specify]",
                      xe(pbmc.get("cryopreservation_medium", "")))
    doc = doc.replace("[e.g., 90% FBS / 10% DMSO; CryoStor CS10 — specify]",
                      xe(pbmc.get("cryopreservation_medium", "")))
    doc = doc.replace("[Cryovial type, volume — specify]",
                      xe(pbmc.get("container_type", "")))
    doc = doc.replace("[Cryovial type, volume — specify]",
                      xe(pbmc.get("container_type", "")))
    doc = doc.replace("[e.g., ≥ 5 × 10⁶ viable cells per vial — specify]",
                      xe(pbmc.get("min_cells_at_freeze", "")))
    doc = doc.replace("[e.g., ≥ 5 × 10⁶ viable cells per vial — specify]",
                      xe(pbmc.get("min_cells_at_freeze", "")))
    doc = doc.replace("[e.g., ≥ 90% by trypan blue or AOPI — specify]",
                      xe(pbmc.get("min_viability_at_freeze", "")))
    doc = doc.replace("[e.g., ≥ 90% by trypan blue or AOPI — specify]",
                      xe(pbmc.get("min_viability_at_freeze", "")))
    doc = doc.replace("[e.g., ≥ 70% — specify]",
                      xe(pbmc.get("min_viability_post_thaw", "")))
    doc = doc.replace("[e.g., ≥ 70% — specify]",
                      xe(pbmc.get("min_viability_post_thaw", "")))
    doc = doc.replace("[e.g., ≥ 50% of frozen cell number — specify]",
                      xe(pbmc.get("min_recovery_post_thaw", "")))
    doc = doc.replace("[e.g., ≥ 50% of frozen cell number — specify]",
                      xe(pbmc.get("min_recovery_post_thaw", "")))

    # -----------------------------------------------------------------------
    # §3.2 Antibody panel – replace all 6 template rows with actual data
    # -----------------------------------------------------------------------
    antibodies = data.get("antibodies", [])
    if antibodies:
        # Find the block: from the <w:tr> before the first [Marker] to the end
        # of the 6th [Marker]-containing row.
        first_marker_pos = doc.find("[Marker]")
        if first_marker_pos != -1:
            first_tr_start = doc.rfind("<w:tr>", 0, first_marker_pos)
            # Walk forward to collect exactly 6 </w:tr> endings
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
    # §4.6 Cytometer qualification table
    # Each row: [Make / Model / Serial], [Site / room],
    #           [IQ ✓ / OQ ✓ / PQ ✓], [YYYY-MM-DD],
    #           [IQ/OQ/PQ report ID; daily QC SOP ID]
    # Template has 3 rows; user provides 1–3.
    # -----------------------------------------------------------------------
    cytometers = data.get("cytometers", [])
    for cyt in cytometers:
        doc = nth_replace(doc, "[Make / Model / Serial]",
                          xe(cyt.get("make_model_serial", "")), 1)
        doc = nth_replace(doc, "[Site / room]",
                          xe(cyt.get("site_location", "")), 1)
        doc = nth_replace(doc, "[IQ ✓ / OQ ✓ / PQ ✓]",
                          xe(cyt.get("qualification_status", "")), 1)
        doc = nth_replace(doc, "[IQ ✓ / OQ ✓ / PQ ✓]",
                          xe(cyt.get("qualification_status", "")), 1)
        doc = nth_replace(doc, "[YYYY-MM-DD]",
                          xe(cyt.get("last_pq_date", "")), 1)
        doc = nth_replace(doc, "[IQ/OQ/PQ report ID; daily QC SOP ID]",
                          xe(cyt.get("reference_docs", "")), 1)

    # -----------------------------------------------------------------------
    # §4.6 cross-cytometer bridging (bullet point [Enter])
    # Position 8 in the [Enter] sequence
    # -----------------------------------------------------------------------
    doc = nth_replace(doc, "[Enter]",
                      xe(data.get("bridging_study_report_id", "")), 1)

    # -----------------------------------------------------------------------
    # §5.11 Acceptance criteria table
    # Remaining [Enter] positions 9–16 (in document order):
    #   9  = Accuracy / Method comparison
    #   10 = Repeatability (intra-assay)
    #   11 = Intermediate precision
    #   12 = LOB / LOD / LOQ
    #   13 = Specificity
    #   14 = Linearity / AMR
    #   15 = Robustness
    #   16 = Carryover
    # Plus the unique "[Enter — typical ±15–20%]" for Reagent/stained-sample stability
    # -----------------------------------------------------------------------
    ac = data.get("acceptance_criteria", {})
    acceptance_fields = [
        ac.get("accuracy", ""),
        ac.get("repeatability", ""),
        ac.get("intermediate_precision", ""),
        ac.get("lob_lod_loq", ""),
        ac.get("specificity", ""),
        ac.get("linearity_amr", ""),
        ac.get("robustness", ""),
        ac.get("carryover", ""),
    ]
    for val in acceptance_fields:
        doc = nth_replace(doc, "[Enter]", xe(val), 1)

    # Unique stability acceptance criterion placeholder
    doc = doc.replace("[Enter — typical ±15–20%]",
                      xe(ac.get("stability", "")))
    doc = doc.replace("[Enter — typical ±15–20%]",
                      xe(ac.get("stability", "")))

    # -----------------------------------------------------------------------
    # §9.2 Deviation SOP reference: [Enter ID]
    # -----------------------------------------------------------------------
    doc = doc.replace("[Enter ID]",
                      xe(data.get("deviation_sop_id", "")))

    # -----------------------------------------------------------------------
    # §9.1 Risks table – [L/M/H] pairs (Likelihood then Impact per row)
    # 9 risk rows × 2 = 18 occurrences, in document order:
    # 1-2: post-thaw viability, 3-4: post-thaw recovery, 5-6: Poisson floor,
    # 7-8: tandem dye, 9-10: cytometer drift, 11-12: reference PBMC lot,
    # 13-14: analyst drift, 15-16: software update, 17-18: PT/EQA failure
    # -----------------------------------------------------------------------
    risks = data.get("risks", [])
    for risk in risks:
        doc = nth_replace(doc, "[L/M/H]",
                          xe(risk.get("likelihood", "M")), 1)
        doc = nth_replace(doc, "[L/M/H]",
                          xe(risk.get("impact", "M")), 1)

    # -----------------------------------------------------------------------
    # §8.3 Approvals table – fill name and date for each role
    # -----------------------------------------------------------------------
    approvals = data.get("approvals", {})
    approval_roles = [
        ("Author",                               approvals.get("author", {})),
        ("Lab Director / Tech Supervisor",       approvals.get("lab_director", {})),
        ("Medical Director (if clinical)",       approvals.get("medical_director", {})),
        ("Quality Assurance",                    approvals.get("quality_assurance", {})),
        ("Sponsor representative (if applicable)", approvals.get("sponsor_rep", {})),
    ]
    for role_text, info in approval_roles:
        name = info.get("name", "")
        date = info.get("date", "")
        if name or date:
            doc = fill_approval_row(doc, role_text, name, date)

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
