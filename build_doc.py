"""
Builds Gait_Anomaly_Detection_Overview.docx using python-docx.
Run from the python/ directory after:
    python generate_gait_data.py
    python generate_plots.py
    python generate_preprocessing_plots.py
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import math

PLOTS = os.path.join(os.path.dirname(__file__), "plots")
OUT   = os.path.join(os.path.dirname(__file__), "..", "Gait_Anomaly_Detection_Overview_v3.docx")

# ── Colour palette ─────────────────────────────────────────────────────────────
BLUE  = RGBColor(0x15, 0x65, 0xC0)
DARK  = RGBColor(0x22, 0x22, 0x22)
GREY  = RGBColor(0x55, 0x55, 0x55)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

# ── Helpers ────────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)

def set_cell_borders(cell, color="CCCCCC"):
    tc      = cell._tc
    tcPr    = tc.get_or_add_tcPr()
    tcBords = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"),   "single")
        el.set(qn("w:sz"),    "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        tcBords.append(el)
    tcPr.append(tcBords)

def add_rule(doc, color="DDDDDD"):
    p    = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(10)
    pPr  = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    "4")
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), color)
    pBdr.append(bot)
    pPr.append(pBdr)

def h1(doc, text):
    p   = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(20)
    p.paragraph_format.space_after  = Pt(6)
    run = p.add_run(text)
    run.bold = True; run.font.size = Pt(16)
    run.font.color.rgb = BLUE; run.font.name = "Arial"
    pPr  = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single"); bot.set(qn("w:sz"), "4")
    bot.set(qn("w:space"), "1");      bot.set(qn("w:color"), "1565C0")
    pBdr.append(bot); pPr.append(pBdr)

def h2(doc, text):
    p   = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.bold = True; run.font.size = Pt(12)
    run.font.color.rgb = DARK; run.font.name = "Arial"

def body(doc, text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after  = Pt(3)
    for r in p.runs:
        r.font.size = Pt(10.5); r.font.name = "Arial"; r.font.color.rgb = DARK

def bullet(doc, text):
    p   = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(text)
    run.font.size = Pt(10.5); run.font.name = "Arial"; run.font.color.rgb = DARK

def add_image(doc, filename, width_in=6.3):
    path = os.path.join(PLOTS, filename)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(2)
    p.add_run().add_picture(path, width=Inches(width_in))

def caption(doc, text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(10)
    for r in p.runs:
        r.italic = True; r.font.size = Pt(9)
        r.font.color.rgb = GREY; r.font.name = "Arial"

def add_table(doc, headers, rows, col_widths_in):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    hrow = t.rows[0]
    for i, (h, w) in enumerate(zip(headers, col_widths_in)):
        cell = hrow.cells[i]; cell.width = Inches(w)
        set_cell_bg(cell, "1565C0"); set_cell_borders(cell)
        p = cell.paragraphs[0]; p.clear()
        run = p.add_run(h); run.bold = True
        run.font.color.rgb = WHITE; run.font.size = Pt(10); run.font.name = "Arial"
    for ri, row_data in enumerate(rows):
        row = t.rows[ri + 1]
        bg  = "F5F9FF" if ri % 2 == 0 else "FFFFFF"
        for ci, (val, w) in enumerate(zip(row_data, col_widths_in)):
            cell = row.cells[ci]; cell.width = Inches(w)
            set_cell_bg(cell, bg); set_cell_borders(cell)
            p = cell.paragraphs[0]; p.clear()
            run = p.add_run(val)
            run.font.size = Pt(10); run.font.name = "Arial"; run.font.color.rgb = DARK
    doc.add_paragraph()

# ── Build document ─────────────────────────────────────────────────────────────

doc = Document()
for section in doc.sections:
    section.top_margin    = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin   = Inches(1.1)
    section.right_margin  = Inches(1.1)

# ── Title ──────────────────────────────────────────────────────────────────────
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(24)
p.paragraph_format.space_after  = Pt(4)
r = p.add_run("Gait Anomaly Detection System")
r.bold = True; r.font.size = Pt(26); r.font.color.rgb = BLUE; r.font.name = "Arial"

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(4)
r = p.add_run("Technical Overview: Waveforms, FFT Preprocessing, Autoencoder Architecture & Enrolment")
r.font.size = Pt(12); r.font.color.rgb = GREY; r.font.name = "Arial"

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(18)
r = p.add_run("June 2026")
r.font.size = Pt(10); r.font.color.rgb = GREY; r.font.name = "Arial"

add_rule(doc)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Simulated Gait Waveforms
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, "1.  Simulated Gait Waveforms")
body(doc, "The system simulates a 3-axis accelerometer mounted on the lower back at 50 Hz. Each axis captures a different component of the walking motion:")
bullet(doc, "acc_x — forward/backward oscillation as the body's centre of mass pitches")
bullet(doc, "acc_y — lateral (mediolateral) sway")
bullet(doc, "acc_z — vertical oscillation, the dominant signal during walking (largest amplitude)")
body(doc, "Five distinct gait patterns are modelled. Each uses a sinusoidal base signal with physiologically motivated parameters, plus Gaussian noise to approximate real sensor noise.")

add_image(doc, "comparison_vertical.png", width_in=6.3)
caption(doc, "Figure 1 — Vertical acceleration (acc_z) for all five gait types over 4 seconds.")

h2(doc, "1.1  Normal Walking")
body(doc, "Step frequency: ~1.9 Hz (cadence ~114 steps/min). The vertical axis shows a strong fundamental and a second harmonic at double frequency, reflecting heel-strike followed by toe-off within each step cycle.")
add_image(doc, "normal_walking_waveform.png", width_in=6.3)
caption(doc, "Figure 2 — Normal walking: regular, symmetric oscillations across all three axes.")

h2(doc, "1.2  Limping")
body(doc, "Step frequency: ~1.7 Hz. Every alternate step has a significantly reduced amplitude (modelled by a half-step-rate modulator), creating a characteristic paired pattern — one strong step followed by one weak step.")
add_image(doc, "limping_waveform.png", width_in=6.3)
caption(doc, "Figure 3 — Limping: alternating high/low amplitude steps produce an asymmetric envelope.")

h2(doc, "1.3  Shuffling")
body(doc, "Step frequency: ~1.4 Hz. The vertical oscillation amplitude is reduced by approximately 80% compared to normal walking, reflecting the reduced heel clearance and lack of push-off characteristic of shuffling gait.")
add_image(doc, "shuffling_waveform.png", width_in=6.3)
caption(doc, "Figure 4 — Shuffling: minimal vertical oscillation; signal barely deviates from the gravity baseline.")

h2(doc, "1.4  Running")
body(doc, "Step frequency: ~2.8 Hz. Both frequency and amplitude increase substantially. Peak vertical acceleration reaches ~3.5 g (versus ~1.7 g during normal walking), and a strong second harmonic is present from the hard foot-strike.")
add_image(doc, "running_waveform.png", width_in=6.3)
caption(doc, "Figure 5 — Running: higher cadence and much larger amplitude than normal walking.")

h2(doc, "1.5  Ataxic")
body(doc, "Ataxic gait is modelled with a phase-jitter process: the instantaneous frequency is randomly perturbed at each time step via a cumulative noise term, and amplitude fluctuates randomly, producing an irregular and unpredictable waveform.")
add_image(doc, "ataxic_waveform.png", width_in=6.3)
caption(doc, "Figure 6 — Ataxic: irregular timing and variable amplitude distinguish it from all periodic patterns.")

add_rule(doc)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — FFT Preprocessing Pipeline
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, "2.  FFT Preprocessing Pipeline")
body(doc, "Before being fed into the encoder, each raw accelerometer window passes through a three-stage preprocessing pipeline. The same pipeline is implemented identically in Python (generate_gait_data.py) and Kotlin (GaitFeatureExtractor.kt + FFT.kt) to ensure the on-device feature distribution exactly matches training.")

add_image(doc, "preprocessing_pipeline.png", width_in=6.5)
caption(doc, "Figure 7 — The three preprocessing stages applied to the vertical axis of a normal walking window.")

h2(doc, "2.1  Stage 1 — Z-score normalisation  (scale invariance)")
body(doc, "Each axis of the 128-sample window is independently Z-score normalised:")
body(doc, "        x_norm = ( x  −  mean(x) )  /  std(x)")
body(doc, "This removes any DC offset and amplitude scaling due to walking speed, step length, or sensor gain differences between individuals and sessions. After this step the signal always has zero mean and unit variance regardless of how energetically the person walks. Because the mean is zero, the DC component of the subsequent FFT (bin 0) is always zero and carries no information.")

h2(doc, "2.2  Stage 2 — FFT magnitude spectrum  (phase invariance)")
body(doc, "The real FFT of the normalised window is computed, producing 65 complex coefficients (bins 0 to 64 for a 128-point transform at 50 Hz, giving a frequency resolution of 50/128 ≈ 0.39 Hz per bin). Only the magnitude |FFT(x_norm)| is retained:")
body(doc, "        mag[k]  =  | FFT(x_norm)[k] |")
body(doc, "Discarding the phase information makes the feature vector invariant to the exact timing offset of the gait cycle within the window. Two windows that capture identical stepping motion but starting at different points in the stride cycle will produce the same magnitude spectrum, and therefore the same embedding.")

h2(doc, "2.3  Stage 3 — Frequency tuning  (frequency invariance)")
body(doc, "Different people walk at different cadences (typically 100–140 steps/min), and the same person may vary their cadence between sessions. Without correction, these cadence differences would shift all harmonic peaks to different FFT bins, causing large L2 distances between embeddings of the same person walking at slightly different speeds.")
body(doc, "The tuning step resamples the magnitude spectrum so that the dominant (fundamental) frequency peak always lands at a fixed reference bin K_REF = 5, corresponding to approximately 1.95 Hz:")
bullet(doc, "Find the fundamental: locate the peak magnitude bin k_fund by searching within bins [2, 20] (0.78–7.8 Hz), covering slow shuffle to fast running.")
bullet(doc, "Compute the scale factor: scale = K_REF / k_fund. For a runner (k_fund = 7): scale = 5/7 = 0.714 (spectrum compressed). For a shuffler (k_fund = 4): scale = 5/4 = 1.25 (spectrum stretched).")
bullet(doc, "Resample via linear interpolation: output bin k samples the original spectrum at position k / scale. This maps the fundamental to K_REF and all subsequent harmonics to 2·K_REF, 3·K_REF, etc., regardless of the original cadence.")
bullet(doc, "Retain the first N_OUT = 32 bins of the tuned spectrum (capturing the fundamental plus up to six harmonics).")

add_image(doc, "frequency_tuning_comparison.png", width_in=6.5)
caption(doc, "Figure 8 — Left: raw FFT spectra for all gait types — fundamentals at different frequencies. Right: after tuning, all fundamentals are aligned to bin 5 and harmonics to multiples of 5.")

body(doc, "The 32 tuned bins are computed for each of the three axes (x, y, z) and concatenated to form the final 96-element feature vector fed to the encoder.")

add_rule(doc)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Autoencoder & Encoder
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, "3.  Autoencoder Architecture & Encoder Export")

h2(doc, "3.1  Training objective")
body(doc, "An autoencoder is trained to reconstruct its input from a compressed bottleneck representation. When trained exclusively on normal gait data, the bottleneck learns a compact manifold of normal gait in feature space. The encoder half of this network — the path from input to bottleneck — is the component used at runtime. It maps the 96-dimensional FFT feature vector to a 12-dimensional embedding vector that captures the essential character of a person's gait pattern.")

h2(doc, "3.2  Architecture")
body(doc, "The full autoencoder uses a symmetric dense architecture:")
add_image(doc, "autoencoder_architecture.png", width_in=6.3)
caption(doc, "Figure 9 — Full autoencoder architecture. Only the shaded encoder portion (left of bottleneck) is exported as gait_encoder.tflite. The decoder is used only during training.")

add_table(doc,
    headers=["Layer", "Neurons", "Activation", "Role"],
    rows=[
        ["Input",              "96",  "—",      "3 axes × 32 tuned FFT bins"],
        ["Encoder Dense 1",    "48",  "ReLU",   "First compression"],
        ["Encoder Dense 2",    "24",  "ReLU",   "Second compression"],
        ["Bottleneck",         "12",  "ReLU",   "Gait identity embedding  ← exported"],
        ["Decoder Dense 1",    "24",  "ReLU",   "Training only"],
        ["Decoder Dense 2",    "48",  "ReLU",   "Training only"],
        ["Output",             "96",  "Linear", "Training only (reconstruction)"],
    ],
    col_widths_in=[1.7, 1.1, 1.2, 2.8]
)

h2(doc, "3.3  Training data")
body(doc, "The autoencoder is trained exclusively on normal gait data from 100 simulated subjects, each with a slightly different step frequency (1.7–2.1 Hz), using MSE reconstruction loss. No anomalous gait is presented during training. After training, the FFT feature vectors are Z-score normalised using training-set statistics, which are exported as scaler_params.json alongside the model.")

h2(doc, "3.4  Model evaluation")
body(doc, "After training, the encoder is evaluated by building an enrolment template from the first half of a held-out normal gait recording and computing L2 distances for all gait types against that template. The figure below shows both the resulting distance distributions and the training convergence curve.")

add_image(doc, "evaluation.png", width_in=6.5)
caption(doc, "Figure 10 — Left: L2 distance distributions from the enrolled template for each gait type, with the suggested threshold (mean + 3σ of normal distances) shown as a red dashed line. Right: MSE reconstruction loss during training.")

h2(doc, "3.4.1  Reading the L2 distance histogram")
body(doc, "The left panel is the most important diagnostic plot for the system. Each bar represents one feature window from the test set, and its position on the x-axis is its L2 distance from the normal gait template.")
bullet(doc, "Normal (blue) — tightly clustered near zero (L2 ≈ 2–5). The encoder has learned to map the user’s own gait to a compact, consistent region of embedding space. All normal windows fall well below the threshold of 7.05.")
bullet(doc, "Running (purple) — also clusters tightly, but at a slightly higher distance (≈5–6). Running shares many structural features with normal walking (regular periodicity, similar harmonic structure after frequency tuning), so the encoder places it close to the normal manifold — but still mostly below threshold, indicating it would not be reliably flagged by this particular threshold setting.")
bullet(doc, "Limping (pink) — spreads across L2 ≈8–25, almost entirely above the threshold. The asymmetric amplitude envelope introduced by the limp is clearly captured by the encoder as a departure from normal gait.")
bullet(doc, "Shuffling (yellow) — widely distributed from L2 ≈10 to 40+. The dramatically reduced vertical oscillation and slower cadence place shuffling embeddings far from the normal template, making it the most distinguishable anomaly.")
bullet(doc, "Ataxic (green) — the most spread-out distribution (L2 ≈15–40). The irregular phase and variable amplitude make each window land in a different region of embedding space, producing high and inconsistent distances from the template.")

h2(doc, "3.4.2  Reading the training curve")
body(doc, "The right panel shows MSE reconstruction loss against epoch for both the training set (blue) and validation set (orange).")
bullet(doc, "Both curves drop steeply in the first ∸10 epochs as the autoencoder learns the dominant structure of normal gait (the fundamental frequency and its harmonics in the tuned FFT spectrum).")
bullet(doc, "The train and validation curves remain close throughout, with no sign of overfitting — the small gap between them is expected and healthy.")
bullet(doc, "Loss plateaus around epoch 40–50 before early stopping triggers. The final validation MSE of ≈0.53 reflects the residual within-class variation in normal gait across 100 synthetic subjects.")
bullet(doc, "A lower reconstruction loss does not always mean a better embedding space for identity discrimination. The loss here serves only to ensure the encoder captures meaningful structure; the L2 distance histogram is the true measure of separation quality.")

h2(doc, "3.5  On-device deployment")
body(doc, "Only the encoder sub-model is exported to TFLite (gait_encoder.tflite). This takes the 96-element normalised feature vector as input and outputs the 12-element bottleneck embedding. The decoder is discarded after training. This keeps the on-device model small and inference fast — no reconstruction pass is needed at runtime.")

add_rule(doc)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Enrolment Session
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, "4.  The Enrolment Session")

h2(doc, "4.1  Purpose")
body(doc, "Enrolment captures a personalised template of the user's gait in the 12-dimensional embedding space. Because the encoder has been trained on population-level normal gait, embeddings for different individuals will cluster in different regions of this space. The template anchors the decision boundary to the specific person, enabling the system to distinguish between that individual (genuine) and anyone else with a different gait pattern (imposter).")

h2(doc, "4.2  What happens during enrolment")
body(doc, "The user initiates a 30-second enrolment session of simulated normal walking. For each 128-sample window (produced every 1.28 s with 50% overlap):")
bullet(doc, "The GaitSimulator produces accelerometer samples at 50 Hz.")
bullet(doc, "Each window is accumulated in a SampleBuffer and dispatched when full.")
bullet(doc, "GaitFeatureExtractor applies the full three-stage pipeline: Z-score normalise → |FFT| → frequency tune → 96-element vector.")
bullet(doc, "GaitAutoencoder normalises the feature vector using scaler_params.json, then runs a forward pass through the encoder to produce a 12-dimensional embedding.")
bullet(doc, "All embeddings are collected into a list (~46 embeddings over 30 s).")
body(doc, "After 30 seconds the session ends and the template is computed.")

h2(doc, "4.3  Template construction")
body(doc, "The template is the element-wise (vector) mean of all collected embeddings:")
body(doc, "        template[d]  =  (1/N)  ·  Σ  embedding_i[d]     for d = 0 … 11")
body(doc, "Taking the mean averages out within-session noise and stride-to-stride variation, producing a stable centroid in embedding space that represents the user's typical gait. If multiple enrolment sessions were provided, the same average could be taken across all sessions to build a more robust template.")

h2(doc, "4.4  Threshold calibration")
body(doc, "Once the template is fixed, the L2 distance from each individual enrollment embedding to the template is computed:")
body(doc, "        dist_i  =  ||  embedding_i  −  template  ||₂")
body(doc, "These distances characterise the natural spread of the user's own gait around their template. The personal threshold is set to:")
body(doc, "        threshold  =  mean(dist)  +  3 · std(dist)")
body(doc, "Under a Gaussian assumption this captures 99.7% of genuine presentations, limiting the false rejection rate (FRR) to ~0.15%. The multiplier (SIGMA_MULTIPLIER = 3 in EnrollmentActivity.kt) is tunable: reducing it tightens the boundary and increases sensitivity to subtle anomalies, at the cost of more false rejections of the genuine user.")
body(doc, "Both the template vector and the threshold are persisted to Android SharedPreferences (template as a JSON float array, threshold as a float).")

h2(doc, "4.5  What changes after enrolment")
body(doc, "Nothing in the encoder weights is modified. The model continues to use the same learned embedding space; only the reference point (template) and decision boundary (threshold) are personalised. This means:")
bullet(doc, "Enrolment requires only ~46 encoder forward passes and basic vector arithmetic — it completes in under a second after the 30-second data collection.")
bullet(doc, "Population-level generalisation of the encoder is preserved; the model is not overfit to one person.")
bullet(doc, "Re-enrolment is trivial if the user's gait changes permanently (e.g. after surgery or rehabilitation).")

h2(doc, "4.6  Detection after enrolment")
body(doc, "During a detection session, each new feature window is encoded to a 12-dimensional embedding and the L2 distance to the stored template is computed in real time. The DetectionActivity displays:")
bullet(doc, "The raw L2 distance as a numerical score.")
bullet(doc, "A progress bar normalised to 3× the threshold (genuine presentations stay in the lower third).")
bullet(doc, "A scrolling history chart with a red dashed threshold line.")
bullet(doc, "A status label: 'Genuine' when L2 ≤ threshold, 'Imposter' when L2 > threshold.")
body(doc, "Users can switch between all five simulated gait types via the spinner to observe the score rise for patterns dissimilar to their enrolled template.")

add_rule(doc)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Quick Reference
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, "5.  Quick Reference")

add_table(doc,
    headers=["Parameter", "Value"],
    rows=[
        ["Sample rate",                "50 Hz"],
        ["Window size",                "128 samples  (2.56 s)"],
        ["Window stride",              "64 samples  (50% overlap)"],
        ["Preprocessing stage 1",      "Z-score normalise per axis  (scale invariance)"],
        ["Preprocessing stage 2",      "|FFT|  magnitude spectrum  (phase invariance)"],
        ["Preprocessing stage 3",      "Resample to align fundamental to K_REF = 5  (frequency invariance)"],
        ["FFT bins per axis",           "32  (tuned, bins 0–31)"],
        ["Feature vector size",        "96  (3 axes × 32 bins)"],
        ["Autoencoder architecture",   "96 → 48 → 24 → 12 → 24 → 48 → 96"],
        ["Embedding (bottleneck) size","12 neurons"],
        ["On-device model file",       "gait_encoder.tflite  (encoder only)"],
        ["Training data",              "100 synthetic subjects, normal gait only"],
        ["Enrolment duration",         "30 seconds  (~46 embedding windows)"],
        ["Template",                   "Vector mean of all enrolment embeddings"],
        ["Anomaly score",              "L2 distance: || embedding − template ||₂"],
        ["Threshold formula",          "mean(L2) + 3σ  of enrolment distances"],
        ["Genuine / Imposter",         "L2 ≤ threshold  /  L2 > threshold"],
        ["On-device weight update",    "None — template & threshold calibration only"],
        ["Supported gait types",       "Normal, Limping, Shuffling, Running, Ataxic"],
    ],
    col_widths_in=[2.5, 4.3]
)

# ── Save ───────────────────────────────────────────────────────────────────────
doc.save(OUT)
print(f"Saved: {os.path.abspath(OUT)}")
