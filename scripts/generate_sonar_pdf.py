from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from fpdf import FPDF

SEVERITY_COLORS = {
    "BLOCKER":  (155, 17, 30),
    "CRITICAL": (220, 53, 69),
    "MAJOR":    (255, 140, 0),
    "MINOR":    (230, 175, 0),
    "INFO":     (23, 162, 184),
}
TYPE_COLORS = {
    "BUG":              (220, 53, 69),
    "VULNERABILITY":    (255, 140, 0),
    "SECURITY_HOTSPOT": (230, 175, 0),
    "CODE_SMELL":       (108, 117, 125),
}
HEADER_BG  = (33, 37, 41)
WHITE      = (255, 255, 255)
DARK_TEXT  = (30, 30, 30)
MUTED_TEXT = (108, 117, 125)
ROW_ODD    = (248, 249, 250)
ROW_EVEN   = (255, 255, 255)
TEAL       = (23, 162, 184)

RATING_COLORS = {
    "1": (40, 167, 69),
    "2": (92, 184, 92),
    "3": (230, 175, 0),
    "4": (255, 128, 0),
    "5": (220, 53, 69),
}
RATING_LETTERS = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}


class SonarPDF(FPDF):
    def header(self):
        self.set_fill_color(*HEADER_BG)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 9)
        self.cell(
            0, 7,
            "  SonarQube / SonarCloud Analysis Report \u2014 SonarTrivy Demo Project",
            fill=True, new_x="LMARGIN", new_y="NEXT",
        )
        self.set_text_color(*DARK_TEXT)
        self.ln(2)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*MUTED_TEXT)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        self.cell(
            0, 8,
            f"SonarQube Analysis Report   |   {ts}   |   Page {self.page_no()}",
            align="C",
        )
        self.set_text_color(*DARK_TEXT)


def safe(text: str, limit: int = 200) -> str:
    return str(text)[:limit].encode("latin-1", errors="replace").decode("latin-1")


def read_sonar_properties() -> dict:
    props = {}
    props_file = Path("sonar-project.properties")
    if not props_file.exists():
        return props
    for line in props_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            props[k.strip()] = v.strip()
    return props


def api_get(url: str, token: str) -> dict | None:
    creds = base64.b64encode(f"{token}:".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {creds}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"[api] HTTP {exc.code} for {url}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"[api] failed for {url}: {exc}", file=sys.stderr)
        return None


def metric_card(pdf: FPDF, label: str, value: str,
                x: float, y: float, color: tuple, w: float = 46):
    pdf.set_xy(x, y)
    pdf.set_fill_color(*color)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(w, 15, value, fill=True, align="C", border=0)
    pdf.set_xy(x, y + 15)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(w, 6, label, fill=True, align="C", border=0)
    pdf.set_text_color(*DARK_TEXT)


def section_title(pdf: FPDF, title: str):
    pdf.set_fill_color(235, 237, 242)
    pdf.set_text_color(40, 44, 80)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 204, 212)
    pdf.line(pdf.l_margin, pdf.get_y(),
             pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(3)
    pdf.set_text_color(*DARK_TEXT)


def table_header_row(pdf: FPDF, columns: list):
    pdf.set_fill_color(*HEADER_BG)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 7)
    for label, w in columns:
        pdf.cell(w, 6, f" {safe(label)}", border=0, fill=True)
    pdf.ln()
    pdf.set_text_color(*DARK_TEXT)


def render_gate_conditions(pdf: FPDF, conditions: list):
    if not conditions:
        return
    cols = [("Metric", 110), ("Status", 26), ("Comparator", 30), ("Threshold", 30), ("Actual", 30)]
    table_header_row(pdf, cols)

    for i, cond in enumerate(conditions):
        row_bg = ROW_ODD if i % 2 == 0 else ROW_EVEN
        status = cond.get("status", "")
        status_col = SEVERITY_COLORS["INFO"] if status == "OK" else SEVERITY_COLORS["CRITICAL"]

        pdf.set_fill_color(*row_bg)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*DARK_TEXT)
        metric = safe(cond.get("metricKey", "").replace("_", " "), 106)
        pdf.cell(110, 5, f" {metric}", border=0, fill=True)

        pdf.set_fill_color(*status_col)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*WHITE)
        pdf.cell(26, 5, f" {safe(status)}", border=0, fill=True)

        pdf.set_fill_color(*row_bg)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*DARK_TEXT)
        pdf.cell(30, 5, f" {safe(cond.get('comparator',''))}", border=0, fill=True)
        pdf.cell(30, 5, f" {safe(cond.get('errorThreshold',''))}", border=0, fill=True)
        pdf.cell(30, 5, f" {safe(cond.get('actualValue',''))}", border=0, fill=True)
        pdf.ln()

    pdf.ln(5)


def render_issues_table(pdf: FPDF, issues: list, total: int):
    if not issues:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(40, 167, 69)
        pdf.cell(0, 6, "  No open issues found.", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*DARK_TEXT)
        return

    type_order = {"VULNERABILITY": 0, "BUG": 1, "SECURITY_HOTSPOT": 2, "CODE_SMELL": 3}
    sev_order  = {"BLOCKER": 0, "CRITICAL": 1, "MAJOR": 2, "MINOR": 3, "INFO": 4}
    sorted_issues = sorted(
        issues,
        key=lambda x: (
            type_order.get(x.get("type", ""), 9),
            sev_order.get(x.get("severity", ""), 9),
        ),
    )

    cols = [
        ("Type", 30), ("Severity", 26), ("Rule", 44),
        ("Message", 106), ("Component", 52), ("Line", 13),
    ]
    table_header_row(pdf, cols)

    shown = min(len(sorted_issues), 200)
    for i, issue in enumerate(sorted_issues[:shown]):
        itype    = issue.get("type", "").upper()
        severity = issue.get("severity", "").upper()
        type_col = TYPE_COLORS.get(itype, MUTED_TEXT)
        sev_col  = SEVERITY_COLORS.get(severity, MUTED_TEXT)
        row_bg   = ROW_ODD if i % 2 == 0 else ROW_EVEN

        pdf.set_fill_color(*type_col)
        pdf.set_font("Helvetica", "B", 6)
        pdf.set_text_color(*WHITE)
        pdf.cell(30, 5, f" {safe(itype.replace('_',' '), 22)}", border=0, fill=True)

        pdf.set_fill_color(*sev_col)
        pdf.cell(26, 5, f" {safe(severity, 18)}", border=0, fill=True)

        pdf.set_fill_color(*row_bg)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*DARK_TEXT)
        pdf.cell(44, 5, f" {safe(issue.get('rule',''), 40)}", border=0, fill=True)
        pdf.cell(106, 5, f" {safe(issue.get('message',''), 102)}", border=0, fill=True)
        component = issue.get("component", "").split(":")[-1]
        pdf.cell(52, 5, f" {safe(component, 48)}", border=0, fill=True)
        pdf.cell(13, 5, f" {safe(str(issue.get('line','')))}", border=0, fill=True)
        pdf.ln()

    if total > shown:
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*MUTED_TEXT)
        pdf.cell(
            0, 5,
            f"  ... {total - shown} more issues not shown. See the SonarQube dashboard for the full list.",
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.set_text_color(*DARK_TEXT)


def main():
    props = read_sonar_properties()
    token = os.environ.get("SONAR_TOKEN", "")
    host  = os.environ.get("SONAR_HOST_URL", "https://sonarcloud.io").rstrip("/")

    project_key  = props.get("sonar.projectKey",
                             os.environ.get("SONAR_PROJECT_KEY", "SonarTrivy"))
    organization = props.get("sonar.organization", "").strip()

    if not token:
        print("[error] SONAR_TOKEN is not set.", file=sys.stderr)
        sys.exit(1)

    is_placeholder = organization in ("", "YOUR_SONARCLOUD_ORG_KEY")
    org_param = (f"&organization={urllib.parse.quote(organization)}"
                 if not is_placeholder else "")
    enc_key = urllib.parse.quote(project_key)

    print(f"Querying {host} for project '{project_key}' ...")

    gate_data = api_get(
        f"{host}/api/qualitygates/project_status?projectKey={enc_key}{org_param}",
        token,
    )

    metrics_keys = (
        "bugs,vulnerabilities,code_smells,coverage,"
        "duplicated_lines_density,security_hotspots,"
        "security_rating,reliability_rating,sqale_rating,ncloc"
    )
    measures_data = api_get(
        f"{host}/api/measures/component"
        f"?component={enc_key}&metricKeys={metrics_keys}{org_param}",
        token,
    )

    issues_data = api_get(
        f"{host}/api/issues/search"
        f"?componentKeys={enc_key}&statuses=OPEN&ps=500{org_param}",
        token,
    )

    gate_status     = (gate_data or {}).get("projectStatus", {})
    qg_result       = gate_status.get("status", "UNKNOWN")
    gate_conditions = gate_status.get("conditions", [])

    measures = {
        m["metric"]: m.get("value", "\u2014")
        for m in ((measures_data or {}).get("component", {}).get("measures") or [])
    }

    issues       = (issues_data or {}).get("issues") or []
    total_issues = (issues_data or {}).get("total", len(issues))

    pdf = SonarPDF(orientation="L", format="A4")
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*DARK_TEXT)
    pdf.cell(0, 13, "SonarQube Analysis Report", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MUTED_TEXT)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pdf.cell(0, 6, f"Project: {safe(project_key)}   |   Host: {safe(host)}   |   Date: {ts}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    gate_passed = qg_result == "OK"
    gate_color  = (40, 167, 69) if gate_passed else (220, 53, 69)
    gate_label  = "PASSED" if gate_passed else "FAILED"

    pdf.set_fill_color(*gate_color)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 16, f"  Quality Gate: {gate_label}", fill=True,
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*DARK_TEXT)
    pdf.ln(5)

    section_title(pdf, "Quality Gate Conditions")
    render_gate_conditions(pdf, gate_conditions)

    section_title(pdf, "Key Metrics")
    cx, cy = pdf.get_x(), pdf.get_y()

    def mv(key: str, suffix: str = "") -> str:
        v = measures.get(key, "\u2014")
        return v + suffix if v != "\u2014" else v

    cards = [
        ("Bugs",           mv("bugs"),                           TYPE_COLORS["BUG"]),
        ("Vulnerabilities",mv("vulnerabilities"),                TYPE_COLORS["VULNERABILITY"]),
        ("Hotspots",       mv("security_hotspots"),              TYPE_COLORS["SECURITY_HOTSPOT"]),
        ("Code Smells",    mv("code_smells"),                    MUTED_TEXT),
        ("Coverage",       mv("coverage", "%"),                  (0, 123, 255)),
        ("Duplications",   mv("duplicated_lines_density", "%"),  TEAL),
    ]
    for i, (lbl, val, col) in enumerate(cards):
        metric_card(pdf, lbl, safe(val, 8), cx + i * 48, cy, col)
    pdf.set_y(cy + 28)
    pdf.ln(6)

    section_title(pdf, "Ratings  (A = best, E = worst)")
    ry = pdf.get_y()
    for i, (lbl, key) in enumerate([
        ("Security",        "security_rating"),
        ("Reliability",     "reliability_rating"),
        ("Maintainability", "sqale_rating"),
    ]):
        raw    = measures.get(key, "")
        letter = RATING_LETTERS.get(raw, safe(raw) or "\u2014")
        color  = RATING_COLORS.get(raw, MUTED_TEXT)
        metric_card(pdf, lbl, letter, cx + i * 48, ry, color)
    pdf.set_y(ry + 28)
    pdf.ln(6)

    pdf.add_page()
    section_title(pdf, f"Open Issues  ({total_issues} total)")
    render_issues_table(pdf, issues, total_issues)

    out = "sonarqube-report.pdf"
    pdf.output(out)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
