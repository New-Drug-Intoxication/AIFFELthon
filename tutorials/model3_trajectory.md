# Biomni Agent Conversation History

#### Human Prompt

*Plan a CRISPR screen to identify genes that regulate T cell exhaustion,
        measured by the change in T cell receptor (TCR) signaling between acute
        (interleukin-2 [IL-2] only) and chronic (anti-CD3 and IL-2) stimulation conditions.
        Generate 32 genes that maximize the perturbation effect.*

#### Step 1

<div class="title-text summary">
<div class="title-text-header">
<strong>Summary and Solution</strong>
</div>
<div class="title-text-content">
Thought process:
- You want a focused, high-signal pooled CRISPR knockout screen in primary human T cells that uses a TCR signaling reporter to capture the difference between an IL-2–only (acute/no TCR) versus anti-CD3 + IL-2 (chronic/TCR-engaged) condition. 
- To maximize perturbation effect, we should include: (i) transcriptional programs that drive exhaustion; (ii) coinhibitory receptors and their proximal adaptors/phosphatases; (iii) canonical negative regulators of TCR signaling and anergy nodes; and (iv) a small set of strong positive TCR signaling nodes to generate a broad dynamic range in both directions. 
- A pooled, FACS-based reporter screen with high/low bin sorting and NGS deconvolution (MAGeCK) is optimal. 

Plan and progress:
<div class="title-text plan">
<div class="title-text-header">
<span class="plan-title">Plan</span>
</div>
<div class="title-text-content">
<ul>
<li><strong>[x]</strong> Define the screen objective and measurable phenotype (completed)</li>
</ul>
</div>
</div>
   - Objective: Identify genes whose loss alters the change in TCR signaling between acute (IL-2 only) and chronic (anti-CD3 + IL-2) conditions, thus regulating T cell exhaustion/adaptation to persistent stimulation. 
   - Primary phenotype: Delta in reporter signal (e.g., NFAT/AP-1 response element-driven fluorescent reporter) under chronic versus acute stimulation (ΔTCR = reporterchronic − reporteracute). 
   - Secondary phenotypes (optional): viability, proliferation (e.g., CFSE/CTV dilution), activation markers (CD69, CD25), inhibitory receptor expression (PD-1, TIM-3), and cytokine output.

<div class="title-text plan">
<div class="title-text-header">
<span class="plan-title">Plan</span>
</div>
<div class="title-text-content">
<ul>
<li><strong>[x]</strong> Choose experimental system and assay (completed)</li>
</ul>
</div>
</div>
   - Cells: Primary human CD8+ T cells from ≥3 donors (biological replicates), purified by negative selection.
   - Screen modality: Pooled CRISPR-Cas9 knockout using a focused sgRNA library (6 sgRNAs/gene) + controls; deliver sgRNAs by lentivirus at low MOI (~0.3) and Cas9 as mRNA or protein (RNP) post-transduction, or use lentiCas9-blast pre-engineered T cells.
   - Reporter: NFAT:AP-1 composite response element driving destabilized GFP (e.g., d2GFP) in a lentiviral vector; alternatively, a dual NFAT and NF-κB reporter for broader capture of TCR signaling.
   - Stimulation and timeline:
     - Day 0: Transduce sgRNA library + reporter at low MOI (keep ≥500–1000× coverage per sgRNA).
     - Day 2: Select/expand lightly (avoid strong pre-activation).
     - Day 5–7: Electroporate Cas9 mRNA/RNP (if not using Cas9-stable cells).
     - Day 10–12: Split into two matched conditions for 16–24 h:
       - Acute: IL-2 only (e.g., 50–100 IU/mL), no TCR crosslinking.
       - Chronic: plate-bound anti-CD3 (e.g., OKT3, 1–5 μg/mL) + IL-2; optionally include submaximal anti-CD28 to mimic tonic co-stimulation if desired; validate titration to induce partial signaling attenuation/exhaustion features without full activation saturation.
   - Readout and sorting:
     - Measure reporter fluorescence; compute ΔTCR per cell context via parallel cultures.
     - Sort the top 10–15% (High-Δ bin; enhanced signaling under chronic) and bottom 10–15% (Low-Δ bin; blunted signaling under chronic) from the chronic-stimulated arm relative to a same-day acute arm baseline.
     - Maintain depth: >500× sgRNA coverage per bin.
   - Sequencing and analysis:
     - Extract genomic DNA, PCR amplify sgRNA cassettes, sequence.
     - Use MAGeCK to identify sgRNAs/genes enriched in High-Δ (anti-exhaustion hits) and Low-Δ (pro-exhaustion or TCR-positive-node hits).

<div class="title-text plan">
<div class="title-text-header">
<span class="plan-title">Plan</span>
</div>
<div class="title-text-content">
<ul>
<li><strong>[x]</strong> Construct the 32-gene set to maximize perturbation (completed)</li>
</ul>
</div>
</div>
   Selection rationale:
   - Enrich for: exhaustion-driving TFs (whose KO relieves exhaustion and boosts ΔTCR), coinhibitory receptors and their phosphatase/adaptor hubs (whose KO increases ΔTCR), and canonical negative regulators/anergy effectors (whose KO increases ΔTCR). 
   - Include a minority of strong positive TCR signaling nodes (whose KO will collapse ΔTCR) to create dynamic range and provide internal positive/negative controls for the analytical pipeline.

   32 prioritized genes (grouped by mechanism):
   A) Exhaustion-driving transcriptional program (10)
   - TOX
   - NR4A1
   - NR4A2
   - NR4A3
   - BATF
   - IRF4
   - PRDM1
   - IKZF2
   - EGR2
   - EGR3

   B) Coinhibitory receptors and immune checkpoints (8)
   - PDCD1 (PD-1)
   - CTLA4
   - LAG3
   - TIGIT
   - HAVCR2 (TIM-3)
   - CD244 (2B4)
   - LAIR1
   - BTLA

   C) Proximal negative regulators of TCR signaling, phosphatases/adaptors (10)
   - CBLB
   - CBL
   - PTPN22
   - PTPN6 (SHP-1)
   - PTPN11 (SHP-2)
   - INPP5D (SHIP1)
   - CSK
   - UBASH3A (STS-2)
   - UBASH3B (STS-1)
   - DOK2

   D) Anergy/DAG-Ca2+ signaling nodes to span dynamic range (4)
   - DGKA
   - DGKZ
   - PPP3CA (Calcineurin catalytic subunit)
   - NFATC1

   Expected directions (for interpretation):
   - High-Δ bin enrichment (enhanced signaling under chronic): KO of A, B, C, and DGK genes typically increase TCR output under persistent stimulation and relieve exhaustion/anergy.
   - Low-Δ bin enrichment (blunted signaling): KO of PPP3CA or NFATC1 (core Ca2+/NFAT axis) serves as strong positive controls for reduced TCR signaling under chronic stimulation; these also benchmark assay dynamic range.

<div class="title-text plan">
<div class="title-text-header">
<span class="plan-title">Plan</span>
</div>
<div class="title-text-content">
<ul>
<li><strong>[x]</strong> Library design, controls, and QC plan (completed)</li>
</ul>
</div>
</div>
   - Guides: 6 sgRNAs/gene × 32 genes = 192 guides.
   - Non-targeting controls: ≥100 sgRNAs (disperse across vector).
   - Positive controls (reduced signaling): LCK, ZAP70, LAT, PLCG1 (2–3 sgRNAs each or include as tracking spikes) to confirm Low-Δ enrichment works and to calibrate effect size.
   - Positive controls (enhanced signaling): Additional CBLB-targeting sgRNAs and DGKA/DGKZ to ensure High-Δ detection.
   - Coverage: ≥500–1000× per sgRNA per arm and per bin.
   - MOI: ~0.3 to keep single perturbations/cell.
   - Replicates: ≥2 technical sorts per donor, ≥3 donor replicates.
   - Batch controls: Spike-in of a known high-effect barcode (e.g., CBLB KO) for run-to-run normalization.

<div class="title-text plan">
<div class="title-text-header">
<span class="plan-title">Plan</span>
</div>
<div class="title-text-content">
<ul>
<li><strong>[x]</strong> Data analysis and hit calling strategy (completed)</li>
</ul>
</div>
</div>
   - Compute enrichment scores with MAGeCK for High-Δ and Low-Δ bins vs unsorted/mid bin.
   - Aggregate sgRNA-level effects to gene-level robust statistics; require ≥3 sgRNAs supporting direction with FDR < 0.1 across donors.
   - Rank “anti-exhaustion” hits by consistency, effect size, and donor concordance in High-Δ; “pro-exhaustion/TCR-positive” by Low-Δ.
   - Secondary filters: viability-adjusted effects (exclude broad cytotoxic hits), expression in T cells (e.g., from proteinatlas or single-cell references), and absence of strong proliferation artifacts in IL-2-only arm.

<div class="title-text plan">
<div class="title-text-header">
<span class="plan-title">Plan</span>
</div>
<div class="title-text-content">
<ul>
<li><strong>[x]</strong> Validation roadmap (completed)</li>
</ul>
</div>
</div>
   - Arrayed RNP knockout for top 8–12 hits (e.g., CBLB, PTPN22, NR4A1/2/3, TOX, DGKA/DGKZ, PDCD1) in fresh donors.
   - Reconfirm ΔTCR with reporter; orthogonal readouts: pERK/pS6 flow after chronic stimulation; cytokines (IFN-γ, TNF); durability of function after 3–5 days of repeated stimulation.
   - Transcriptional profiling (bulk RNA-seq or targeted panel) to verify reversal of exhaustion signature and maintenance of T cell identity.

Deliverable: 32 genes for the screen
- TOX; NR4A1; NR4A2; NR4A3; BATF; IRF4; PRDM1; IKZF2; EGR2; EGR3
- PDCD1; CTLA4; LAG3; TIGIT; HAVCR2; CD244; LAIR1; BTLA
- CBLB; CBL; PTPN22; PTPN6; PTPN11; INPP5D; CSK; UBASH3A; UBASH3B; DOK2
- DGKA; DGKZ; PPP3CA; NFATC1

Notes and cautions:
- Reporter neutrality: Avoid reporters driven by NR4A promoters (e.g., Nur77-GFP), since NR4A KOs are in the library and could confound readout. Use composite NFAT/AP-1 or NF-κB elements instead.
- Titration: Ensure chronic anti-CD3 dose yields measurable attenuation compared with acute baseline to avoid ceiling/floor effects.
- Donor variability: Include multiple donors and mixed-effects modeling if feasible.
- Off-targets: Use multiple sgRNAs/gene and concordance filters; optionally test at least one orthogonal sgRNA per top hit in validation.
- Safety: Some perturbations (e.g., PRDM1, IKZF2) can alter differentiation profoundly; monitor phenotype and apoptosis to decouple signal vs survival artifacts.

Updated checklist
<div class="title-text plan">
<div class="title-text-header">
<span class="plan-title">Plan</span>
</div>
<div class="title-text-content">
<ul>
<li><strong>[x]</strong> Define the screen objective and measurable phenotype (completed)</li>
<li><strong>[x]</strong> Choose experimental system and assay (completed)</li>
<li><strong>[x]</strong> Construct the 32-gene set to maximize perturbation (completed)</li>
<li><strong>[x]</strong> Library design, controls, and QC plan (completed)</li>
<li><strong>[x]</strong> Data analysis and hit calling strategy (completed)</li>
<li><strong>[x]</strong> Validation roadmap (completed)</li>
</ul>
</div>
</div>
</div>
</div>

