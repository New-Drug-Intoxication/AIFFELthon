description = [
{   'description': 'Generate a 3D model of facial anatomy from MRI scans of '
                   'the head and neck.',
    'name': 'reconstruct_3d_face_from_mri',
    'optional_parameters': [   {   'default': './output',
                                   'description': 'Directory where output '
                                                  'files will be saved',
                                   'name': 'output_dir',
                                   'type': 'str'},
                               {   'default': 'subject',
                                   'description': 'Identifier for the subject, '
                                                  'used in output filenames',
                                   'name': 'subject_id',
                                   'type': 'str'},
                               {   'default': 300,
                                   'description': 'Threshold value for initial '
                                                  'segmentation of facial '
                                                  'tissues',
                                   'name': 'threshold_value',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the MRI scan file '
                                                  '(NIfTI format: .nii or '
                                                  '.nii.gz)',
                                   'name': 'mri_file_path',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Failed '
                                                                                   'to '
                                                                                   'load '
                                                                                   'MRI '
                                                                                   'data',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'MRI '
                                                                                    'file '
                                                                                    'path '
                                                                                    'is '
                                                                                    'correct '
                                                                                    'and '
                                                                                    'the '
                                                                                    'file '
                                                                                    'is '
                                                                                    'a '
                                                                                    'valid '
                                                                                    'NIfTI '
                                                                                    'format.',
                                                                      'source': 'return '
                                                                                '"\\n".join(log)'},
                                                                  {   'condition': 'Error '
                                                                                   'generating '
                                                                                   'mesh',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'segmentation '
                                                                                    'and '
                                                                                    'threshold '
                                                                                    'values.  '
                                                                                    'Ensure '
                                                                                    'the '
                                                                                    'input '
                                                                                    'data '
                                                                                    'is '
                                                                                    'valid '
                                                                                    'for '
                                                                                    'the '
                                                                                    'marching '
                                                                                    'cubes '
                                                                                    'algorithm.',
                                                                      'source': 'log.append(f"  '
                                                                                'Error '
                                                                                'generating '
                                                                                'mesh: '
                                                                                '{str(e)}")'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'detailing the '
                                                              'reconstruction '
                                                              'process and '
                                                              'output file '
                                                              'locations',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'simulation',
                                           'domain': 'physiology'}}},
{   'description': 'Extracts P1 amplitude and latency from Auditory Brainstem '
                   'Response (ABR) waveform data.',
    'name': 'analyze_abr_waveform_p1_metrics',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'Time points of the ABR '
                                                  'recording in milliseconds',
                                   'name': 'time_ms',
                                   'type': 'array-like'},
                               {   'default': None,
                                   'description': 'Amplitude values of the ABR '
                                                  'recording in microvolts',
                                   'name': 'amplitude_uv',
                                   'type': 'array-like'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'No '
                                                                                   'positive '
                                                                                   'peaks '
                                                                                   'detected '
                                                                                   'in '
                                                                                   'the '
                                                                                   'ABR '
                                                                                   'waveform.',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'input '
                                                                                    'waveform '
                                                                                    'data '
                                                                                    'is '
                                                                                    'valid '
                                                                                    'and '
                                                                                    'contains '
                                                                                    'positive '
                                                                                    'peaks.',
                                                                      'source': 'return '
                                                                                '"Research '
                                                                                'Log: '
                                                                                'No '
                                                                                'positive '
                                                                                'peaks '
                                                                                'detected '
                                                                                'in '
                                                                                'the '
                                                                                'ABR '
                                                                                'waveform."'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results, '
                                                              'including P1 '
                                                              'amplitude and '
                                                              'latency',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'physiology'}}},
{   'description': 'Analyze ciliary beat frequency from high-speed video '
                   'microscopy data using FFT analysis.',
    'name': 'analyze_ciliary_beat_frequency',
    'optional_parameters': [   {   'default': 5,
                                   'description': 'Number of regions of '
                                                  'interest to analyze',
                                   'name': 'roi_count',
                                   'type': 'int'},
                               {   'default': 0,
                                   'description': 'Minimum frequency to '
                                                  'consider in Hz',
                                   'name': 'min_freq',
                                   'type': 'float'},
                               {   'default': 30,
                                   'description': 'Maximum frequency to '
                                                  'consider in Hz',
                                   'name': 'max_freq',
                                   'type': 'float'},
                               {   'default': './',
                                   'description': 'Directory to save output '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the high-speed '
                                                  'video microscopy file of '
                                                  'ciliary beating',
                                   'name': 'video_path',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Could '
                                                                                   'not '
                                                                                   'open '
                                                                                   'video '
                                                                                   'file',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'video '
                                                                                    'file '
                                                                                    'path '
                                                                                    'is '
                                                                                    'correct '
                                                                                    'and '
                                                                                    'the '
                                                                                    'file '
                                                                                    'exists.',
                                                                      'source': 'return '
                                                                                'f"Error: '
                                                                                'Could '
                                                                                'not '
                                                                                'open '
                                                                                'video '
                                                                                'file '
                                                                                '{video_path}"'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'physiology'}}},
{   'description': 'Analyze colocalization between two fluorescently labeled '
                   'proteins in microscopy images.',
    'name': 'analyze_protein_colocalization',
    'optional_parameters': [   {   'default': './output',
                                   'description': 'Directory to save output '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'},
                               {   'default': 'otsu',
                                   'description': 'Method for thresholding '
                                                  "images ('otsu', 'li', or "
                                                  "'yen')",
                                   'name': 'threshold_method',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the first channel '
                                                  'image file (fluorescent '
                                                  'protein 1)',
                                   'name': 'channel1_path',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Path to the second channel '
                                                  'image file (fluorescent '
                                                  'protein 2)',
                                   'name': 'channel2_path',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Images '
                                                                                   'must '
                                                                                   'have '
                                                                                   'the '
                                                                                   'same '
                                                                                   'dimensions',
                                                                      'resolution': 'Ensure '
                                                                                    'images '
                                                                                    'have '
                                                                                    'the '
                                                                                    'same '
                                                                                    'dimensions '
                                                                                    'before '
                                                                                    'calling '
                                                                                    'the '
                                                                                    'function.',
                                                                      'source': 'return '
                                                                                '"Error: '
                                                                                'Images '
                                                                                'must '
                                                                                'have '
                                                                                'the '
                                                                                'same '
                                                                                'dimensions"'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'colocalization '
                                                              'analysis '
                                                              'results and '
                                                              'saved files',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'physiology'}}},
{   'description': 'Performs cosinor analysis on physiological time series '
                   'data to characterize circadian rhythms.',
    'name': 'perform_cosinor_analysis',
    'optional_parameters': [   {   'default': 24.0,
                                   'description': 'Period of the rhythm in '
                                                  'hours, default is 24 hours '
                                                  'for circadian rhythms',
                                   'name': 'period',
                                   'type': 'float'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Time points of the '
                                                  'measurements in hours',
                                   'name': 'time_data',
                                   'type': 'array-like'},
                               {   'default': None,
                                   'description': 'Physiological measurements '
                                                  'corresponding to each time '
                                                  'point',
                                   'name': 'physiological_data',
                                   'type': 'array-like'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'An '
                                                                                   'exception '
                                                                                   'occurs '
                                                                                   'during '
                                                                                   'the '
                                                                                   'curve '
                                                                                   'fitting '
                                                                                   'process.',
                                                                      'resolution': 'Check '
                                                                                    'input '
                                                                                    'data '
                                                                                    'for '
                                                                                    'validity '
                                                                                    '(e.g., '
                                                                                    'sufficient '
                                                                                    'data '
                                                                                    'points, '
                                                                                    'non-NaN '
                                                                                    'values). '
                                                                                    'Review '
                                                                                    'the '
                                                                                    'error '
                                                                                    'message '
                                                                                    'for '
                                                                                    'specific '
                                                                                    'causes.',
                                                                      'source': 'return '
                                                                                'f"Error '
                                                                                'in '
                                                                                'cosinor '
                                                                                'analysis: '
                                                                                '{str(e)}"'}]},
                          'return_schema': {   'description': 'A research log '
                                                              'summarizing the '
                                                              'cosinor '
                                                              'analysis '
                                                              'process and '
                                                              'results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'physiology'}}},
{   'description': 'Calculate Apparent Diffusion Coefficient (ADC) map from '
                   'diffusion-weighted MRI data using monoexponential '
                   'diffusion model.',
    'name': 'calculate_brain_adc_map',
    'optional_parameters': [   {   'default': 'adc_map.nii.gz',
                                   'description': 'Path where the output ADC '
                                                  'map will be saved',
                                   'name': 'output_path',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Path to a binary mask file '
                                                  'to limit ADC calculation to '
                                                  'brain regions',
                                   'name': 'mask_file_path',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the 4D NIfTI file '
                                                  'containing '
                                                  'diffusion-weighted MRI data',
                                   'name': 'dwi_file_path',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'List of b-values '
                                                  'corresponding to each '
                                                  'volume in the 4D DWI data',
                                   'name': 'b_values',
                                   'type': 'List[float]'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'ADC mapping '
                                                              'process and '
                                                              'results.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'physiology'}}},
{   'description': 'Analyze calcium dynamics in endo-lysosomal compartments '
                   'using ELGA/ELGA1 probe data.',
    'name': 'analyze_endolysosomal_calcium_dynamics',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Time point (in seconds) '
                                                  'when treatment/stimulus was '
                                                  'applied',
                                   'name': 'treatment_time',
                                   'type': 'float'},
                               {   'default': '',
                                   'description': 'Type of cells used in the '
                                                  'experiment',
                                   'name': 'cell_type',
                                   'type': 'str'},
                               {   'default': '',
                                   'description': 'Name of the treatment or '
                                                  'stimulus applied',
                                   'name': 'treatment_name',
                                   'type': 'str'},
                               {   'default': 'calcium_analysis_results.txt',
                                   'description': 'Name of the file to save '
                                                  'detailed analysis results',
                                   'name': 'output_file',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Time points of the '
                                                  'measurements in seconds',
                                   'name': 'time_points',
                                   'type': 'numpy.ndarray or list'},
                               {   'default': None,
                                   'description': 'Luminescence intensity '
                                                  'values from ELGA/ELGA1 '
                                                  'probes corresponding to '
                                                  'Ca2+ levels',
                                   'name': 'luminescence_values',
                                   'type': 'numpy.ndarray or list'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'A research log '
                                                              'summarizing the '
                                                              'calcium '
                                                              'dynamics '
                                                              'analysis and '
                                                              'key findings',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'physiology'}}},
{   'description': 'Analyzes fatty acid composition in tissue samples using '
                   'gas chromatography data.',
    'name': 'analyze_fatty_acid_composition_by_gc',
    'optional_parameters': [   {   'default': './results',
                                   'description': 'Directory where result '
                                                  'files will be saved',
                                   'name': 'output_directory',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the CSV file '
                                                  'containing gas '
                                                  'chromatography data with '
                                                  "columns 'retention_time' "
                                                  "and 'peak_area'",
                                   'name': 'gc_data_file',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Type of tissue sample '
                                                  '(e.g., liver, kidney, '
                                                  'heart, muscle, adipose)',
                                   'name': 'tissue_type',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Identifier for the sample '
                                                  'being analyzed',
                                   'name': 'sample_id',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Missing '
                                                                                   'columns '
                                                                                   'in '
                                                                                   'the '
                                                                                   'input '
                                                                                   'CSV '
                                                                                   'file.',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'input '
                                                                                    'CSV '
                                                                                    'file '
                                                                                    'contains '
                                                                                    'the '
                                                                                    'required '
                                                                                    'columns: '
                                                                                    "'retention_time' "
                                                                                    'and '
                                                                                    "'peak_area'.",
                                                                      'source': 'log '
                                                                                '+= '
                                                                                'f"  '
                                                                                '- '
                                                                                'Error: '
                                                                                'Missing '
                                                                                'columns: '
                                                                                "{', "
                                                                                '\'.join(missing_cols)}\\n"\n'
                                                                                '            '
                                                                                'return '
                                                                                'log'},
                                                                  {   'condition': 'Error '
                                                                                   'loading '
                                                                                   'the '
                                                                                   'CSV '
                                                                                   'file.',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'file '
                                                                                    'path '
                                                                                    'and '
                                                                                    'ensure '
                                                                                    'the '
                                                                                    'CSV '
                                                                                    'file '
                                                                                    'is '
                                                                                    'valid '
                                                                                    'and '
                                                                                    'accessible.',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                'f"  '
                                                                                '- '
                                                                                'Error '
                                                                                'loading '
                                                                                'data: '
                                                                                '{str(e)}\\n"\n'
                                                                                '        '
                                                                                'return '
                                                                                'log'},
                                                                  {   'condition': 'Total '
                                                                                   'peak '
                                                                                   'area '
                                                                                   'is '
                                                                                   'zero.',
                                                                      'resolution': 'Verify '
                                                                                    'the '
                                                                                    'input '
                                                                                    'data '
                                                                                    'and '
                                                                                    'ensure '
                                                                                    'that '
                                                                                    'the '
                                                                                    'peak '
                                                                                    'areas '
                                                                                    'are '
                                                                                    'not '
                                                                                    'all '
                                                                                    'zero.',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                '"  '
                                                                                '- '
                                                                                'Error: '
                                                                                'Total '
                                                                                'peak '
                                                                                'area '
                                                                                'is '
                                                                                'zero, '
                                                                                'cannot '
                                                                                'calculate '
                                                                                'percentages.\\n"\n'
                                                                                '        '
                                                                                'return '
                                                                                'log'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'physiology'}}},
{   'description': 'Analyzes raw blood pressure data to calculate key '
                   'hemodynamic parameters.',
    'name': 'analyze_hemodynamic_data',
    'optional_parameters': [   {   'default': 'hemodynamic_results.csv',
                                   'description': 'Filename to save the '
                                                  'calculated parameters',
                                   'name': 'output_file',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Raw blood pressure '
                                                  'measurements in mmHg',
                                   'name': 'pressure_data',
                                   'type': 'numpy.ndarray'},
                               {   'default': None,
                                   'description': 'Data acquisition rate in Hz '
                                                  '(samples per second)',
                                   'name': 'sampling_rate',
                                   'type': 'float'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'physiology'}}},
{   'description': 'Simulates the transport and binding of thyroid hormones '
                   'across different tissue compartments using an ODE-based '
                   'pharmacokinetic model.',
    'name': 'simulate_thyroid_hormone_pharmacokinetics',
    'optional_parameters': [   {   'default': '(0, 24)',
                                   'description': 'Start and end time for '
                                                  'simulation in hours',
                                   'name': 'time_span',
                                   'type': 'tuple'},
                               {   'default': 100,
                                   'description': 'Number of time points to '
                                                  'output',
                                   'name': 'time_points',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Dictionary containing model '
                                                  'parameters including '
                                                  'transport_rates, '
                                                  'binding_constants, '
                                                  'metabolism_rates, and '
                                                  'volumes',
                                   'name': 'parameters',
                                   'type': 'dict'},
                               {   'default': None,
                                   'description': 'Dictionary of initial '
                                                  'concentrations for all '
                                                  'molecular species in each '
                                                  'compartment',
                                   'name': 'initial_conditions',
                                   'type': 'dict'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Simulation '
                                                                                   'fails',
                                                                      'resolution': 'Check '
                                                                                    'simulation '
                                                                                    'parameters '
                                                                                    'and '
                                                                                    'initial '
                                                                                    'conditions.',
                                                                      'source': 'return '
                                                                                'f"Simulation '
                                                                                'failed: '
                                                                                '{solution.message}"'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'simulation and '
                                                              'results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'simulation',
                                           'domain': 'physiology'}}},
{   'description': 'Analyzes an image to detect and quantify amyloid-beta '
                   'plaques, returning a detailed analysis log.',
    'name': 'quantify_amyloid_beta_plaques',
    'optional_parameters': [   {   'default': './results',
                                   'description': 'Directory where results '
                                                  'will be saved',
                                   'name': 'output_dir',
                                   'type': 'str'},
                               {   'default': 'otsu',
                                   'description': 'Method for image '
                                                  'thresholding (otsu, '
                                                  'adaptive, or manual)',
                                   'name': 'threshold_method',
                                   'type': 'str'},
                               {   'default': 50,
                                   'description': 'Minimum size in pixels² for '
                                                  'a region to be considered a '
                                                  'plaque',
                                   'name': 'min_plaque_size',
                                   'type': 'int'},
                               {   'default': 127,
                                   'description': 'Threshold value to use when '
                                                  'threshold_method is manual',
                                   'name': 'manual_threshold',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the image file to '
                                                  'be analyzed for '
                                                  'amyloid-beta plaques',
                                   'name': 'image_path',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': None,
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'physiology'}}}
]
