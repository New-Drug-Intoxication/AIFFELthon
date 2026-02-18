description = [
{   'description': 'Perform ATAC-seq peak calling and differential '
                   'accessibility analysis using MACS2.',
    'name': 'analyze_atac_seq_differential_accessibility',
    'optional_parameters': [   {   'default': './atac_results',
                                   'description': 'Directory to save output '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'},
                               {   'default': 'hs',
                                   'description': 'Genome size parameter for '
                                                  'MACS2',
                                   'name': 'genome_size',
                                   'type': 'str'},
                               {   'default': 0.05,
                                   'description': 'q-value cutoff for peak '
                                                  'detection',
                                   'name': 'q_value',
                                   'type': 'float'},
                               {   'default': 'atac',
                                   'description': 'Prefix for output file '
                                                  'names',
                                   'name': 'name_prefix',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the treatment '
                                                  'condition BAM file with '
                                                  'aligned ATAC-seq reads',
                                   'name': 'treatment_bam',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Path to the control '
                                                  'condition BAM file with '
                                                  'aligned ATAC-seq reads',
                                   'name': 'control_bam',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'immunology'}}},
{   'description': 'Analyzes bacterial growth curve data to determine growth '
                   'parameters such as doubling time, growth rate, and lag '
                   'phase.',
    'name': 'analyze_bacterial_growth_curve',
    'optional_parameters': [   {   'default': '.',
                                   'description': 'Directory where output '
                                                  'files will be saved',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Time points of measurements '
                                                  'in hours',
                                   'name': 'time_points',
                                   'type': 'List or numpy.ndarray'},
                               {   'default': None,
                                   'description': 'Optical density '
                                                  'measurements corresponding '
                                                  'to each time point',
                                   'name': 'od_values',
                                   'type': 'List or numpy.ndarray'},
                               {   'default': None,
                                   'description': 'Name of the bacterial '
                                                  'strain being analyzed',
                                   'name': 'strain_name',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'A research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'immunology'}}},
{   'description': 'Simulates the isolation and purification of immune cells '
                   'from tissue samples.',
    'name': 'isolate_purify_immune_cells',
    'optional_parameters': [   {   'default': 'collagenase',
                                   'description': 'The enzyme used for tissue '
                                                  'digestion',
                                   'name': 'enzyme_type',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Specific antibody for '
                                                  'magnetic-assisted cell '
                                                  'sorting',
                                   'name': 'macs_antibody',
                                   'type': 'str'},
                               {   'default': 45,
                                   'description': 'Digestion time in minutes',
                                   'name': 'digestion_time_min',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'The type of tissue sample '
                                                  "(e.g., 'adipose', 'kidney', "
                                                  "'liver', 'lung', 'spleen')",
                                   'name': 'tissue_type',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'The immune cell population '
                                                  'to isolate (e.g., '
                                                  "'macrophages', "
                                                  "'leukocytes', 'T cells')",
                                   'name': 'target_cell_type',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'A research log '
                                                              'describing the '
                                                              'cell isolation '
                                                              'and '
                                                              'purification '
                                                              'process',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'simulation',
                                           'domain': 'immunology'}}},
{   'description': 'Estimate cell cycle phase durations using dual-nucleoside '
                   'pulse labeling data and mathematical modeling.',
    'name': 'estimate_cell_cycle_phase_durations',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'Dictionary containing '
                                                  'experimental data from flow '
                                                  'cytometry with EdU and BrdU '
                                                  'labeling, including time '
                                                  'points and percentages of '
                                                  'labeled cells',
                                   'name': 'flow_cytometry_data',
                                   'type': 'dict'},
                               {   'default': None,
                                   'description': 'Initial estimates for cell '
                                                  'cycle phase durations and '
                                                  'death rates',
                                   'name': 'initial_estimates',
                                   'type': 'dict'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'cell cycle '
                                                              'phase duration '
                                                              'estimation '
                                                              'process and '
                                                              'results.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'immunology'}}},
{   'description': 'Track immune cells under flow conditions and classify '
                   'their behaviors.',
    'name': 'track_immune_cells_under_flow',
    'optional_parameters': [   {   'default': './output',
                                   'description': 'Directory to save output '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'},
                               {   'default': 1.0,
                                   'description': 'Pixel size in micrometers',
                                   'name': 'pixel_size_um',
                                   'type': 'float'},
                               {   'default': 1.0,
                                   'description': 'Time interval between '
                                                  'frames in seconds',
                                   'name': 'time_interval_sec',
                                   'type': 'float'},
                               {   'default': 'right',
                                   'description': "Direction of flow ('right', "
                                                  "'left', 'up', 'down')",
                                   'name': 'flow_direction',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to image sequence '
                                                  'directory or video file',
                                   'name': 'image_sequence_path',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Log of the '
                                                              'analysis '
                                                              'process.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'immunology'}}},
{   'description': 'Analyze CFSE-labeled cell samples to quantify cell '
                   'division and proliferation.',
    'name': 'analyze_cfse_cell_proliferation',
    'optional_parameters': [   {   'default': 'FL1-A',
                                   'description': 'Name of the channel '
                                                  'containing CFSE '
                                                  'fluorescence data',
                                   'name': 'cfse_channel',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Tuple of (min_fsc, max_fsc, '
                                                  'min_ssc, max_ssc) for '
                                                  'lymphocyte gating',
                                   'name': 'lymphocyte_gate',
                                   'type': 'tuple or None'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the FCS file '
                                                  'containing flow cytometry '
                                                  'data from CFSE-labeled '
                                                  'cells',
                                   'name': 'fcs_file_path',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'CFSE '
                                                                                   'channel '
                                                                                   'not '
                                                                                   'found',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'specified '
                                                                                    'CFSE '
                                                                                    'channel '
                                                                                    'exists '
                                                                                    'in '
                                                                                    'the '
                                                                                    'FCS '
                                                                                    'file.',
                                                                      'source': 'return '
                                                                                'f"Error: '
                                                                                'CFSE '
                                                                                'channel '
                                                                                "'{cfse_channel}' "
                                                                                'not '
                                                                                'found. '
                                                                                'Available '
                                                                                'channels: '
                                                                                '{available_channels}"'},
                                                                  {   'condition': 'Could '
                                                                                   'not '
                                                                                   'import '
                                                                                   'FlowCytometryTools',
                                                                      'resolution': 'Install '
                                                                                    'FlowCytometryTools '
                                                                                    'or '
                                                                                    'ensure '
                                                                                    'it '
                                                                                    'is '
                                                                                    'correctly '
                                                                                    'installed '
                                                                                    'and '
                                                                                    'accessible '
                                                                                    'in '
                                                                                    'the '
                                                                                    'environment.',
                                                                      'source': 'Warning: '
                                                                                'Could '
                                                                                'not '
                                                                                'import '
                                                                                'FlowCytometryTools: '
                                                                                '{str(e)}'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results, '
                                                              'including cell '
                                                              'division index '
                                                              'and percentage '
                                                              'of '
                                                              'proliferating '
                                                              'cells',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'immunology'}}},
{   'description': 'Analyze cytokine production (IFN-γ, IL-17) in CD4+ T cells '
                   'after antigen stimulation.',
    'name': 'analyze_cytokine_production_in_cd4_tcells',
    'optional_parameters': [   {   'default': './results',
                                   'description': 'Directory to save the '
                                                  'results file',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Dictionary mapping '
                                                  'stimulation conditions to '
                                                  'FCS file paths. Expected '
                                                  "keys: 'unstimulated', "
                                                  "'Mtb300', 'CMV', 'SEB'",
                                   'name': 'fcs_files_dict',
                                   'type': 'dict'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'CD4 '
                                                                                   'channel '
                                                                                   'not '
                                                                                   'found',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'FCS '
                                                                                    'file '
                                                                                    'contains '
                                                                                    'a '
                                                                                    'channel '
                                                                                    'named '
                                                                                    'CD4.',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                '"ERROR: '
                                                                                'CD4 '
                                                                                'channel '
                                                                                'not '
                                                                                'found '
                                                                                'in '
                                                                                'data\\n"'},
                                                                  {   'condition': 'Cytokine '
                                                                                   'channels '
                                                                                   'not '
                                                                                   'found',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'FCS '
                                                                                    'file '
                                                                                    'contains '
                                                                                    'channels '
                                                                                    'for '
                                                                                    'IFN-γ '
                                                                                    'and/or '
                                                                                    'IL-17.',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                '"ERROR: '
                                                                                'Cytokine '
                                                                                'channels '
                                                                                '(IFN-γ, '
                                                                                'IL-17) '
                                                                                'not '
                                                                                'found '
                                                                                'in '
                                                                                'data\\n"'},
                                                                  {   'condition': 'Error '
                                                                                   'during '
                                                                                   'analysis',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'specific '
                                                                                    'error '
                                                                                    'message '
                                                                                    '(e) '
                                                                                    'for '
                                                                                    'the '
                                                                                    'cause '
                                                                                    'of '
                                                                                    'the '
                                                                                    'problem. '
                                                                                    'This '
                                                                                    'could '
                                                                                    'be '
                                                                                    'due '
                                                                                    'to '
                                                                                    'issues '
                                                                                    'with '
                                                                                    'gating, '
                                                                                    'data '
                                                                                    'transformation, '
                                                                                    'or '
                                                                                    'file '
                                                                                    'loading.',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                'f"ERROR '
                                                                                'during '
                                                                                'analysis: '
                                                                                '{str(e)}\\n"'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'immunology'}}},
{   'description': 'Analyze ELISA data to quantify EBV antibody titers in '
                   'plasma/serum samples.',
    'name': 'analyze_ebv_antibody_titers',
    'optional_parameters': [   {   'default': './',
                                   'description': 'Directory to save output '
                                                  'files.',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Dictionary containing '
                                                  'optical density (OD) '
                                                  'readings for each sample. '
                                                  'Format: {sample_id: '
                                                  "{'VCA_IgG': float, "
                                                  "'VCA_IgM': float, 'EA_IgG': "
                                                  "float, 'EA_IgM': float, "
                                                  "'EBNA1_IgG': float, "
                                                  "'EBNA1_IgM': float}}",
                                   'name': 'raw_od_data',
                                   'type': 'dict'},
                               {   'default': None,
                                   'description': 'Dictionary containing '
                                                  'standard curve data for '
                                                  'each antibody type. Format: '
                                                  '{antibody_type: '
                                                  '[(concentration, OD), ...]}',
                                   'name': 'standard_curve_data',
                                   'type': 'dict'},
                               {   'default': None,
                                   'description': 'Dictionary containing '
                                                  'metadata for each sample. '
                                                  'Format: {sample_id: '
                                                  "{'group': str, "
                                                  "'collection_date': str}}",
                                   'name': 'sample_metadata',
                                   'type': 'dict'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis '
                                                              'process and '
                                                              'results.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'immunology'}}},
{   'description': 'Analyzes histological images of CNS lesions to quantify '
                   'immune cell infiltration, demyelination, and tissue '
                   'damage.',
    'name': 'analyze_cns_lesion_histology',
    'optional_parameters': [   {   'default': './output',
                                   'description': 'Directory to save output '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'},
                               {   'default': 'H&E',
                                   'description': 'Type of histological stain '
                                                  'used (options: "H&E", '
                                                  '"LFB", "IHC")',
                                   'name': 'stain_type',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the microscopy '
                                                  'image file of brain or '
                                                  'spinal cord tissue section',
                                   'name': 'image_path',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'scikit-image '
                                                                                   'not '
                                                                                   'available',
                                                                      'resolution': 'Install '
                                                                                    'scikit-image',
                                                                      'source': 'log.append("WARNING: '
                                                                                'scikit-image '
                                                                                'not '
                                                                                'available. '
                                                                                'Using '
                                                                                'simulated '
                                                                                'analysis.")'},
                                                                  {   'condition': 'Error '
                                                                                   'during '
                                                                                   'image '
                                                                                   'analysis',
                                                                      'resolution': 'Check '
                                                                                    'image '
                                                                                    'file '
                                                                                    'and '
                                                                                    'dependencies',
                                                                      'source': 'log.append(f"Error '
                                                                                'during '
                                                                                'image '
                                                                                'analysis: '
                                                                                '{str(e)}")'},
                                                                  {   'condition': 'Could '
                                                                                   'not '
                                                                                   'save '
                                                                                   'segmentation '
                                                                                   'result',
                                                                      'resolution': 'Check '
                                                                                    'file '
                                                                                    'permissions '
                                                                                    'and '
                                                                                    'output '
                                                                                    'directory',
                                                                      'source': 'log.append(f"Warning: '
                                                                                'Could '
                                                                                'not '
                                                                                'save '
                                                                                'segmentation '
                                                                                'result: '
                                                                                '{str(e)}")'},
                                                                  {   'condition': 'Could '
                                                                                   'not '
                                                                                   'save '
                                                                                   'metrics '
                                                                                   'file',
                                                                      'resolution': 'Check '
                                                                                    'file '
                                                                                    'permissions '
                                                                                    'and '
                                                                                    'output '
                                                                                    'directory',
                                                                      'source': 'log.append(f"Warning: '
                                                                                'Could '
                                                                                'not '
                                                                                'save '
                                                                                'metrics '
                                                                                'file: '
                                                                                '{str(e)}")'},
                                                                  {   'condition': 'Could '
                                                                                   'not '
                                                                                   'save '
                                                                                   'simulated '
                                                                                   'metrics '
                                                                                   'file',
                                                                      'resolution': 'Check '
                                                                                    'file '
                                                                                    'permissions '
                                                                                    'and '
                                                                                    'output '
                                                                                    'directory',
                                                                      'source': 'log.append(f"Warning: '
                                                                                'Could '
                                                                                'not '
                                                                                'save '
                                                                                'simulated '
                                                                                'metrics '
                                                                                'file: '
                                                                                '{str(e)}")'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps, '
                                                              'findings, and '
                                                              'saved file '
                                                              'paths',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'immunology'}}},
{   'description': 'Analyzes immunohistochemistry images to quantify protein '
                   'expression and spatial distribution.',
    'name': 'analyze_immunohistochemistry_image',
    'optional_parameters': [   {   'default': 'Unknown',
                                   'description': 'Name of the protein being '
                                                  'analyzed',
                                   'name': 'protein_name',
                                   'type': 'str'},
                               {   'default': './ihc_results/',
                                   'description': 'Directory to save output '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the microscopy '
                                                  'image of tissue section '
                                                  'stained with antibodies',
                                   'name': 'image_path',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Error '
                                                                                   'loading '
                                                                                   'image',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'image '
                                                                                    'path '
                                                                                    'is '
                                                                                    'correct '
                                                                                    'and '
                                                                                    'the '
                                                                                    'file '
                                                                                    'is '
                                                                                    'accessible.',
                                                                      'source': 'return '
                                                                                'f"Error '
                                                                                'loading '
                                                                                'image: '
                                                                                '{str(e)}"'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps, '
                                                              'results, and '
                                                              'saved file '
                                                              'locations',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'immunology'}}}
]
