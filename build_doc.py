"""
Builds Gait_Anomaly_Detection_Overview.docx using python-docx.
Run from the python/ directory after generate_plots.py has been executed.
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

PLOTS = os.path.join(os.path.dirname(__file__), "plots")
OUT   = os.path.join(os.path.dirname(__file__), "..", "Gait_Anomaly_Detection_Overview.docx")

# ── Helpers ───────────────────────────────────────────────────────────────────

BLUE   = RGBColor(0x15, 0x65, 0xC0)
DARK   = RGBColor(0x22, 0x22, 0x22)
GREY   = RGBColor(0x55, 0x55, 0x55)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
LTBLUE = RGBColor(0xBB, 0xDE, 0xFB)


def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_cell_borders(cell, color="CCCCCC"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        tcBorders.append(el)
    tcPr.append(tcBorders)


def add_horizontal_rule(doc, color="DDDDDD"):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(10)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def h1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(20)
    p.paragraph_format.space_after  = Pt(6)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = BLUE
    run.font.name = "Arial"
    # bottom border
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "1565C0")
    pBdr.append(bottom)
    pPr.append(pBdr)


def h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(12)
    run.font.color.rgb = DARK
    run.font.name = "Arial"


def body(doc, text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after  = Pt(3)
    for run in p.runs:
        run.font.size = Pt(10.5)
        run.font.name = "Arial"
        run.font.color.rgb = DARK


def bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    run.font.name = "Arial"
    run.font.color.rgb = DARK


def add_image(doc, filename, width_in=6.3):
    path = os.path.join(PLOTS, filename)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run()
    run.add_picture(path, width=Inches(width_in))


def caption(doc, text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(10)
    for run in p.runs:
        run.italic = True
        run.font.size = Pt(9)
        run.font.color.rgb = GREY
        run.font.name = "Arial"


def add_table(doc, headers, rows, col_widths_in):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"

    # Header row
    hrow = t.rows[0]
    for i, (h, w) in enumerate(zip(headers, col_widths_in)):
        cell = hrow.cells[i]
        cell.width = Inches(w)
        set_cell_bg(cell, "1565C0")
        set_cell_borders(cell)
        p = cell.paragraphs[0]
        p.clear()
        run = p.add_run(h)
        run.bold = True
        run.font.color.rgb = WHITE
        run.font.size = Pt(10)
        run.font.name = "Arial"

    # Data rows
    for ri, row_data in enumerate(rows):
        row = t.rows[ri + 1]
        bg = "F5F9FF" if ri % 2 == 0 else "FFFFFF"
        for ci, (val, w) in enumerate(zip(row_data, col_widths_in)):
            cell = row.cells[ci]
            cell.width = Inches(w)
            set_cell_bg(cell, bg)
            set_cell_borders(cell)
            p = cell.paragraphs[0]
            p.clear()
            run = p.add_run(val)
            run.font.size = Pt(10)
            run.font.name = "Arial"
            run.font.color.rgb = DARK

    doc.add_paragraph()  # spacing after table


# ── Build document ─────────────────────────────────────────────────────────────

doc = Document()

# Page margins
for section in doc.sections:
    section.top_margin    = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin   = Inches(1.1)
    section.right_margin  = Inches(1.1)

# ── Title block ───────────────────────────────────────────────────────────────
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(24)
p.paragraph_format.space_after  = Pt(4)
r = p.add_run("Gait Anomaly Detection System")
r.bold = True; r.font.size = Pt(26); r.font.color.rgb = BLUE; r.font.name = "Arial"

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(4)
r = p.add_run("Technical Overview: Simulated Waveforms, Autoencoder Model & Enrolment")
r.font.size = Pt(12); r.font.color.rgb = GREY; r.font.name = "Arial"

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(18)
r = p.add_run("June 2026")
r.font.size = Pt(10); r.font.color.rgb = GREY; r.font.name = "Arial"

add_horizontal_rule(doc)

# ── Section 1: Waveforms ──────────────────────────────────────────────────────
h1(doc, "1.  Simulated Gait Waveforms")
body(doc, "The system simulates a 3-axis accelerometer mounted on the lower back at 50 Hz. Each axis captures a different component of the walking motion:")
bullet(doc, "acc_x — forward/backward oscillation as the body's centre of mass pitches")
bullet(doc, "acc_y — lateral (mediolateral) sway")
bullet(doc, "acc_z — vertical oscillation, the dominant signal during walking (largest amplitude)")
body(doc, "Five distinct gait patterns are modelled. Each uses a sinusoidal base signal with physiologically motivated parameters, plus Gaussian noise to approximate real sensor noise.")

add_image(doc, "comparison_vertical.png", width_in=6.3)
caption(doc, "Figure 1 — Vertical acceleration (acc_z) for all five gait types over 4 seconds.")

h2(doc, "1.1  Normal Walking")
body(doc, "Step frequency: ~1.9 Hz (cadence ~114 steps/min). The vertical axis shows a strong fundamental and a second harmonic at double frequency, reflecting heel-strike followed by toe-off within each step cycle. Forward and lateral axes have lower amplitude and are phase-shifted relative to vertical.")
add_image(doc, "normal_walking_waveform.png", width_in=6.3)
caption(doc, "Figure 2 — Normal walking: regular, symmetric oscillations across all three axes.")

h2(doc, "1.2  Limping")
body(doc, "Step frequency: ~1.7 Hz. Every alternate step has a significantly reduced amplitude (modelled by a half-step-rate modulator). This creates a characteristic paired pattern — one strong step followed by one weak step — visible as amplitude doubling in the period of the signal.")
add_image(doc, "limping_waveform.png", width_in=6.3)
caption(doc, "Figure 3 — Limping: alternating high/low amplitude steps produce an asymmetric envelope.")

h2(doc, "1.3  Shuffling")
body(doc, "Step frequency: ~1.4 Hz. The vertical oscillation amplitude is reduced by approximately 80% compared to normal walking. This reflects the reduced heel clearance and lack of push-off characteristic of shuffling gait (e.g. Parkinson's disease or extreme fatigue). The signal closely resembles noise around the gravity baseline.")
add_image(doc, "shuffling_waveform.png", width_in=6.3)
caption(doc, "Figure 4 — Shuffling: minimal vertical oscillation; signal barely deviates from the gravity baseline.")

h2(doc, "1.4  Running")
body(doc, "Step frequency: ~2.8 Hz. Both frequency and amplitude increase substantially. Peak vertical acceleration reaches ~3.5 g (versus ~1.7 g during normal walking), and a strong second harmonic is present from the hard foot-strike.")
add_image(doc, "running_waveform.png", width_in=6.3)
caption(doc, "Figure 5 — Running: higher cadence and much larger amplitude than normal walking.")

h2(doc, "1.5  Ataxic")
body(doc, "Ataxic gait is modelled with a phase-jitter process: the instantaneous frequency is perturbed at each time step via a cumulative phase noise term, and amplitude fluctuates randomly. The result is an irregular, unpredictable waveform that lacks the consistent periodicity of normal gait.")
add_image(doc, "ataxic_waveform.png", width_in=6.3)
caption(doc, "Figure 6 — Ataxic: irregular timing and variable amplitude distinguish it from all periodic patterns.")

add_horizontal_rule(doc)

# ── Section 2: Autoencoder ────────────────────────────────────────────────────
h1(doc, "2.  Autoencoder for Anomaly Detection")

h2(doc, "2.1  What is an autoencoder?")
body(doc, "An autoencoder is a neural network trained to compress an input into a compact representation (the bottleneck) and then reconstruct the original input from that representation. Because it is trained exclusively on normal examples, it learns the statistical structure of normal data well. When presented with anomalous data it has never seen during training, it produces a poor reconstruction — indicated by a high mean-squared error (MSE) between the input and the output. This reconstruction error serves directly as the anomaly score: the higher the error, the more anomalous the input is considered to be.")

h2(doc, "2.2  Architecture")
body(doc, "The model operates on an 18-element feature vector extracted from each 2.56-second window of accelerometer data. The architecture is a symmetric dense network:")
add_image(doc, "autoencoder_architecture.png", width_in=6.3)
caption(doc, "Figure 7 — Autoencoder architecture. The 6-neuron bottleneck forces the network to learn a compact representation of normal gait.")

add_table(doc,
    headers=["Layer", "Neurons", "Activation"],
    rows=[
        ["Input",              "18", "—"],
        ["Encoder (Dense)",    "12", "ReLU"],
        ["Bottleneck (Dense)", "6",  "ReLU"],
        ["Decoder (Dense)",    "12", "ReLU"],
        ["Output (Dense)",     "18", "Linear"],
    ],
    col_widths_in=[2.8, 1.5, 1.5]
)

h2(doc, "2.3  Feature extraction")
body(doc, "Raw samples are grouped into overlapping windows (128 samples, 50% stride). Six statistical features are extracted per axis, giving 18 features total:")
bullet(doc, "Mean — the DC component; shifts with gravity and orientation")
bullet(doc, "Standard deviation — measures oscillation intensity")
bullet(doc, "Minimum and maximum — capture peak excursions")
bullet(doc, "Root mean square (RMS) — energy of the signal including the mean")
bullet(doc, "Zero-crossing rate (relative to axis mean) — a proxy for step frequency")
body(doc, "The feature extraction is implemented identically in both the Python training pipeline (generate_gait_data.py) and the Android app (GaitFeatureExtractor.kt) to ensure the model receives the same input distribution at runtime as it was trained on.")

h2(doc, "2.4  Training")
body(doc, "The autoencoder is trained exclusively on normal gait data from 100 simulated subjects, each with a slightly different step frequency (1.7–2.1 Hz). No anomalous examples are used during training. Features are Z-score normalised using the training-set mean and standard deviation, which are exported alongside the model as scaler_params.json.")

h2(doc, "2.5  Anomaly scoring")
body(doc, "At inference time, a feature window is normalised, passed through the autoencoder, and the MSE between the normalised input and the reconstruction is computed. This scalar is the anomaly score. Scores below a per-user threshold are classified as normal; scores above are flagged as anomalous.")

add_horizontal_rule(doc)

# ── Section 3: Enrolment ──────────────────────────────────────────────────────
h1(doc, "3.  The Enrolment Session")

h2(doc, "3.1  Purpose")
body(doc, "Although the base autoencoder is trained on a population of simulated walkers, every individual has a unique gait signature. Factors such as walking speed, stride length, posture, phone placement, and natural cadence all affect the reconstruction error for a given person, even when their gait is entirely normal. If a single global threshold were used, it would either generate too many false alarms for people whose normal gait produces slightly higher reconstruction errors, or miss genuine anomalies in people who naturally walk closer to the population mean. The enrolment session solves this by calibrating a personal threshold on the individual's own baseline.")

h2(doc, "3.2  What happens during enrolment")
body(doc, "The user initiates a 30-second enrolment session. During this period:")
bullet(doc, "The GaitSimulator produces accelerometer samples at 50 Hz, mirroring normal walking.")
bullet(doc, "Samples are accumulated in a SampleBuffer and processed into overlapping 128-sample windows with a 64-sample stride, yielding ~46 feature windows over 30 seconds.")
bullet(doc, "Each feature window is passed through the pre-trained autoencoder and the reconstruction error (MSE) is recorded.")
bullet(doc, "After 30 seconds the mean (μ) and standard deviation (σ) of all collected errors are computed.")
bullet(doc, "The personal threshold is set to μ + 3σ, capturing 99.7% of the individual's normal-gait error distribution under a Gaussian assumption.")
bullet(doc, "This threshold is persisted to device storage (Android SharedPreferences) and used for all subsequent detection sessions.")

h2(doc, "3.3  Why μ + 3σ?")
body(doc, "A threshold of three standard deviations above the personal mean limits false alarms to approximately 0.15% of normal windows under a Gaussian assumption. In practice, reconstruction errors are right-skewed, so the effective false-alarm rate is even lower. The multiplier is a tunable constant (SIGMA_MULTIPLIER in EnrollmentActivity.kt); reducing it to 2 increases sensitivity at the cost of more false positives.")

h2(doc, "3.4  What changes after enrolment")
body(doc, "Nothing in the autoencoder's weights is modified. Enrolment is a threshold-calibration step only, not a fine-tuning step. This design means:")
bullet(doc, "Enrolment is computationally trivial — it requires only standard forward passes and basic statistics.")
bullet(doc, "The model does not overfit to a single individual; population-level generalisation is preserved.")
bullet(doc, "Re-enrolment is fast if the user's gait changes (e.g. after injury or recovery).")

h2(doc, "3.5  Detection after enrolment")
body(doc, "During a detection session, each new feature window produces an anomaly score that is compared to the personal threshold in real time. The DetectionActivity displays the raw score, a normalised progress bar, and a scrolling history chart with a red dashed threshold line. The status label switches from 'Normal' to 'Anomaly Detected' when the score exceeds the threshold. Users can switch between all five simulated gait types during detection to observe how the score rises for anomalous patterns.")

add_horizontal_rule(doc)

# ── Section 4: Quick Reference ────────────────────────────────────────────────
h1(doc, "4.  Quick Reference")

add_table(doc,
    headers=["Parameter", "Value"],
    rows=[
        ["Sample rate",              "50 Hz"],
        ["Window size",              "128 samples  (2.56 s)"],
        ["Window stride",            "64 samples  (50% overlap)"],
        ["Features per window",      "18  (6 stats × 3 axes)"],
        ["Autoencoder layers",       "18 → 12 → 6 → 12 → 18"],
        ["Bottleneck size",          "6 neurons"],
        ["Training data",            "100 synthetic subjects, normal gait only"],
        ["Anomaly score metric",     "MSE(normalised input, reconstruction)"],
        ["Enrolment duration",       "30 seconds (~46 feature windows)"],
        ["Threshold formula",        "μ + 3σ  of enrolment errors"],
        ["On-device model update",   "None — threshold calibration only"],
        ["Supported anomaly types",  "Limping, Shuffling, Running, Ataxic"],
    ],
    col_widths_in=[2.5, 4.3]
)

# ── Save ───────────────────────────────────────────────────────────────────────
doc.save(OUT)
print(f"Saved: {os.path.abspath(OUT)}")
