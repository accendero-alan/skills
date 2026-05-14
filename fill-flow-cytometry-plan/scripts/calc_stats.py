#!/usr/bin/env python3
"""
Validate inputs and compute all statistical values for the Flow Cytometry
Experimental Plan. Outputs a single JSON blob consumed by fill_template.py.

Usage:
    python calc_stats.py <input.json>

Exits with code 1 and prints validation errors if inputs fail checks.
On success, writes the enriched data JSON to stdout.

All arithmetic is done here — never by the LLM.
"""
import json
import math
import statistics
import sys
from datetime import datetime


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

VALID_CLASSIFICATIONS = {"Quantitative", "Semi-quantitative", "Qualitative"}
VALID_TIERS = {"Research", "Fit-for-purpose (GCLP)", "CLIA LDT", "IVD"}
VALID_MATRICES = {"Whole blood", "PBMC", "BM aspirate", "Apheresis", "CSF", "Other"}
VALID_LMH = {"L", "M", "H"}


def is_valid_date(s):
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def validate(data):
    errors = []

    # Cover page required fields
    for field in ["study_protocol_number", "assay_name_version", "sponsor_department",
                  "authors", "reviewers", "approvers", "effective_date",
                  "intended_use_statement"]:
        if not data.get(field, "").strip():
            errors.append(f"Cover page: '{field}' is required and cannot be empty.")

    if data.get("assay_classification") not in VALID_CLASSIFICATIONS:
        errors.append(
            f"assay_classification must be one of: {sorted(VALID_CLASSIFICATIONS)}. "
            f"Got: {data.get('assay_classification')!r}"
        )

    if data.get("regulatory_tier") not in VALID_TIERS:
        errors.append(
            f"regulatory_tier must be one of: {sorted(VALID_TIERS)}. "
            f"Got: {data.get('regulatory_tier')!r}"
        )

    if data.get("sample_matrix") not in VALID_MATRICES:
        errors.append(
            f"sample_matrix must be one of: {sorted(VALID_MATRICES)}. "
            f"Got: {data.get('sample_matrix')!r}"
        )

    if not is_valid_date(data.get("effective_date", "")):
        errors.append("effective_date must be in YYYY-MM-DD format.")

    # §3.1 PBMC specs
    pbmc = data.get("pbmc_specs", {})
    for pct_field in ["min_viability_at_freeze", "min_viability_post_thaw",
                      "min_recovery_post_thaw"]:
        val = pbmc.get(pct_field)
        if val is not None:
            try:
                v = float(val)
                if not (0 <= v <= 100):
                    errors.append(
                        f"pbmc_specs.{pct_field} must be between 0 and 100 (got {v})."
                    )
            except (TypeError, ValueError):
                errors.append(f"pbmc_specs.{pct_field} must be numeric.")

    freeze_v = pbmc.get("min_viability_at_freeze")
    thaw_v = pbmc.get("min_viability_post_thaw")
    if freeze_v is not None and thaw_v is not None:
        try:
            if float(thaw_v) > float(freeze_v):
                errors.append(
                    "pbmc_specs.min_viability_post_thaw cannot exceed "
                    "min_viability_at_freeze (post-thaw viability ≤ freeze viability)."
                )
        except (TypeError, ValueError):
            pass

    # §3.2 Antibody panel
    antibodies = data.get("antibodies", [])
    if not antibodies:
        errors.append("antibodies: at least one antibody row is required.")
    for i, ab in enumerate(antibodies):
        for col in ["marker", "fluorochrome", "clone", "vendor_cat", "lot", "volume_dilution"]:
            if not str(ab.get(col, "")).strip():
                errors.append(f"antibodies[{i}].{col} is required.")

    # §4.6 Cytometer qualification
    cytometers = data.get("cytometers", [])
    if not cytometers:
        errors.append("cytometers: at least one cytometer row is required.")
    for i, cyt in enumerate(cytometers):
        pq_date = cyt.get("last_pq_date", "")
        if pq_date and not is_valid_date(pq_date):
            errors.append(
                f"cytometers[{i}].last_pq_date must be YYYY-MM-DD (got {pq_date!r})."
            )

    # §8.3 Approvals dates
    for role_key, role_label in [
        ("author", "Author"),
        ("lab_director", "Lab Director"),
        ("medical_director", "Medical Director"),
        ("quality_assurance", "Quality Assurance"),
        ("sponsor_rep", "Sponsor Rep"),
    ]:
        d = data.get("approvals", {}).get(role_key, {})
        date_val = d.get("date", "")
        if date_val and not is_valid_date(date_val):
            errors.append(
                f"approvals.{role_key}.date must be YYYY-MM-DD (got {date_val!r})."
            )

    # §9.1 Risks L/M/H
    for i, risk in enumerate(data.get("risks", [])):
        for field in ["likelihood", "impact"]:
            val = risk.get(field, "")
            if val and val.upper() not in VALID_LMH:
                errors.append(
                    f"risks[{i}].{field} must be L, M, or H (got {val!r})."
                )
            elif val:
                risk[field] = val.upper()

    return errors


# ---------------------------------------------------------------------------
# Statistical calculations — ALL numeric work happens here
# ---------------------------------------------------------------------------

def compute_precision(data):
    """
    Compute CV% for intra-assay and inter-assay precision from replicate arrays.

    Input structure (within data["precision"]):
      {
        "intra_assay": {
          "low":  [float, ...],   # >= 10 replicates
          "mid":  [float, ...],
          "high": [float, ...]
        },
        "inter_assay": {
          "low":  [float, ...],   # all replicates across days/analysts
          "mid":  [float, ...],
          "high": [float, ...]
        }
      }

    Returns dict with computed CV% values (rounded to 2 decimal places).
    Raises ValueError with clear message if inputs are invalid.
    """
    prec = data.get("precision", {})
    results = {"intra_assay_cv": {}, "inter_assay_cv": {}}
    errors = []

    for assay_type in ["intra_assay", "inter_assay"]:
        min_n = 10 if assay_type == "intra_assay" else 1
        for level in ["low", "mid", "high"]:
            reps = prec.get(assay_type, {}).get(level)
            if reps is None:
                continue
            if not isinstance(reps, list) or len(reps) < min_n:
                errors.append(
                    f"precision.{assay_type}.{level}: need at least {min_n} "
                    f"replicates (got {len(reps) if isinstance(reps, list) else 0})."
                )
                continue
            vals = [float(v) for v in reps]
            mean_val = statistics.mean(vals)
            if mean_val == 0:
                errors.append(
                    f"precision.{assay_type}.{level}: mean is zero; CV undefined."
                )
                continue
            sd = statistics.stdev(vals)
            cv = round((sd / mean_val) * 100, 2)
            results[f"{assay_type}_cv"][level] = {
                "n": len(vals),
                "mean": round(mean_val, 4),
                "sd": round(sd, 4),
                "cv_pct": cv,
            }

    if errors:
        raise ValueError("\n".join(errors))

    return results


def compute_lob_lod_loq(data):
    """
    Compute LOB, LOD, and LOQ per CLSI EP17-A2.

    Required inputs in data["sensitivity"]:
      blank_measurements:       list of >= 60 floats
      low_level_measurements:   list of floats (spike/admix near LOB)
      lloq_spike_levels:        list of {
                                    "concentration": float,
                                    "replicates": [float, ...]
                                  }
      lloq_assigned_values:     matching list of assigned/nominal concentrations
      lloq_cv_threshold_pct:    float (e.g. 30)
      lloq_bias_threshold_pct:  float (e.g. 30)
      minimum_events_required:  int (optional – Poisson CV)

    All formulas:
      LOB = mean(blank) + 1.645 * SD(blank)
      LOD = LOB + 1.645 * SD(low_level)
      LOQ = lowest spike concentration where CV% <= threshold AND bias% <= threshold
    """
    sens = data.get("sensitivity", {})
    if not sens:
        return {}

    errors = []

    blank = sens.get("blank_measurements", [])
    if len(blank) < 60:
        errors.append(
            f"sensitivity.blank_measurements: LOB requires >= 60 measurements "
            f"per CLSI EP17 (got {len(blank)})."
        )
    low_level = sens.get("low_level_measurements", [])

    if errors:
        raise ValueError("\n".join(errors))

    blank_f = [float(v) for v in blank]
    blank_mean = statistics.mean(blank_f)
    blank_sd = statistics.stdev(blank_f)
    lob = blank_mean + 1.645 * blank_sd

    ll_f = [float(v) for v in low_level]
    ll_sd = statistics.stdev(ll_f) if len(ll_f) >= 2 else 0.0
    lod = lob + 1.645 * ll_sd

    # LOQ: iterate spike levels in order, return the first meeting both criteria
    cv_thresh = float(sens.get("lloq_cv_threshold_pct", 30))
    bias_thresh = float(sens.get("lloq_bias_threshold_pct", 30))
    spike_levels = sens.get("lloq_spike_levels", [])
    loq = None
    loq_details = []
    for lvl in spike_levels:
        conc = float(lvl["concentration"])
        reps = [float(v) for v in lvl["replicates"]]
        assigned = float(lvl.get("assigned_value", conc))
        if len(reps) < 2:
            loq_details.append({"concentration": conc, "skipped": "< 2 replicates"})
            continue
        lvl_mean = statistics.mean(reps)
        lvl_sd = statistics.stdev(reps)
        cv = (lvl_sd / lvl_mean * 100) if lvl_mean != 0 else float("inf")
        bias = (abs(lvl_mean - assigned) / assigned * 100) if assigned != 0 else float("inf")
        passes = cv <= cv_thresh and bias <= bias_thresh
        loq_details.append({
            "concentration": conc,
            "n": len(reps),
            "mean": round(lvl_mean, 4),
            "cv_pct": round(cv, 2),
            "bias_pct": round(bias, 2),
            "passes": passes,
        })
        if passes and loq is None:
            loq = conc

    # Poisson CV for rare events
    min_events = sens.get("minimum_events_required")
    poisson_cv = None
    if min_events is not None:
        n = int(min_events)
        if n > 0:
            poisson_cv = round((1.0 / math.sqrt(n)) * 100, 2)

    return {
        "LOB": round(lob, 4),
        "LOD": round(lod, 4),
        "LOQ": loq,
        "blank_n": len(blank_f),
        "blank_mean": round(blank_mean, 4),
        "blank_sd": round(blank_sd, 4),
        "low_level_n": len(ll_f),
        "low_level_sd": round(ll_sd, 4),
        "loq_spike_details": loq_details,
        "poisson_cv_pct": poisson_cv,
    }


def compute_linearity(data):
    """
    Compute linear regression and deviation from linearity.

    Input in data["linearity"]:
      levels: list of {
                "concentration": float,
                "replicates": [float, ...]   # >= 3
              }
    Requires >= 5 levels.

    Computes: slope, intercept, R^2, per-level deviation_from_linearity_pct
    """
    lin = data.get("linearity", {})
    if not lin:
        return {}

    levels = lin.get("levels", [])
    if len(levels) < 5:
        raise ValueError(
            f"linearity.levels: >= 5 levels required per CLSI EP06 (got {len(levels)})."
        )

    xs = []  # concentrations
    ys = []  # all individual measurements (for regression)
    level_means = []

    for lvl in levels:
        conc = float(lvl["concentration"])
        reps = [float(v) for v in lvl["replicates"]]
        if len(reps) < 3:
            raise ValueError(
                f"linearity level at {conc}: >= 3 replicates required (got {len(reps)})."
            )
        for r in reps:
            xs.append(conc)
            ys.append(r)
        level_means.append((conc, statistics.mean(reps)))

    # Ordinary least squares
    n = len(xs)
    x_bar = statistics.mean(xs)
    y_bar = statistics.mean(ys)
    ss_xy = sum((x - x_bar) * (y - y_bar) for x, y in zip(xs, ys))
    ss_xx = sum((x - x_bar) ** 2 for x in xs)
    slope = ss_xy / ss_xx
    intercept = y_bar - slope * x_bar

    # R²
    ss_tot = sum((y - y_bar) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0

    # Deviation from linearity per level
    deviations = []
    for conc, mean_val in level_means:
        predicted = slope * conc + intercept
        if predicted != 0:
            dev = abs(predicted - mean_val) / abs(predicted) * 100
        else:
            dev = float("inf")
        deviations.append({
            "concentration": conc,
            "mean_measured": round(mean_val, 4),
            "predicted": round(predicted, 4),
            "deviation_pct": round(dev, 2),
        })

    return {
        "slope": round(slope, 6),
        "intercept": round(intercept, 6),
        "r_squared": round(r_squared, 6),
        "levels": deviations,
    }


# ---------------------------------------------------------------------------
# Acceptance criteria summary builder
# ---------------------------------------------------------------------------

def build_acceptance_criteria_summary(data, stats):
    """
    Merge user-supplied acceptance criteria text with computed statistical
    values to produce the §5.11 summary strings.
    """
    ac_in = data.get("acceptance_criteria", {})
    prec = stats.get("precision", {})
    sens = stats.get("sensitivity", {})
    lin = stats.get("linearity", {})

    def cv_summary(cv_dict):
        parts = []
        for level in ["low", "mid", "high"]:
            if level in cv_dict:
                parts.append(f"{level}: {cv_dict[level]['cv_pct']}%")
        return ", ".join(parts) if parts else ""

    # Auto-populate acceptance fields from computed values if user left them blank
    ac_out = dict(ac_in)

    if not ac_out.get("repeatability") and prec.get("intra_assay_cv"):
        ac_out["repeatability"] = (
            f"Observed CV%: {cv_summary(prec['intra_assay_cv'])} "
            f"(target: {ac_in.get('repeatability_target', '≤15% mid-range')})"
        )

    if not ac_out.get("intermediate_precision") and prec.get("inter_assay_cv"):
        ac_out["intermediate_precision"] = (
            f"Observed CV%: {cv_summary(prec['inter_assay_cv'])} "
            f"(target: {ac_in.get('precision_target', '≤15% mid-range')})"
        )

    if not ac_out.get("lob_lod_loq") and sens:
        parts = []
        if sens.get("LOB") is not None:
            parts.append(f"LOB={sens['LOB']}")
        if sens.get("LOD") is not None:
            parts.append(f"LOD={sens['LOD']}")
        if sens.get("LOQ") is not None:
            parts.append(f"LOQ={sens['LOQ']}")
        if parts:
            ac_out["lob_lod_loq"] = "; ".join(parts)

    if not ac_out.get("linearity_amr") and lin:
        ac_out["linearity_amr"] = (
            f"R²={lin.get('r_squared', 'N/A')}; "
            f"slope={lin.get('slope', 'N/A')}; "
            f"max deviation={max((l['deviation_pct'] for l in lin.get('levels', [])), default=0):.2f}%"
        )

    return ac_out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: calc_stats.py <input.json> [output.json]", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate
    errors = validate(data)
    if errors:
        print("VALIDATION ERRORS:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    # Compute statistics (each section is optional)
    stats = {}
    computation_errors = []

    if data.get("precision"):
        try:
            p = compute_precision(data)
            stats["precision"] = p
        except ValueError as e:
            computation_errors.append(str(e))

    if data.get("sensitivity"):
        try:
            s = compute_lob_lod_loq(data)
            stats["sensitivity"] = s
        except ValueError as e:
            computation_errors.append(str(e))

    if data.get("linearity"):
        try:
            lin = compute_linearity(data)
            stats["linearity"] = lin
        except ValueError as e:
            computation_errors.append(str(e))

    if computation_errors:
        print("COMPUTATION ERRORS:", file=sys.stderr)
        for e in computation_errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    # Build final acceptance criteria summary (merges computed values)
    data["acceptance_criteria"] = build_acceptance_criteria_summary(data, stats)

    # Embed computed stats into the output data so fill_template.py can use them
    data["_computed"] = stats

    output_json = json.dumps(data, indent=2, ensure_ascii=False)

    if len(sys.argv) == 3:
        # Write to file (avoids PowerShell/shell encoding issues with stdout redirect)
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Computed data written to: {sys.argv[2]}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
