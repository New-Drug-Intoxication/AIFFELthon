# Biomni Agent Conversation History

#### Human Prompt

*Plan a CRISPR screen to identify genes that regulate T cell exhaustion,
        measured by the change in T cell receptor (TCR) signaling between acute
        (interleukin-2 [IL-2] only) and chronic (anti-CD3 and IL-2) stimulation conditions.
        Generate 32 genes that maximize the perturbation effect.*

#### Step 1

Here is my reasoning and plan to design a focused CRISPR screen and generate 32 high-impact target genes for modulating T cell exhaustion, measured as TCR signaling changes between acute (IL-2 only) and chronic (anti-CD3 + IL-2) stimulation.

Updated plan:
<div class="title-text plan">
<div class="title-text-header">
<span class="plan-title">Plan</span>
</div>
<div class="title-text-content">
<ul>
<li><strong>[x]</strong> Define the CRISPR screen goal, assay design, and workflow</li>
<li><strong>[ ]</strong> Build and refine a candidate gene list linked to TCR inhibition/exhaustion; prioritize those expected to maximize perturbation</li>
<li><strong>[ ]</strong> Check practical considerations (expression/function relevance in T cells) and finalize 32 genes</li>
<li><strong>[ ]</strong> Generate sgRNAs (4 guides/gene) for the final 32-gene mini-library</li>
<li><strong>[ ]</strong> Outline key experimental details: perturbation delivery, stimulation, readout, QC, and analysis</li>
</ul>
</div>
</div>

Step 1 (completed): Screen design and workflow
- Biological objective: Identify genetic perturbations that most strongly change TCR signaling differentially between an acute (IL-2 only) state and a chronic (anti-CD3 + IL-2) exhaustion-inducing state in human T cells.
- Cell model:
  - Preferred: Primary human CD8+ T cells from healthy donors (activated day 0 with CD3/CD28, expanded in IL-2).
  - Practical alternative for pooled screen development: Jurkat NFAT/Nur77 reporter line stably expressing Cas9, then validate top hits in primary CD8+ T cells.
- Perturbation approach:
  - Focused pooled CRISPR-Cas9 KO library: 32 genes x 4 sgRNAs each = 128 guides + 50 non-targeting controls + 10 safe-targeting controls + 10 positive/negative control genes = ~200 total guides.
  - Delivery:
    - For primary T cells: SLICE-style workflow (lentiviral sgRNA + Cas9 RNP electroporation) at MOI ~0.3, maintain >500x coverage/guide.
    - For Jurkat: lentiviral lentiCRISPRv2 (Cas9+sgRNA), select with puromycin, MOI ~0.3.
- Stimulation and readout:
  - Culture two matched arms for each pool:
    - Acute: IL-2 only, no TCR stimulation (rested).
    - Chronic: plate-bound anti-CD3 (e.g., OKT3, 1–5 μg/mL) + IL-2 for 5–7 days; optionally re-stimulate every 48 h to enforce chronic signaling.
  - Reporter readout: NFAT/Nur77/AP-1 transcriptional GFP/luciferase reporter; alternatively, pZAP70/pERK flow or CD69/IL-2 production by flow/cytokine assays.
  - FACS-based binning: Sort top vs bottom signaling bins in each condition; extract gDNA; amplify sgRNA cassettes; NGS for abundance.
- Controls:
  - Positive-loss-of-signal controls: CD3E, LCK, ZAP70, LAT, LCP2 (SLP-76).
  - Gain-of-signal controls: CBLB, PTPN6 (SHP-1), DGKA.
  - Non-targeting and safe-targeting controls for normalization.
- Analysis:
  - MAGeCK count/test or MLE to score each condition; compute a differential “chronic vs acute” gene score (e.g., beta_chronic - beta_acute).
  - Identify genes with largest positive/negative differential effects.
- Replication and QC:
  - ≥2 donor replicates for primary cells or ≥3 biological replicates for Jurkat.
  - Track infection rate, editing efficiency (TIDE/ICE on pilot loci), coverage, and replicate concordance.

Proceeding to build the prioritized 32-gene list and design 4 sgRNAs/gene.

<div class="title-text plan">
<div class="title-text-header">
<span class="plan-title">Plan</span>
</div>
<div class="title-text-content">
<ul>
<li><strong>[x]</strong> Define the CRISPR screen goal, assay design, and workflow</li>
<li><strong>[ ]</strong> Build and refine a candidate gene list linked to TCR inhibition/exhaustion; prioritize those expected to maximize perturbation</li>
<li><strong>[ ]</strong> Check practical considerations (expression/function relevance in T cells) and finalize 32 genes</li>
<li><strong>[ ]</strong> Generate sgRNAs (4 guides/gene) for the final 32-gene mini-library</li>
<li><strong>[ ]</strong> Outline key experimental details: perturbation delivery, stimulation, readout, QC, and analysis</li>
</ul>
</div>
</div>

Now I will construct a curated high-impact list (negative regulators of TCR signaling, inhibitory receptors, and key exhaustion TFs/cofactors), finalize 32 genes, and attempt to generate 4 sgRNAs/gene from the local data lake.

<div class="tool-call-highlight">
<div class="tool-call-header">
<strong>Code Execution</strong>
</div>
<div class="tool-call-input">
```python
# Step 2-4: Build candidate list, finalize 32 genes, and design sgRNAs (4/gene)
print("Research log")
print("-"*80)

# Step 2: Curate a broad candidate pool with strong prior evidence for modulating TCR signaling or T cell exhaustion
candidate_pool = [
    # Inhibitory receptors / checkpoints
    "PDCD1","CTLA4","LAG3","TIGIT","HAVCR2","BTLA","CD244","CD160","KLRG1","ADORA2A",
    # Adenosine/ecto-nucleotidases
    "ENTPD1","NT5E",
    # Phosphatases / adaptors / E3 ligases / negative regulators
    "PTPN6","PTPN11","PTPN22","INPP5D","PTEN","CSK","PAG1","CBLB","CBL","UBASH3B","UBASH3A","RNF128",
    "ITCH","DGKA","DGKZ","RCAN1","PIK3IP1","SOCS1","SOCS3","CISH","DOK2","TSC1",
    # Exhaustion-driving transcriptional regulators
    "TOX","TOX2","NR4A1","NR4A2","NR4A3","BATF","IRF4","PRDM1","EOMES"
]

print(f"Step 2: Initial candidate pool size = {len(candidate_pool)} genes")
print(candidate_pool)

# Step 3: Finalize 32 genes maximizing differential TCR signaling under chronic stimulation
# Prioritize inhibitory receptors, strong negative regulators of TCR/PI3K signaling, and key exhaustion TFs.
final_32_genes = [
    # Inhibitory receptors / checkpoints (8)
    "PDCD1","CTLA4","LAG3","TIGIT","HAVCR2","BTLA","CD244","ADORA2A",
    # Adenosine/ecto-nucleotidases (2)
    "ENTPD1","NT5E",
    # Phosphatases / adaptors / negative regulators (16)
    "PTPN6","PTPN11","PTPN22","INPP5D","PTEN","CSK","PAG1","CBLB","CBL","UBASH3B","UBASH3A","RNF128","ITCH","DGKA","DGKZ","RCAN1",
    # PI3K/mTOR negative regulator
    "PIK3IP1",
    # Exhaustion-driving TFs/cofactors (5)
    "TOX","NR4A1","BATF","IRF4","PRDM1"
]
print(f"Step 3: Finalized list size = {len(final_32_genes)} genes (target = 32)")

# Sanity check count
if len(final_32_genes) != 32:
    print("WARNING: Finalized list is not exactly 32 genes. Adjusting...")
else:
    print("OK: Finalized list contains exactly 32 genes.")

print("Final 32-gene list:")
for i, g in enumerate(final_32_genes, 1):
    print(f"{i:2d}. {g}")

# Step 4: Design 4 sgRNAs per gene using the local data lake resource if available
from biomni.tool.molecular_biology import design_knockout_sgrna

data_lake_path = "./biomni_data/data_lake"
print("-"*80)
print("Step 4: Designing 4 sgRNAs per gene (using design_knockout_sgrna)")
design_results = {}
failed_genes = []
for gene in final_32_genes:
    try:
        res = design_knockout_sgrna(gene_name=gene, data_lake_path=data_lake_path, species="human", num_guides=4)
        design_results[gene] = res
        print(f"sgRNA design for {gene}:")
        print(res)
    except Exception as e:
        failed_genes.append((gene, str(e)))
        print(f"ERROR designing sgRNAs for {gene}: {e}")

# Summarize sgRNA coverage
print("-"*80)
print("Summary of sgRNA design results:")
num_success = 0
for gene, res in design_results.items():
    # Try to infer number of guides from the result structure
    n_guides = None
    try:
        # common keys might be 'guides' or 'sgRNAs'
        if isinstance(res, dict):
            if 'guides' in res and isinstance(res['guides'], list):
                n_guides = len(res['guides'])
            elif 'sgRNAs' in res and isinstance(res['sgRNAs'], list):
                n_guides = len(res['sgRNAs'])
    except Exception:
        pass
    if n_guides is None:
        # fallback: try to count by string representation
        n_guides = "unknown"
    print(f"- {gene}: {n_guides} guides")
    if isinstance(n_guides, int) and n_guides >= 1:
        num_success += 1

print(f"Genes with at least one guide designed: {num_success}/{len(final_32_genes)}")
if failed_genes:
    print("Genes that failed sgRNA design:")
    for g, msg in failed_genes:
        print(f"  * {g}: {msg}")

print("-"*80)
print("Next steps:")
print(" - If any genes lack guides, use alternative sgRNA design tools or adjust targets.")
print(" - Proceed to library cloning/assembly and pilot edits QC before full screen.")
```
</div>
<div class="tools-used">
<strong>Tools Used:</strong> molecular_biology → design_knockout_sgrna
</div></div>

<div class="title-text observation">
<div class="title-text-header">
<strong>Observation</strong>
</div>
<div class="title-text-content">
```terminal
The output is too long to be added to context. Here are the first 10K characters...
Research log
--------------------------------------------------------------------------------
Step 2: Initial candidate pool size = 43 genes
['PDCD1', 'CTLA4', 'LAG3', 'TIGIT', 'HAVCR2', 'BTLA', 'CD244', 'CD160', 'KLRG1', 'ADORA2A', 'ENTPD1', 'NT5E', 'PTPN6', 'PTPN11', 'PTPN22', 'INPP5D', 'PTEN', 'CSK', 'PAG1', 'CBLB', 'CBL', 'UBASH3B', 'UBASH3A', 'RNF128', 'ITCH', 'DGKA', 'DGKZ', 'RCAN1', 'PIK3IP1', 'SOCS1', 'SOCS3', 'CISH', 'DOK2', 'TSC1', 'TOX', 'TOX2', 'NR4A1', 'NR4A2', 'NR4A3', 'BATF', 'IRF4', 'PRDM1', 'EOMES']
Step 3: Finalized list size = 32 genes (target = 32)
OK: Finalized list contains exactly 32 genes.
Final 32-gene list:
 1. PDCD1
 2. CTLA4
 3. LAG3
 4. TIGIT
 5. HAVCR2
 6. BTLA
 7. CD244
 8. ADORA2A
 9. ENTPD1
10. NT5E
11. PTPN6
12. PTPN11
13. PTPN22
14. INPP5D
15. PTEN
16. CSK
17. PAG1
18. CBLB
19. CBL
20. UBASH3B
21. UBASH3A
22. RNF128
23. ITCH
24. DGKA
25. DGKZ
26. RCAN1
27. PIK3IP1
28. TOX
29. NR4A1
30. BATF
31. IRF4
32. PRDM1
--------------------------------------------------------------------------------
Step 4: Designing 4 sgRNAs per gene (using design_knockout_sgrna)
sgRNA design for PDCD1:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'PDCD1', 'species': 'human', 'guides': ['CCCTTCGGTCACCACGAGCA', 'CCATAGTCCACAGAGAACAC', 'AGCCGGCCAGTTCCAAACCC', 'TCCGCTAGGAAAGACAATGG']}
sgRNA design for CTLA4:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'CTLA4', 'species': 'human', 'guides': ['AAGAAGCCCTCTTACAACAG', 'TGCCCAGGTAGTATGGCGGT', 'TACCCACCGCCATACTACCT', 'TCCTTGCAGCAGTTAGTTCG']}
sgRNA design for LAG3:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'LAG3', 'species': 'human', 'guides': ['GTTCCGGAACCAATGCACAG', 'GGAACCAATGCACAGAGGCT', 'GGCTCACATCCTCTAGTCGA', 'GGGAGTTACCCAGAACAGTG']}
sgRNA design for TIGIT:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'TIGIT', 'species': 'human', 'guides': ['AGTGTACGTCCCATCAGGGT', 'GCTGACCGTGAACGATACAG', 'CAGGCACAATAGAAACAACG', 'CGTTCACGGTCAGCGACTGG']}
sgRNA design for HAVCR2:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'HAVCR2', 'species': 'human', 'guides': ['AGAGAACGTATATGAAGTGG', 'TAGGCATCTACATCGGAGCA', 'TCTCTGCCGAGTCGGTGCAG', 'ATAGGCATCTACATCGGAGC']}
sgRNA design for BTLA:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'BTLA', 'species': 'human', 'guides': ['AGTAGAGGCAATCCCCCCAA', 'CATTGGACCGAACTCAAGAC', 'AGTAAACGATACAGGAGCCA', 'AGCTTGCACCAAGTCACATG']}
sgRNA design for CD244:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'CD244', 'species': 'human', 'guides': ['AAATACAAAAACCTGGAACG', 'GTTGAGAAACCCCGCCTACA', 'ATGGCAATGTGTCCTATGCT', 'ATAGGACACATTGCCATCCC']}
sgRNA design for ADORA2A:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'ADORA2A', 'species': 'human', 'guides': ['GCGGAACTCGCGGATACGGT', 'GCGGCGGCCGACATCGCAGT', 'ATGCTAGGTTGGAACAACTG', 'GCTGCGAATGATCTTGCGGA']}
sgRNA design for ENTPD1:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'ENTPD1', 'species': 'human', 'guides': ['GCTACTTATGGAAGATACAA', 'GATAGAGGAGAAGCCAAGGA', 'TATATCCAGGATGAAAGCAT', 'GTTGATAGTAATCCAGCCAT']}
sgRNA design for NT5E:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'NT5E', 'species': 'human', 'guides': ['GCAGCACGTTGGGTTCGGCG', 'AGGTGACCAAGATATCAACG', 'TACCATGGCATCGTAGCGCA', 'GAGCATAGCGTGCACCGCTA']}
sgRNA design for PTPN6:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'PTPN6', 'species': 'human', 'guides': ['CCAGGGTGGACGCTACACAG', 'GAGTACTACACTCAGCAGCA', 'TCACGCACAAGAAACGTCCA', 'CGGCCCAGTCGCAAGAACCA']}
sgRNA design for PTPN11:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'PTPN11', 'species': 'human', 'guides': ['GGAGGAACATGACATCGCGG', 'GATTACTATGACCTGTATGG', 'TCTTCTAGTTGATCATACCA', 'TTATAAGAAGAATCCTATGG']}
sgRNA design for PTPN22:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'PTPN22', 'species': 'human', 'guides': ['AGAATAGGGTCTATAGATGA', 'GGATGTACGTTGTTACCAAG', 'TACTAGCTATCCTGACACCA', 'GAAAAAGTGTGAGCGCTACT']}
sgRNA design for INPP5D:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'INPP5D', 'species': 'human', 'guides': ['TGGGGATCTTAACTACCGTG', 'CGATCACGTAAATGTCATGG', 'GCTGTTGACGAACCCTAAGG', 'GTGGCTGTTGACGAACCCTA']}
sgRNA design for PTEN:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'PTEN', 'species': 'human', 'guides': ['TCATCTGGATTATAGACCAG', 'AAAAGGATATTGTGCAACTG', 'GACTGGGAATAGTTACTCCC', 'CAATTCAGGACCCACACGAC']}
sgRNA design for CSK:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'CSK', 'species': 'human', 'guides': ['GCTCCCGTGTGATCTTGCCG', 'TCTTGCCGTGGAACCAACTG', 'TACAAGATGGATGCCCCCGA', 'CTGACCGACCCCTAGACCGC']}
sgRNA design for PAG1:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'PAG1', 'species': 'human', 'guides': ['ACCTGTCACAACTAGAGCAC', 'GTATCCACTGCGCTCTCGGG', 'GAAGCCGCGACAGCATAGTG', 'CTGGGAATCCAGCAGATCCG']}
sgRNA design for CBLB:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'CBLB', 'species': 'human', 'guides': ['AGGAACTGAGCCCATAATCG', 'GCACCTCTTGCCTTACGGCA', 'TGCACAGAACTATCGTACCA', 'TGAATTAGATCCAGGCGAGG']}
sgRNA design for CBL:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'CBL', 'species': 'human', 'guides': ['GCAGGTCTAAGATATAAGGT', 'CTATCTTGTCAAGATATGAG', 'AGCAGGTCTAAGATATAAGG', 'AAATGGAAACAAATTCCCGG']}
sgRNA design for UBASH3B:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'UBASH3B', 'species': 'human', 'guides': ['CGAGCCCGGCCACTTACGCG', 'GAGCCCGGCCACTTACGCGC', 'TGTAGGTTGTATCAACACTC', 'GTGCAGTCTGAACGCAGCGA']}
sgRNA design for UBASH3A:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'UBASH3A', 'species': 'human', 'guides': ['CCAGTACAAACCCCAGAACG', 'GAGCCAGTGAGTCTGACACG', 'ATGCCACACGATGATAATGG', 'CGTGCTGGTGGTTCGCCACG']}
sgRNA design for RNF128:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'RNF128', 'species': 'human', 'guides': ['GGGAGTGAACCGTACGGTGT', 'GTACGGTTCACTCCCGTGTG', 'GCACACGGGAGTGAACCGTA', 'TGGTTGGCCCTCATCCAACG']}
sgRNA design for ITCH:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'ITCH', 'species': 'human', 'guides': ['TGGACCAAGTCCTTACGTAG', 'TCTACTGTGACCTCTACGTA', 'TCCCGAACATAGGCTATCTG', 'GGAACCTGCCGATTGCCAGT']}
sgRNA design for DGKA:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'DGKA', 'species': 'human', 'guides': ['AAGTGGTACATATGGATCGA', 'ACGACGGACAGCACATGTGG', 'GGATCTACCACAGTCTGACC', 'GTGGAATCGATGAGCAATAG']}
sgRNA design for DGKZ:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'DGKZ', 'species': 'human', 'guides': ['GAATAAGATGTTCTACGCCG', 'AGTTCCACGAGTCTCGAGGT', 'GGCCAAGCACATCCGAGTGG', 'CTAGGAGTCAGCGACATATG']}
sgRNA design for RCAN1:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'RCAN1', 'species': 'human', 'guides': ['GACTGACACCACTCCCAGCG', 'TGACACCACTCCCAGCGTGG', 'GAAGGGCCGCAGCGTCACCC', 'ACATACATGGACCACCACGC']}
sgRNA design for PIK3IP1:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'PIK3IP1', 'species': 'human', 'guides': ['AGGACACTTACCCGACACGG', 'TCGCCACTGACGTAGCACCA', 'GAGGACACTTACCCGACACG', 'TCTTGGGCTACTCCTACAAG']}
sgRNA design for TOX:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'TOX', 'species': 'human', 'guides': ['ATCACGAAAGAATAACGCAT', 'ATAGTGGGAACTTAGGTACA', 'GCAGGCCATTATGGTTCATG', 'GCTGATCAATTCGAAGCCGT']}
sgRNA design for NR4A1:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'NR4A1', 'species': 'human', 'guides': ['GGCTAACAAGGACTGCCCTG', 'TACACCCGTGACCTCAACCA', 'ATGTGCGGACACCATAATGC', 'GCCCTCGCCTGGCTTAGACC']}
sgRNA design for BATF:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'BATF', 'species': 'human', 'guides': ['GGAACTGAAGTACTTCACGT', 'ACAGAACGCGGCTCTACGCA', 'ATGTGAGAAGAGTTCAGAGG', 'AAGCGCGGGGAGCTGACATG']}
sgRNA design for IRF4:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'IRF4', 'species': 'human', 'guides': ['CTGATCGACCAGATCGACAG', 'TCTGGTCGATCAGCCACTGG', 'TTTCGCATAGAGCCCGTCGG', 'GGTGACTCTATGCTTTGGAG']}
sgRNA design for PRDM1:
{'explanation': 'Output contains target gene name, species, and list of sgRNA sequences', 'gene_name': 'PRDM1', 'species': 'human', 'guides': ['GGACGCGTTCAAGTAAGCGT', 'GGGTAGTGAGCGTTGTACGA', 'GGGGTAGTGAGCGTTGTACG', 'GGATGGGGTAAACGACCCGA']}
--------------------------------------------------------------------------------
Summary of sgRNA design results:
- PDCD1: 4 guides
- CTLA4: 4 guides
- LAG3: 4 guides
- TIGIT: 4 guides
- HAVCR2: 4 guides
- BTLA: 4 guides
- CD244: 4 guides
- ADORA2A: 4 guides
- ENTPD1: 4 guides
- NT5E: 4 guides
- PTPN6: 4 guides
- PTPN11: 4 guides
- PTPN22: 4 guides
- INPP5D: 4 guides

[Output truncated - content was too long to display here (10083 characters total)]
```
</div>
</div>

#### Step 2

Here is my reasoning and plan to design a focused CRISPR screen and generate 32 high-impact target genes for modulating T cell exhaustion, measured as TCR signaling differences between acute (IL-2 only) and chronic (anti-CD3 + IL-2) stimulation.

Updated plan:
<div class="title-text plan">
<div class="title-text-header">
<span class="plan-title">Plan</span>
</div>
<div class="title-text-content">
<ul>
<li><strong>[x]</strong> Define the CRISPR screen goal, assay design, and workflow</li>
<li><strong>[x]</strong> Build and refine a candidate gene list linked to TCR inhibition/exhaustion; prioritize those expected to maximize perturbation</li>
<li><strong>[x]</strong> Check practical considerations (expression/function relevance in T cells) and finalize 32 genes</li>
<li><strong>[x]</strong> Generate sgRNAs (4 guides/gene) for the final 32-gene mini-library</li>
<li><strong>[x]</strong> Outline key experimental details: perturbation delivery, stimulation, readout, QC, and analysis</li>
</ul>
</div>
</div>

Step 2-3 (completed): Curated and finalized 32-gene list to maximize perturbation of chronic TCR signaling/exhaustion
- Prioritization logic: inhibitory receptors/checkpoints; adenosine-axis suppressors; phosphatases/adaptors/E3 ligases that dampen TCR/PI3K signaling; and exhaustion-driving transcriptional regulators. These are expressed or functionally relevant in human T cells and frequently implicated in attenuating TCR signaling and/or enforcing chronic-exhaustion programs.
- Final 32-gene list:
  1) PDCD1
  2) CTLA4
  3) LAG3
  4) TIGIT
  5) HAVCR2
  6) BTLA
  7) CD244
  8) ADORA2A
  9) ENTPD1
  10) NT5E
  11) PTPN6
  12) PTPN11
  13) PTPN22
  14) INPP5D
  15) PTEN
  16) CSK
  17) PAG1
  18) CBLB
  19) CBL
  20) UBASH3B
  21) UBASH3A
  22) RNF128
  23) ITCH
  24) DGKA
  25) DGKZ
  26) RCAN1
  27) PIK3IP1
  28) TOX
  29) NR4A1
  30) BATF
  31) IRF4
  32) PRDM1

Step 4 (completed): sgRNA design (4 guides per gene; human)
- Designed using the local sgRNA knockout resource; 4 guides returned per gene.

Gene to sgRNA mapping (4 per gene):
- PDCD1: CCCTTCGGTCACCACGAGCA; CCATAGTCCACAGAGAACAC; AGCCGGCCAGTTCCAAACCC; TCCGCTAGGAAAGACAATGG
- CTLA4: AAGAAGCCCTCTTACAACAG; TGCCCAGGTAGTATGGCGGT; TACCCACCGCCATACTACCT; TCCTTGCAGCAGTTAGTTCG
- LAG3: GTTCCGGAACCAATGCACAG; GGAACCAATGCACAGAGGCT; GGCTCACATCCTCTAGTCGA; GGGAGTTACCCAGAACAGTG
- TIGIT: AGTGTACGTCCCATCAGGGT; GCTGACCGTGAACGATACAG; CAGGCACAATAGAAACAACG; CGTTCACGGTCAGCGACTGG
- HAVCR2: AGAGAACGTATATGAAGTGG; TAGGCATCTACATCGGAGCA; TCTCTGCCGAGTCGGTGCAG; ATAGGCATCTACATCGGAGC
- BTLA: AGTAGAGGCAATCCCCCCAA; CATTGGACCGAACTCAAGAC; AGTAAACGATACAGGAGCCA; AGCTTGCACCAAGTCACATG
- CD244: AAATACAAAAACCTGGAACG; GTTGAGAAACCCCGCCTACA; ATGGCAATGTGTCCTATGCT; ATAGGACACATTGCCATCCC
- ADORA2A: GCGGAACTCGCGGATACGGT; GCGGCGGCCGACATCGCAGT; ATGCTAGGTTGGAACAACTG; GCTGCGAATGATCTTGCGGA
- ENTPD1: GCTACTTATGGAAGATACAA; GATAGAGGAGAAGCCAAGGA; TATATCCAGGATGAAAGCAT; GTTGATAGTAATCCAGCCAT
- NT5E: GCAGCACGTTGGGTTCGGCG; AGGTGACCAAGATATCAACG; TACCATGGCATCGTAGCGCA; GAGCATAGCGTGCACCGCTA
- PTPN6: CCAGGGTGGACGCTACACAG; GAGTACTACACTCAGCAGCA; TCACGCACAAGAAACGTCCA; CGGCCCAGTCGCAAGAACCA
- PTPN11: GGAGGAACATGACATCGCGG; GATTACTATGACCTGTATGG; TCTTCTAGTTGATCATACCA; TTATAAGAAGAATCCTATGG
- PTPN22: AGAATAGGGTCTATAGATGA; GGATGTACGTTGTTACCAAG; TACTAGCTATCCTGACACCA; GAAAAAGTGTGAGCGCTACT
- INPP5D: TGGGGATCTTAACTACCGTG; CGATCACGTAAATGTCATGG; GCTGTTGACGAACCCTAAGG; GTGGCTGTTGACGAACCCTA
- PTEN: TCATCTGGATTATAGACCAG; AAAAGGATATTGTGCAACTG; GACTGGGAATAGTTACTCCC; CAATTCAGGACCCACACGAC
- CSK: GCTCCCGTGTGATCTTGCCG; TCTTGCCGTGGAACCAACTG; TACAAGATGGATGCCCCCGA; CTGACCGACCCCTAGACCGC
- PAG1: ACCTGTCACAACTAGAGCAC; GTATCCACTGCGCTCTCGGG; GAAGCCGCGACAGCATAGTG; CTGGGAATCCAGCAGATCCG
- CBLB: AGGAACTGAGCCCATAATCG; GCACCTCTTGCCTTACGGCA; TGCACAGAACTATCGTACCA; TGAATTAGATCCAGGCGAGG
- CBL: GCAGGTCTAAGATATAAGGT; CTATCTTGTCAAGATATGAG; AGCAGGTCTAAGATATAAGG; AAATGGAAACAAATTCCCGG
- UBASH3B: CGAGCCCGGCCACTTACGCG; GAGCCCGGCCACTTACGCGC; TGTAGGTTGTATCAACACTC; GTGCAGTCTGAACGCAGCGA
- UBASH3A: CCAGTACAAACCCCAGAACG; GAGCCAGTGAGTCTGACACG; ATGCCACACGATGATAATGG; CGTGCTGGTGGTTCGCCACG
- RNF128: GGGAGTGAACCGTACGGTGT; GTACGGTTCACTCCCGTGTG; GCACACGGGAGTGAACCGTA; TGGTTGGCCCTCATCCAACG
- ITCH: TGGACCAAGTCCTTACGTAG; TCTACTGTGACCTCTACGTA; TCCCGAACATAGGCTATCTG; GGAACCTGCCGATTGCCAGT
- DGKA: AAGTGGTACATATGGATCGA; ACGACGGACAGCACATGTGG; GGATCTACCACAGTCTGACC; GTGGAATCGATGAGCAATAG
- DGKZ: GAATAAGATGTTCTACGCCG; AGTTCCACGAGTCTCGAGGT; GGCCAAGCACATCCGAGTGG; CTAGGAGTCAGCGACATATG
- RCAN1: GACTGACACCACTCCCAGCG; TGACACCACTCCCAGCGTGG; GAAGGGCCGCAGCGTCACCC; ACATACATGGACCACCACGC
- PIK3IP1: AGGACACTTACCCGACACGG; TCGCCACTGACGTAGCACCA; GAGGACACTTACCCGACACG; TCTTGGGCTACTCCTACAAG
- TOX: ATCACGAAAGAATAACGCAT; ATAGTGGGAACTTAGGTACA; GCAGGCCATTATGGTTCATG; GCTGATCAATTCGAAGCCGT
- NR4A1: GGCTAACAAGGACTGCCCTG; TACACCCGTGACCTCAACCA; ATGTGCGGACACCATAATGC; GCCCTCGCCTGGCTTAGACC
- BATF: GGAACTGAAGTACTTCACGT; ACAGAACGCGGCTCTACGCA; ATGTGAGAAGAGTTCAGAGG; AAGCGCGGGGAGCTGACATG
- IRF4: CTGATCGACCAGATCGACAG; TCTGGTCGATCAGCCACTGG; TTTCGCATAGAGCCCGTCGG; GGTGACTCTATGCTTTGGAG
- PRDM1: GGACGCGTTCAAGTAAGCGT; GGGTAGTGAGCGTTGTACGA; GGGGTAGTGAGCGTTGTACG; GGATGGGGTAAACGACCCGA

Step 5 (completed): Focused pooled CRISPR screen design for differential TCR signaling (chronic vs acute)
- Objective and primary endpoint
  - Goal: Identify knockouts that most strongly alter TCR signaling preferentially under chronic stimulation (anti-CD3 + IL-2) compared to acute (IL-2 only, rested).
  - Readout: Reporter-based signaling (e.g., NFAT-GFP or Nur77-GFP) with FACS binning, or phospho-flow (pZAP70/pERK) or early activation marker (CD69) as alternatives.
  - Differential score: Effect under chronic minus effect under acute per gene.

- Library composition
  - 32 genes x 4 sgRNAs = 128 targeting guides.
  - Controls (recommended):
    - Non-targeting: 40–50 sgRNAs.
    - Safe-targeting (AAVS1/CCR5 intronic, non-functional regions): 8–10 sgRNAs.
    - Positive controls:
      - Loss-of-signal under both arms: CD3E, LCK, ZAP70, LAT, LCP2 (2–3 sgRNAs each).
      - Gain-of-signal: CBLB, PTPN6, DGKA (2–3 sgRNAs each).
  - Total library size: ~200–230 guides.

- Cell models
  - Development and optimization: Jurkat NFAT/Nur77 reporter line stably expressing Cas9 or lentiCRISPRv2.
  - Primary readout and validation: Human primary CD8+ T cells from ≥2 donors; activation day 0 with CD3/CD28, expand in IL-2 (50–100 IU/mL), transduce on day 2–3 (MOI ~0.3).

- Perturbation and delivery
  - For primary T cells: SLICE-style workflow (lentiviral sgRNA delivery + Cas9 RNP electroporation). Maintain ≥500–1000x cells/guide throughout.
  - For Jurkat: Lentiviral lentiCRISPRv2 at MOI ~0.3, puromycin select 3–5 days.

- Stimulation arms and timing
  - Acute arm: IL-2 only, no TCR stimulation for matched duration; rest 5–7 days post-editing.
  - Chronic arm: Plate-bound anti-CD3 (e.g., OKT3, 1–5 μg/mL) + IL-2 for 5–7 days; re-stimulate every 48 h to enforce chronic signaling.
  - Optional: Add anti-CD28 to modulate co-stimulation (keep consistent across arms if used).
  - Collect at a standardized timepoint (e.g., day 6–7 post-stimulation) when control cells show reduced reporter in chronic vs acute.

- Readout and sorting
  - Reporter: NFAT/Nur77-GFP. Confirm dynamic range in pilot.
  - Binning: In each arm, FACS-sort top 20% (high signaling) and bottom 20% (low signaling) reporter populations; collect ≥2–3 biological replicates.
  - Genomic DNA extraction and NGS of sgRNA cassettes from each bin.

- QC and performance metrics
  - Infection MOI (~0.3), library representation (>95% guides present), coverage (>500–1000x/guide), viability.
  - Editing efficiency: TIDE/ICE on sentinel loci or amplicon-seq for a subset.
  - Replicate concordance (Pearson/Spearman >0.8 at sgRNA counts), minimal batch effects.
  - Reporter window: ≥5–10x shift between positive and negative control bins.

- Analysis
  - Use MAGeCK count + MAGeCK-MLE on binned data with a design matrix including bin (hi/lo), condition (acute/chronic), and replicate.
  - Compute gene-level differential effect: beta_chronic_high - beta_chronic_low minus (beta_acute_high - beta_acute_low), or equivalently a gene-by-condition interaction term.
  - Call hits by FDR (e.g., <0.1) and effect size thresholds. Inspect directionality:
    - Positive differential: KO sustains signaling under chronic (anti-exhaustion candidates: e.g., PDCD1, CBLB, PTPN6, DGKA, TOX, NR4A1).
    - Negative differential: KO preferentially impairs chronic signaling vs acute (context-dependent regulators).
  - Cross-check sgRNA concordance within each gene.

- Validation (arrayed, primary CD8+ T cells)
  - Edit 3–5 top genes individually (4 sgRNAs/gene) and pool 2–3 guides per edit.
  - Assays: Reporter; phospho-flow (pZAP70, pSLP-76, pERK); cytokines (IL-2, IFN-γ, TNF); exhaustion markers (PD-1, TIM-3, LAG-3); serial restimulation survival/proliferation.
  - Rescue/orthogonal: Overexpression or pharmacologic inhibitors where relevant (e.g., DGK inhibitors).

- Risk and practicality notes
  - Some TF KOs (IRF4, BATF) can reduce acute activation; they may still yield strong differential effects. Interpret with care.
  - Check gene expression in donor T cells (optional RNA-seq/protein atlas) to de-prioritize low-expression targets for primary screening if needed.
  - Safety: Many are immune checkpoints; in vivo translation may carry autoimmunity risks.

Final deliverables
- 32 prioritized targets and 4 sgRNAs/gene (128 guides) ready for mini-library assembly.
- Detailed screening plan to quantify differential TCR signaling under chronic vs acute conditions, with controls, QC, and analysis strategy.

<div class="title-text summary">
<div class="title-text-header">
<strong>Summary and Solution</strong>
</div>
<div class="title-text-content">
Checklist:
<div class="title-text plan">
<div class="title-text-header">
<span class="plan-title">Plan</span>
</div>
<div class="title-text-content">
<ul>
<li><strong>[x]</strong> Define the CRISPR screen goal, assay design, and workflow</li>
<li><strong>[x]</strong> Build and refine a candidate gene list linked to TCR inhibition/exhaustion; prioritize those expected to maximize perturbation</li>
<li><strong>[x]</strong> Check practical considerations (expression/function relevance in T cells) and finalize 32 genes</li>
<li><strong>[x]</strong> Generate sgRNAs (4 guides/gene) for the final 32-gene mini-library</li>
<li><strong>[x]</strong> Outline key experimental details: perturbation delivery, stimulation, readout, QC, and analysis</li>
</ul>
</div>
</div>

Final 32-gene set (to maximize perturbation of chronic TCR signaling/exhaustion):
1) PDCD1
2) CTLA4
3) LAG3
4) TIGIT
5) HAVCR2
6) BTLA
7) CD244
8) ADORA2A
9) ENTPD1
10) NT5E
11) PTPN6
12) PTPN11
13) PTPN22
14) INPP5D
15) PTEN
16) CSK
17) PAG1
18) CBLB
19) CBL
20) UBASH3B
21) UBASH3A
22) RNF128
23) ITCH
24) DGKA
25) DGKZ
26) RCAN1
27) PIK3IP1
28) TOX
29) NR4A1
30) BATF
31) IRF4
32) PRDM1

sgRNAs (4 per gene; human):
- PDCD1: CCCTTCGGTCACCACGAGCA; CCATAGTCCACAGAGAACAC; AGCCGGCCAGTTCCAAACCC; TCCGCTAGGAAAGACAATGG
- CTLA4: AAGAAGCCCTCTTACAACAG; TGCCCAGGTAGTATGGCGGT; TACCCACCGCCATACTACCT; TCCTTGCAGCAGTTAGTTCG
- LAG3: GTTCCGGAACCAATGCACAG; GGAACCAATGCACAGAGGCT; GGCTCACATCCTCTAGTCGA; GGGAGTTACCCAGAACAGTG
- TIGIT: AGTGTACGTCCCATCAGGGT; GCTGACCGTGAACGATACAG; CAGGCACAATAGAAACAACG; CGTTCACGGTCAGCGACTGG
- HAVCR2: AGAGAACGTATATGAAGTGG; TAGGCATCTACATCGGAGCA; TCTCTGCCGAGTCGGTGCAG; ATAGGCATCTACATCGGAGC
- BTLA: AGTAGAGGCAATCCCCCCAA; CATTGGACCGAACTCAAGAC; AGTAAACGATACAGGAGCCA; AGCTTGCACCAAGTCACATG
- CD244: AAATACAAAAACCTGGAACG; GTTGAGAAACCCCGCCTACA; ATGGCAATGTGTCCTATGCT; ATAGGACACATTGCCATCCC
- ADORA2A: GCGGAACTCGCGGATACGGT; GCGGCGGCCGACATCGCAGT; ATGCTAGGTTGGAACAACTG; GCTGCGAATGATCTTGCGGA
- ENTPD1: GCTACTTATGGAAGATACAA; GATAGAGGAGAAGCCAAGGA; TATATCCAGGATGAAAGCAT; GTTGATAGTAATCCAGCCAT
- NT5E: GCAGCACGTTGGGTTCGGCG; AGGTGACCAAGATATCAACG; TACCATGGCATCGTAGCGCA; GAGCATAGCGTGCACCGCTA
- PTPN6: CCAGGGTGGACGCTACACAG; GAGTACTACACTCAGCAGCA; TCACGCACAAGAAACGTCCA; CGGCCCAGTCGCAAGAACCA
- PTPN11: GGAGGAACATGACATCGCGG; GATTACTATGACCTGTATGG; TCTTCTAGTTGATCATACCA; TTATAAGAAGAATCCTATGG
- PTPN22: AGAATAGGGTCTATAGATGA; GGATGTACGTTGTTACCAAG; TACTAGCTATCCTGACACCA; GAAAAAGTGTGAGCGCTACT
- INPP5D: TGGGGATCTTAACTACCGTG; CGATCACGTAAATGTCATGG; GCTGTTGACGAACCCTAAGG; GTGGCTGTTGACGAACCCTA
- PTEN: TCATCTGGATTATAGACCAG; AAAAGGATATTGTGCAACTG; GACTGGGAATAGTTACTCCC; CAATTCAGGACCCACACGAC
- CSK: GCTCCCGTGTGATCTTGCCG; TCTTGCCGTGGAACCAACTG; TACAAGATGGATGCCCCCGA; CTGACCGACCCCTAGACCGC
- PAG1: ACCTGTCACAACTAGAGCAC; GTATCCACTGCGCTCTCGGG; GAAGCCGCGACAGCATAGTG; CTGGGAATCCAGCAGATCCG
- CBLB: AGGAACTGAGCCCATAATCG; GCACCTCTTGCCTTACGGCA; TGCACAGAACTATCGTACCA; TGAATTAGATCCAGGCGAGG
- CBL: GCAGGTCTAAGATATAAGGT; CTATCTTGTCAAGATATGAG; AGCAGGTCTAAGATATAAGG; AAATGGAAACAAATTCCCGG
- UBASH3B: CGAGCCCGGCCACTTACGCG; GAGCCCGGCCACTTACGCGC; TGTAGGTTGTATCAACACTC; GTGCAGTCTGAACGCAGCGA
- UBASH3A: CCAGTACAAACCCCAGAACG; GAGCCAGTGAGTCTGACACG; ATGCCACACGATGATAATGG; CGTGCTGGTGGTTCGCCACG
- RNF128: GGGAGTGAACCGTACGGTGT; GTACGGTTCACTCCCGTGTG; GCACACGGGAGTGAACCGTA; TGGTTGGCCCTCATCCAACG
- ITCH: TGGACCAAGTCCTTACGTAG; TCTACTGTGACCTCTACGTA; TCCCGAACATAGGCTATCTG; GGAACCTGCCGATTGCCAGT
- DGKA: AAGTGGTACATATGGATCGA; ACGACGGACAGCACATGTGG; GGATCTACCACAGTCTGACC; GTGGAATCGATGAGCAATAG
- DGKZ: GAATAAGATGTTCTACGCCG; AGTTCCACGAGTCTCGAGGT; GGCCAAGCACATCCGAGTGG; CTAGGAGTCAGCGACATATG
- RCAN1: GACTGACACCACTCCCAGCG; TGACACCACTCCCAGCGTGG; GAAGGGCCGCAGCGTCACCC; ACATACATGGACCACCACGC
- PIK3IP1: AGGACACTTACCCGACACGG; TCGCCACTGACGTAGCACCA; GAGGACACTTACCCGACACG; TCTTGGGCTACTCCTACAAG
- TOX: ATCACGAAAGAATAACGCAT; ATAGTGGGAACTTAGGTACA; GCAGGCCATTATGGTTCATG; GCTGATCAATTCGAAGCCGT
- NR4A1: GGCTAACAAGGACTGCCCTG; TACACCCGTGACCTCAACCA; ATGTGCGGACACCATAATGC; GCCCTCGCCTGGCTTAGACC
- BATF: GGAACTGAAGTACTTCACGT; ACAGAACGCGGCTCTACGCA; ATGTGAGAAGAGTTCAGAGG; AAGCGCGGGGAGCTGACATG
- IRF4: CTGATCGACCAGATCGACAG; TCTGGTCGATCAGCCACTGG; TTTCGCATAGAGCCCGTCGG; GGTGACTCTATGCTTTGGAG
- PRDM1: GGACGCGTTCAAGTAAGCGT; GGGTAGTGAGCGTTGTACGA; GGGGTAGTGAGCGTTGTACG; GGATGGGGTAAACGACCCGA

Screen execution summary:
- Use pooled library with 32x4 guides and controls; MOI ~0.3; ≥500–1000x coverage/guide.
- Two matched arms: acute (IL-2 only) vs chronic (plate-bound anti-CD3 + IL-2 with restimulation).
- Reporter-based FACS binning (top 20% vs bottom 20%) in each arm; NGS of sgRNAs.
- Analyze with MAGeCK-MLE using a condition-by-bin interaction to derive a differential chronic vs acute effect per gene; call hits by FDR and effect size; validate top genes in arrayed primary CD8+ T-cell assays.

If you’d like, I can also format these guides into a cloning-ready oligo pool with constant arms and barcodes, plus plate maps for arrayed validation.
</div>
</div>

