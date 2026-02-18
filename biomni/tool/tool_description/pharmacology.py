description = [
{   'description': 'Run DiffDock molecular docking using a protein PDB file '
                   'and a SMILES string for the ligand, executing the process '
                   'in a Docker container.',
    'name': 'run_diffdock_with_smiles',
    'optional_parameters': [   {   'default': 0,
                                   'description': 'GPU device ID to use for '
                                                  'computation',
                                   'name': 'gpu_device',
                                   'type': 'int'},
                               {   'default': True,
                                   'description': 'Whether to use GPU '
                                                  'acceleration for docking',
                                   'name': 'use_gpu',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the protein PDB '
                                                  'file for docking',
                                   'name': 'pdb_path',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'SMILES string '
                                                  'representation of the '
                                                  'ligand molecule',
                                   'name': 'smiles_string',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Local directory path where '
                                                  'docking results will be '
                                                  'saved',
                                   'name': 'local_output_dir',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'The '
                                                                                   'PDB '
                                                                                   'file '
                                                                                   'does '
                                                                                   'not '
                                                                                   'exist.',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'PDB '
                                                                                    'file '
                                                                                    'path '
                                                                                    'is '
                                                                                    'correct '
                                                                                    'and '
                                                                                    'the '
                                                                                    'file '
                                                                                    'exists.',
                                                                      'source': 'raise '
                                                                                'FileNotFoundError(f"The '
                                                                                'PDB '
                                                                                'file '
                                                                                "'{pdb_path}' "
                                                                                'does '
                                                                                'not '
                                                                                'exist.")'},
                                                                  {   'condition': 'An '
                                                                                   'error '
                                                                                   'occurred '
                                                                                   'during '
                                                                                   'the '
                                                                                   'Docker '
                                                                                   'command '
                                                                                   'execution.',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'Docker '
                                                                                    'command '
                                                                                    'output '
                                                                                    '(stderr) '
                                                                                    'for '
                                                                                    'details '
                                                                                    'on '
                                                                                    'the '
                                                                                    'error.  '
                                                                                    'Ensure '
                                                                                    'Docker '
                                                                                    'is '
                                                                                    'installed '
                                                                                    'and '
                                                                                    'configured '
                                                                                    'correctly.  '
                                                                                    'Verify '
                                                                                    'the '
                                                                                    'input '
                                                                                    'parameters '
                                                                                    '(PDB '
                                                                                    'path, '
                                                                                    'SMILES '
                                                                                    'string) '
                                                                                    'are '
                                                                                    'valid.',
                                                                      'source': 'result.returncode '
                                                                                '!= '
                                                                                '0: '
                                                                                '... '
                                                                                'return '
                                                                                'f"Error '
                                                                                'during '
                                                                                'inference: '
                                                                                '{result.stderr.strip()}"'},
                                                                  {   'condition': 'A '
                                                                                   'FileNotFoundError '
                                                                                   'occurs.',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'file '
                                                                                    'paths '
                                                                                    'and '
                                                                                    'ensure '
                                                                                    'the '
                                                                                    'files '
                                                                                    'exist.',
                                                                      'source': 'except '
                                                                                'FileNotFoundError '
                                                                                'as '
                                                                                'e: '
                                                                                'return '
                                                                                'f"File '
                                                                                'error: '
                                                                                '{e}"'},
                                                                  {   'condition': 'A '
                                                                                   'subprocess.CalledProcessError '
                                                                                   'occurs.',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'command '
                                                                                    'being '
                                                                                    'executed '
                                                                                    'and '
                                                                                    'the '
                                                                                    'environment '
                                                                                    "it's "
                                                                                    'running '
                                                                                    'in.',
                                                                      'source': 'except '
                                                                                'subprocess.CalledProcessError '
                                                                                'as '
                                                                                'e: '
                                                                                'return '
                                                                                'f"Command '
                                                                                'execution '
                                                                                'error: '
                                                                                '{e}"'},
                                                                  {   'condition': 'An '
                                                                                   'unexpected '
                                                                                   'error '
                                                                                   'occurs.',
                                                                      'resolution': 'Examine '
                                                                                    'the '
                                                                                    'error '
                                                                                    'message '
                                                                                    'for '
                                                                                    'details.',
                                                                      'source': 'except '
                                                                                'Exception '
                                                                                'as '
                                                                                'e: '
                                                                                'return '
                                                                                'f"An '
                                                                                'error '
                                                                                'occurred: '
                                                                                '{e}"'}]},
                          'return_schema': {   'description': 'A string '
                                                              'containing a '
                                                              'summary of the '
                                                              'DiffDock run, '
                                                              'including '
                                                              'status messages '
                                                              'and potential '
                                                              'error messages.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'simulation',
                                           'domain': 'pharmacology'}}},
{   'description': 'Performs molecular docking using AutoDock Vina to predict '
                   'binding affinities between small molecules and a receptor '
                   'protein.',
    'name': 'docking_autodock_vina',
    'optional_parameters': [   {   'default': 1,
                                   'description': 'Number of CPU cores to use '
                                                  'for docking',
                                   'name': 'ncpu',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'List of SMILES strings '
                                                  'representing small '
                                                  'molecules to dock',
                                   'name': 'smiles_list',
                                   'type': 'List[str]'},
                               {   'default': None,
                                   'description': 'Path to the receptor '
                                                  'protein structure PDB file',
                                   'name': 'receptor_pdb_file',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': '3D coordinates [x, y, z] of '
                                                  'the docking box center',
                                   'name': 'box_center',
                                   'type': 'List[float]'},
                               {   'default': None,
                                   'description': 'Dimensions [x, y, z] of the '
                                                  'docking box',
                                   'name': 'box_size',
                                   'type': 'List[float]'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'A string '
                                                              'containing the '
                                                              'research log.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'simulation',
                                           'domain': 'pharmacology'}}},
{   'description': 'Runs AutoSite on a PDB file to identify potential binding '
                   'sites and returns a research log with the results.',
    'name': 'run_autosite',
    'optional_parameters': [   {   'default': 1.0,
                                   'description': 'Grid spacing parameter for '
                                                  'AutoSite calculation',
                                   'name': 'spacing',
                                   'type': 'float'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the input PDB file',
                                   'name': 'pdb_file',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Directory where AutoSite '
                                                  'results will be saved',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'The '
                                                                                   'prepare_receptor4.py '
                                                                                   'script '
                                                                                   'is '
                                                                                   'not '
                                                                                   'accessible.',
                                                                      'resolution': 'Ensure '
                                                                                    'prepare_receptor4.py '
                                                                                    'is '
                                                                                    'in '
                                                                                    'the '
                                                                                    "system's "
                                                                                    'PATH '
                                                                                    'or '
                                                                                    'provide '
                                                                                    'the '
                                                                                    'correct '
                                                                                    'path.',
                                                                      'source': 'subprocess.run(["prepare_receptor", '
                                                                                '"-r", '
                                                                                'pdb_file, '
                                                                                '"-o", '
                                                                                'pdbqt_file], '
                                                                                'check=True)'},
                                                                  {   'condition': 'The '
                                                                                   'autosite '
                                                                                   'command '
                                                                                   'fails.',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'autosite '
                                                                                    'command '
                                                                                    'and '
                                                                                    'its '
                                                                                    'dependencies. '
                                                                                    'Examine '
                                                                                    'the '
                                                                                    'output '
                                                                                    'for '
                                                                                    'error '
                                                                                    'messages.',
                                                                      'source': 'subprocess.run(autosite_cmd, '
                                                                                'check=True)'},
                                                                  {   'condition': 'The '
                                                                                   'log '
                                                                                   'file '
                                                                                   '(_AutoSiteSummary.log) '
                                                                                   'is '
                                                                                   'not '
                                                                                   'found '
                                                                                   'or '
                                                                                   'does '
                                                                                   'not '
                                                                                   'contain '
                                                                                   'the '
                                                                                   'expected '
                                                                                   'box '
                                                                                   'center/size '
                                                                                   'information.',
                                                                      'resolution': 'Verify '
                                                                                    'the '
                                                                                    'output '
                                                                                    'directory '
                                                                                    'and '
                                                                                    'log '
                                                                                    'file. '
                                                                                    'Check '
                                                                                    'the '
                                                                                    'AutoSite '
                                                                                    'output '
                                                                                    'format '
                                                                                    'for '
                                                                                    'changes.',
                                                                      'source': 'with '
                                                                                'open(log_path) '
                                                                                'as '
                                                                                'log_file:\n'
                                                                                '        '
                                                                                'log_content '
                                                                                '= '
                                                                                'log_file.read()\n'
                                                                                '\n'
                                                                                '        '
                                                                                'box_center_match '
                                                                                '= '
                                                                                're.search(r"Box '
                                                                                'center:\\s*\\(([^)]+)\\)", '
                                                                                'log_content)\n'
                                                                                '        '
                                                                                'box_size_match '
                                                                                '= '
                                                                                're.search(r"Box '
                                                                                'size:\\s*\\(([^)]+)\\)", '
                                                                                'log_content)'}]},
                          'return_schema': {   'description': 'A string '
                                                              'containing the '
                                                              'research log, '
                                                              'including '
                                                              'information '
                                                              'about the '
                                                              'AutoSite run, '
                                                              'output '
                                                              'directory, and '
                                                              'box center/size '
                                                              'if found.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'simulation',
                                           'domain': 'pharmacology'}}},
{   'description': 'Computes TxGNN model predictions for drug repurposing and '
                   'returns the top predicted drugs with their scores for a '
                   'given disease.',
    'name': 'retrieve_topk_repurposing_drugs_from_disease_txgnn',
    'optional_parameters': [   {   'default': 5,
                                   'description': 'The number of top drug '
                                                  'predictions to return',
                                   'name': 'k',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'The name of the disease for '
                                                  'which to retrieve drug '
                                                  'predictions',
                                   'name': 'disease_name',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Path to the data lake',
                                   'name': 'data_lake_path',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'No '
                                                                                   'matching '
                                                                                   'disease '
                                                                                   'found',
                                                                      'resolution': 'Provide '
                                                                                    'a '
                                                                                    'disease '
                                                                                    'name '
                                                                                    'that '
                                                                                    'matches '
                                                                                    'the '
                                                                                    'available '
                                                                                    'data.',
                                                                      'source': 'return '
                                                                                'f"Error: '
                                                                                'No '
                                                                                'matching '
                                                                                'disease '
                                                                                'found '
                                                                                'for '
                                                                                "'{disease_name}'. "
                                                                                'Please '
                                                                                'try '
                                                                                'a '
                                                                                'different '
                                                                                'name."'}]},
                          'return_schema': {   'description': 'A summary of '
                                                              'the steps and '
                                                              'the top K drug '
                                                              'predictions '
                                                              'with their '
                                                              'scores.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Predicts ADMET (Absorption, Distribution, Metabolism, '
                   'Excretion, Toxicity) properties for a list of compounds '
                   'using pretrained models.',
    'name': 'predict_admet_properties',
    'optional_parameters': [   {   'default': 'MPNN',
                                   'description': 'Type of model to use for '
                                                  'ADMET prediction (options: '
                                                  "'MPNN', 'CNN', 'Morgan')",
                                   'name': 'ADMET_model_type',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'List of SMILES strings '
                                                  'representing chemical '
                                                  'compounds to analyze',
                                   'name': 'smiles_list',
                                   'type': 'List[str]'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Invalid '
                                                                                   'ADMET '
                                                                                   'model '
                                                                                   'type '
                                                                                   'is '
                                                                                   'provided.',
                                                                      'resolution': 'Provide '
                                                                                    'a '
                                                                                    'valid '
                                                                                    'ADMET '
                                                                                    'model '
                                                                                    'type '
                                                                                    'from '
                                                                                    'the '
                                                                                    'available '
                                                                                    'options.',
                                                                      'source': 'return '
                                                                                'f"Error: '
                                                                                'Invalid '
                                                                                'ADMET '
                                                                                'model '
                                                                                'type '
                                                                                "'{ADMET_model_type}'. "
                                                                                'Available '
                                                                                'options '
                                                                                'are: '
                                                                                "{', "
                                                                                '\'.join(available_model_types)}."'}]},
                          'return_schema': {   'description': 'A string '
                                                              'containing the '
                                                              'research log '
                                                              'with ADMET '
                                                              'predictions for '
                                                              'each SMILES '
                                                              'string in the '
                                                              'input list.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Predicts binding affinity between small molecules and a '
                   'protein sequence using pre-trained deep learning models.',
    'name': 'predict_binding_affinity_protein_1d_sequence',
    'optional_parameters': [   {   'default': 'MPNN-CNN',
                                   'description': 'Deep learning model '
                                                  'architecture to use for '
                                                  'binding affinity prediction '
                                                  '(options: CNN-CNN, '
                                                  'MPNN-CNN, Morgan-CNN, '
                                                  'Morgan-AAC, Daylight-AAC)',
                                   'name': 'affinity_model_type',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'List of SMILES strings '
                                                  'representing chemical '
                                                  'compounds',
                                   'name': 'smiles_list',
                                   'type': 'List[str]'},
                               {   'default': None,
                                   'description': 'Protein sequence in amino '
                                                  'acid format',
                                   'name': 'amino_acid_sequence',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Invalid '
                                                                                   'affinity '
                                                                                   'model '
                                                                                   'type '
                                                                                   'is '
                                                                                   'provided.',
                                                                      'resolution': 'Provide '
                                                                                    'a '
                                                                                    'valid '
                                                                                    'affinity '
                                                                                    'model '
                                                                                    'type '
                                                                                    'from '
                                                                                    'the '
                                                                                    'available '
                                                                                    'options.',
                                                                      'source': 'return '
                                                                                'f"Error: '
                                                                                'Invalid '
                                                                                'affinity '
                                                                                'model '
                                                                                'type '
                                                                                "'{affinity_model_type}'. "
                                                                                'Available '
                                                                                'options '
                                                                                'are: '
                                                                                "{', "
                                                                                '\'.join(available_affinity_model_types)}."'}]},
                          'return_schema': {   'description': 'A string '
                                                              'containing the '
                                                              'research log '
                                                              'with predicted '
                                                              'binding '
                                                              'affinities for '
                                                              'each SMILES '
                                                              'string and '
                                                              'amino acid '
                                                              'sequence.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Analyzes the stability of pharmaceutical formulations '
                   'under accelerated storage conditions.',
    'name': 'analyze_accelerated_stability_of_pharmaceutical_formulations',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'List of formulation '
                                                  'dictionaries containing '
                                                  'name, active ingredient, '
                                                  'concentration, and '
                                                  'excipients',
                                   'name': 'formulations',
                                   'type': 'List[dict]'},
                               {   'default': None,
                                   'description': 'List of storage condition '
                                                  'dictionaries containing '
                                                  'temperature, humidity '
                                                  '(optional), and description',
                                   'name': 'storage_conditions',
                                   'type': 'List[dict]'},
                               {   'default': None,
                                   'description': 'List of time points in days '
                                                  'to evaluate stability',
                                   'name': 'time_points',
                                   'type': 'List[int]'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'stability '
                                                              'testing process '
                                                              'and results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Generates a detailed protocol for performing a 3D '
                   'chondrogenic aggregate culture assay to evaluate '
                   "compounds' effects on chondrogenesis.",
    'name': 'run_3d_chondrogenic_aggregate_assay',
    'optional_parameters': [   {   'default': 21,
                                   'description': 'Total duration of the '
                                                  'culture period in days',
                                   'name': 'culture_duration_days',
                                   'type': 'int'},
                               {   'default': 7,
                                   'description': 'Interval in days between '
                                                  'measurements',
                                   'name': 'measurement_intervals',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Dictionary with cell '
                                                  'information including '
                                                  "'source', 'passage_number', "
                                                  "and 'cell_density'",
                                   'name': 'chondrocyte_cells',
                                   'type': 'dict'},
                               {   'default': None,
                                   'description': 'List of compounds to test, '
                                                  "each with 'name', "
                                                  "'concentration', and "
                                                  "'vehicle' keys",
                                   'name': 'test_compounds',
                                   'type': 'list of dict'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Detailed '
                                                              'protocol '
                                                              'document for '
                                                              'the 3D '
                                                              'chondrogenic '
                                                              'aggregate '
                                                              'culture assay',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'general',
                                           'domain': 'pharmacology'}}},
{   'description': 'Grade and monitor adverse events in animal studies using '
                   'the VCOG-CTCAE standard.',
    'name': 'grade_adverse_events_using_vcog_ctcae',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to a CSV file '
                                                  'containing clinical '
                                                  'evaluation data with '
                                                  'columns: subject_id, '
                                                  'time_point, symptom, '
                                                  'severity, measurement '
                                                  '(optional)',
                                   'name': 'clinical_data_file',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Error '
                                                                                   'loading '
                                                                                   'data',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'file '
                                                                                    'path '
                                                                                    'and '
                                                                                    'ensure '
                                                                                    'the '
                                                                                    'CSV '
                                                                                    'file '
                                                                                    'exists '
                                                                                    'and '
                                                                                    'is '
                                                                                    'correctly '
                                                                                    'formatted.',
                                                                      'source': 'Error '
                                                                                'loading '
                                                                                'data: '
                                                                                '{str(e)}'}]},
                          'return_schema': {   'description': 'A research log '
                                                              'summarizing the '
                                                              'adverse event '
                                                              'grading process '
                                                              'and results. '
                                                              'The graded '
                                                              'events are '
                                                              'saved to '
                                                              "'vcog_ctcae_graded_events.csv'.",
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Analyze biodistribution and pharmacokinetic profile of '
                   'radiolabeled antibodies.',
    'name': 'analyze_radiolabeled_antibody_biodistribution',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'Time points (hours) at '
                                                  'which measurements were '
                                                  'taken',
                                   'name': 'time_points',
                                   'type': 'List[float] or numpy.ndarray'},
                               {   'default': None,
                                   'description': 'Dictionary where keys are '
                                                  'tissue names and values are '
                                                  'lists/arrays of %IA/g '
                                                  'measurements corresponding '
                                                  'to time_points. Must '
                                                  "include 'tumor' as one of "
                                                  'the keys',
                                   'name': 'tissue_data',
                                   'type': 'dict'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Tumor '
                                                                                   'data '
                                                                                   'not '
                                                                                   'provided '
                                                                                   'in '
                                                                                   'tissue_data '
                                                                                   'dictionary',
                                                                      'resolution': 'Ensure '
                                                                                    "'tumor' "
                                                                                    'key '
                                                                                    'exists '
                                                                                    'in '
                                                                                    'tissue_data '
                                                                                    'dictionary.',
                                                                      'source': 'return '
                                                                                '"Error: '
                                                                                'Tumor '
                                                                                'data '
                                                                                'must '
                                                                                'be '
                                                                                'provided '
                                                                                'in '
                                                                                'tissue_data '
                                                                                'dictionary"'},
                                                                  {   'condition': 'Fitting '
                                                                                   'of '
                                                                                   'bi-exponential '
                                                                                   'model '
                                                                                   'fails '
                                                                                   'for '
                                                                                   'a '
                                                                                   'tissue',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'input '
                                                                                    'data '
                                                                                    'for '
                                                                                    'the '
                                                                                    'specific '
                                                                                    'tissue '
                                                                                    'and '
                                                                                    'ensure '
                                                                                    'it '
                                                                                    'is '
                                                                                    'suitable '
                                                                                    'for '
                                                                                    'the '
                                                                                    'bi-exponential '
                                                                                    'model. '
                                                                                    'Review '
                                                                                    'the '
                                                                                    'error '
                                                                                    'message '
                                                                                    '(e) '
                                                                                    'for '
                                                                                    'specific '
                                                                                    'fitting '
                                                                                    'issues.',
                                                                      'source': 'results["pk_parameters"][tissue] '
                                                                                '= '
                                                                                'f"Fitting '
                                                                                'failed: '
                                                                                '{str(e)}"'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'biodistribution '
                                                              'analysis, '
                                                              'pharmacokinetic '
                                                              'parameters, and '
                                                              'tumor-to-normal '
                                                              'tissue ratios',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Estimate radiation absorbed doses to tumor and normal '
                   'organs for alpha-particle radiotherapeutics using the '
                   'Medical Internal Radiation Dose (MIRD) schema.',
    'name': 'estimate_alpha_particle_radiotherapy_dosimetry',
    'optional_parameters': [   {   'default': 'dosimetry_results.csv',
                                   'description': 'Filename to save the '
                                                  'dosimetry results',
                                   'name': 'output_file',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Dictionary containing '
                                                  'organ/tissue names as keys '
                                                  'and a list of time-activity '
                                                  'measurements as values. '
                                                  'Each measurement should be '
                                                  'a tuple of (time_hours, '
                                                  'percent_injected_activity). '
                                                  'Must include entries for '
                                                  'all relevant organs '
                                                  "including 'tumor'.",
                                   'name': 'biodistribution_data',
                                   'type': 'dict'},
                               {   'default': None,
                                   'description': 'Dictionary containing '
                                                  'radiation parameters for '
                                                  'the alpha-emitting '
                                                  'radionuclide including '
                                                  "'radionuclide', "
                                                  "'half_life_hours', "
                                                  "'energy_per_decay_MeV', "
                                                  "'radiation_weighting_factor', "
                                                  "and 'S_factors'.",
                                   'name': 'radiation_parameters',
                                   'type': 'dict'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'dosimetry '
                                                              'estimation '
                                                              'process and '
                                                              'results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Perform a Methylome-wide Association Study (MWAS) to '
                   'identify CpG sites significantly associated with CYP2C19 '
                   'metabolizer status.',
    'name': 'perform_mwas_cyp2c19_metabolizer_status',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Path to CSV or TSV file '
                                                  'containing covariates to '
                                                  'adjust for in the '
                                                  'regression model (e.g., '
                                                  'age, sex, smoking status).',
                                   'name': 'covariates_path',
                                   'type': 'str'},
                               {   'default': 0.05,
                                   'description': 'P-value threshold for '
                                                  'significance after multiple '
                                                  'testing correction.',
                                   'name': 'pvalue_threshold',
                                   'type': 'float'},
                               {   'default': 'significant_cpg_sites.csv',
                                   'description': 'Filename to save '
                                                  'significant CpG sites.',
                                   'name': 'output_file',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to CSV or TSV file '
                                                  'containing DNA methylation '
                                                  'beta values. Rows should be '
                                                  'samples, columns should be '
                                                  'CpG sites.',
                                   'name': 'methylation_data_path',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Path to CSV or TSV file '
                                                  'containing CYP2C19 '
                                                  'metabolizer status for each '
                                                  'sample. Should have a '
                                                  'sample ID column and a '
                                                  'status column.',
                                   'name': 'metabolizer_status_path',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'A research log '
                                                              'summarizing the '
                                                              'MWAS analysis '
                                                              'and results.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Calculate key physicochemical properties of a drug '
                   'candidate molecule.',
    'name': 'calculate_physicochemical_properties',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'The molecular structure in '
                                                  'SMILES format',
                                   'name': 'smiles_string',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Invalid '
                                                                                   'SMILES '
                                                                                   'string '
                                                                                   'provided.',
                                                                      'resolution': 'Ensure '
                                                                                    'a '
                                                                                    'valid '
                                                                                    'SMILES '
                                                                                    'string '
                                                                                    'is '
                                                                                    'provided '
                                                                                    'as '
                                                                                    'input.',
                                                                      'source': 'return '
                                                                                '"ERROR: '
                                                                                'Invalid '
                                                                                'SMILES '
                                                                                'string '
                                                                                'provided."'},
                                                                  {   'condition': 'Failed '
                                                                                   'to '
                                                                                   'process '
                                                                                   'SMILES '
                                                                                   'string.',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'SMILES '
                                                                                    'string '
                                                                                    'for '
                                                                                    'errors '
                                                                                    'or '
                                                                                    'inconsistencies.',
                                                                      'source': 'return '
                                                                                'f"ERROR: '
                                                                                'Failed '
                                                                                'to '
                                                                                'process '
                                                                                'SMILES '
                                                                                'string: '
                                                                                '{str(e)}"'}]},
                          'return_schema': {   'description': 'A research log '
                                                              'summarizing the '
                                                              'calculated '
                                                              'physicochemical '
                                                              'properties and '
                                                              'indicating '
                                                              'where the '
                                                              'detailed '
                                                              'results are '
                                                              'saved',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Analyze tumor growth inhibition in xenograft models across '
                   'different treatment groups.',
    'name': 'analyze_xenograft_tumor_growth_inhibition',
    'optional_parameters': [   {   'default': './results',
                                   'description': 'Directory to save output '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to CSV or TSV file '
                                                  'containing tumor volume '
                                                  'measurements',
                                   'name': 'data_path',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Name of the column '
                                                  'containing time points',
                                   'name': 'time_column',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Name of the column '
                                                  'containing tumor volume '
                                                  'measurements',
                                   'name': 'volume_column',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Name of the column '
                                                  'containing treatment group '
                                                  'labels',
                                   'name': 'group_column',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Name of the column '
                                                  'containing subject/mouse '
                                                  'identifiers',
                                   'name': 'subject_column',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps, '
                                                              'findings, and '
                                                              'generated file '
                                                              'paths',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Analyze western blot or DNA electrophoresis images and '
                   'return pixel distribution statistics including intensity '
                   'statistics, percentiles, and brightness distribution. Use '
                   'this to determine appropriate threshold values for '
                   'find_roi_from_image.',
    'name': 'analyze_pixel_distribution',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the input grayscale '
                                                  'image. Automatically '
                                                  'appends .png if no suffix '
                                                  'is provided.',
                                   'name': 'image_path',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Image '
                                                                                   'not '
                                                                                   'found',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'image '
                                                                                    'path '
                                                                                    'is '
                                                                                    'correct '
                                                                                    'and '
                                                                                    'the '
                                                                                    'file '
                                                                                    'exists.',
                                                                      'source': 'raise '
                                                                                'FileNotFoundError(f"Image '
                                                                                'not '
                                                                                'found '
                                                                                'at '
                                                                                '{image_path}")'}]},
                          'return_schema': {   'description': 'Summary '
                                                              'dictionary '
                                                              'containing '
                                                              'image shape, '
                                                              'intensity '
                                                              'statistics, '
                                                              'percentiles, '
                                                              'histogram '
                                                              'values, and '
                                                              'brightness '
                                                              'distribution '
                                                              'for predefined '
                                                              'buckets.',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Find the ROIs (regions of interest) of protein bands from '
                   'a Western blot or DNA electrophoresis image using '
                   'threshold-based blob detection. Returns annotated image '
                   'path and list of ROI coordinates. Use '
                   'analyze_pixel_distribution first to determine appropriate '
                   'threshold values. The returned ROI list can be converted '
                   'to target_bands format for analyze_western_blot.',
    'name': 'find_roi_from_image',
    'optional_parameters': [   {   'default': True,
                                   'description': 'If True, draw green '
                                                  'contours (hulls) and blue '
                                                  'keypoint boxes for '
                                                  'debugging.',
                                   'name': 'debug',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the input image.',
                                   'name': 'image_path',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Pixel intensities lower '
                                                  'than this value are used to '
                                                  'make the binary image. Use '
                                                  'analyze_pixel_distribution '
                                                  'to determine appropriate '
                                                  'values.',
                                   'name': 'lower_threshold',
                                   'type': 'int'},
                               {   'default': None,
                                   'description': 'Pixel intensities greater '
                                                  'than or equal to this value '
                                                  'are used to make the binary '
                                                  'image. Use '
                                                  'analyze_pixel_distribution '
                                                  'to determine appropriate '
                                                  'values.',
                                   'name': 'upper_threshold',
                                   'type': 'int'},
                               {   'default': None,
                                   'description': 'The actual number of bands '
                                                  'expected in the image.',
                                   'name': 'number_of_bands',
                                   'type': 'int'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'threshold '
                                                                                   'values '
                                                                                   'are '
                                                                                   'outside '
                                                                                   'the '
                                                                                   'valid '
                                                                                   'range '
                                                                                   'or '
                                                                                   'inconsistent.',
                                                                      'resolution': 'Ensure '
                                                                                    'threshold '
                                                                                    'values '
                                                                                    'are '
                                                                                    'within '
                                                                                    'the '
                                                                                    'valid '
                                                                                    'range '
                                                                                    'and '
                                                                                    'consistent.',
                                                                      'source': 'raise '
                                                                                "ValueError('...')"},
                                                                  {   'condition': 'source '
                                                                                   'image '
                                                                                   'cannot '
                                                                                   'be '
                                                                                   'loaded.',
                                                                      'resolution': 'Check '
                                                                                    'if '
                                                                                    'the '
                                                                                    'image '
                                                                                    'file '
                                                                                    'exists '
                                                                                    'and '
                                                                                    'is '
                                                                                    'accessible.',
                                                                      'source': 'raise '
                                                                                'FileNotFoundError'}]},
                          'return_schema': {   'description': 'A tuple '
                                                              'containing: - '
                                                              'str: Absolute '
                                                              'path to the '
                                                              'saved annotated '
                                                              'image - list: '
                                                              'List of ROI '
                                                              'coordinates in '
                                                              '(x, y, width, '
                                                              'height) format.',
                                               'type': 'tuple[str, list]'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Performs densitometric analysis of Western blot images to '
                   'quantify relative protein expression.',
    'name': 'analyze_western_blot',
    'optional_parameters': [   {   'default': './results',
                                   'description': 'Directory to save output '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the Western blot '
                                                  'image file',
                                   'name': 'blot_image_path',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'List of dictionaries '
                                                  'containing information '
                                                  'about target protein bands, '
                                                  "each with 'name' and 'roi' "
                                                  '(region of interest as [x, '
                                                  'y, width, height])',
                                   'name': 'target_bands',
                                   'type': 'list of dict'},
                               {   'default': None,
                                   'description': "Dictionary with 'name' and "
                                                  "'roi' for the loading "
                                                  'control protein (e.g., '
                                                  'β-actin, GAPDH)',
                                   'name': 'loading_control_band',
                                   'type': 'dict'},
                               {   'default': None,
                                   'description': 'Dictionary containing '
                                                  'information about '
                                                  'antibodies used with '
                                                  "'primary' and 'secondary' "
                                                  'keys',
                                   'name': 'antibody_info',
                                   'type': 'dict'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'Western blot '
                                                              'analysis '
                                                              'process and '
                                                              'results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Query drug-drug interactions from DDInter database to '
                   'identify potential interactions, mechanisms, and severity '
                   'levels between specified drugs.',
    'name': 'query_drug_interactions',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Filter results by specific '
                                                  'interaction types',
                                   'name': 'interaction_types',
                                   'type': 'List[str]'},
                               {   'default': None,
                                   'description': 'Filter results by severity '
                                                  'levels (Major, Moderate, '
                                                  'Minor)',
                                   'name': 'severity_levels',
                                   'type': 'List[str]'},
                               {   'default': None,
                                   'description': 'Path to data lake directory '
                                                  'containing DDInter data',
                                   'name': 'data_lake_path',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'List of drug names to query '
                                                  'for interactions',
                                   'name': 'drug_names',
                                   'type': 'List[str]'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'FileNotFoundError '
                                                                                   'during '
                                                                                   'data '
                                                                                   'loading',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'data_lake_path '
                                                                                    'is '
                                                                                    'correct '
                                                                                    'and '
                                                                                    'the '
                                                                                    'DDInter '
                                                                                    'data '
                                                                                    'exists.',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                'f"Error '
                                                                                'during '
                                                                                'interaction '
                                                                                'query: '
                                                                                '{str(e)}\\n"'},
                                                                  {   'condition': 'General '
                                                                                   'exception '
                                                                                   'during '
                                                                                   'interaction '
                                                                                   'query',
                                                                      'resolution': 'Inspect '
                                                                                    'the '
                                                                                    'specific '
                                                                                    'exception '
                                                                                    'and '
                                                                                    'address '
                                                                                    'the '
                                                                                    'underlying '
                                                                                    'cause '
                                                                                    '(e.g., '
                                                                                    'invalid '
                                                                                    'data '
                                                                                    'format, '
                                                                                    'incorrect '
                                                                                    'input).',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                'f"Error '
                                                                                'during '
                                                                                'interaction '
                                                                                'query: '
                                                                                '{str(e)}\\n"'},
                                                                  {   'condition': 'No '
                                                                                   'valid '
                                                                                   'drugs '
                                                                                   'found '
                                                                                   'in '
                                                                                   'DDInter '
                                                                                   'database',
                                                                      'resolution': 'Verify '
                                                                                    'that '
                                                                                    'the '
                                                                                    'drug '
                                                                                    'names '
                                                                                    'provided '
                                                                                    'are '
                                                                                    'present '
                                                                                    'in '
                                                                                    'the '
                                                                                    'DDInter '
                                                                                    'database '
                                                                                    'or '
                                                                                    'correct '
                                                                                    'the '
                                                                                    'drug '
                                                                                    'names.',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                '"Error: '
                                                                                'No '
                                                                                'valid '
                                                                                'drugs '
                                                                                'found '
                                                                                'in '
                                                                                'DDInter '
                                                                                'database\\n"'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'with detailed '
                                                              'interaction '
                                                              'analysis',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'pharmacology'}}},
{   'description': 'Analyze safety of a drug combination for potential '
                   'interactions using DDInter database with comprehensive '
                   'risk assessment and clinical recommendations.',
    'name': 'check_drug_combination_safety',
    'optional_parameters': [   {   'default': True,
                                   'description': 'Include interaction '
                                                  'mechanism descriptions in '
                                                  'results',
                                   'name': 'include_mechanisms',
                                   'type': 'bool'},
                               {   'default': True,
                                   'description': 'Include management '
                                                  'recommendations in results',
                                   'name': 'include_management',
                                   'type': 'bool'},
                               {   'default': None,
                                   'description': 'Path to data lake directory '
                                                  'containing DDInter data',
                                   'name': 'data_lake_path',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'List of drugs to analyze '
                                                  'for combination safety',
                                   'name': 'drug_list',
                                   'type': 'List[str]'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Drugs '
                                                                                   'not '
                                                                                   'found '
                                                                                   'in '
                                                                                   'DDInter '
                                                                                   'database',
                                                                      'resolution': 'Ensure '
                                                                                    'drugs '
                                                                                    'are '
                                                                                    'in '
                                                                                    'the '
                                                                                    'database '
                                                                                    'or '
                                                                                    'handle '
                                                                                    'missing '
                                                                                    'drugs '
                                                                                    'gracefully.',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                '"Warning: '
                                                                                'The '
                                                                                'following '
                                                                                'drugs '
                                                                                'were '
                                                                                'not '
                                                                                'found '
                                                                                'in '
                                                                                'DDInter '
                                                                                'database:\\n"'},
                                                                  {   'condition': 'At '
                                                                                   'least '
                                                                                   '2 '
                                                                                   'valid '
                                                                                   'drugs '
                                                                                   'are '
                                                                                   'required '
                                                                                   'for '
                                                                                   'combination '
                                                                                   'analysis',
                                                                      'resolution': 'Ensure '
                                                                                    'at '
                                                                                    'least '
                                                                                    'two '
                                                                                    'valid '
                                                                                    'drugs '
                                                                                    'are '
                                                                                    'provided '
                                                                                    'as '
                                                                                    'input.',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                '"Error: '
                                                                                'At '
                                                                                'least '
                                                                                '2 '
                                                                                'valid '
                                                                                'drugs '
                                                                                'required '
                                                                                'for '
                                                                                'combination '
                                                                                'analysis\\n"'},
                                                                  {   'condition': 'Error '
                                                                                   'during '
                                                                                   'safety '
                                                                                   'analysis',
                                                                      'resolution': 'Inspect '
                                                                                    'the '
                                                                                    'exception '
                                                                                    "'e' "
                                                                                    'to '
                                                                                    'determine '
                                                                                    'the '
                                                                                    'root '
                                                                                    'cause '
                                                                                    'and '
                                                                                    'implement '
                                                                                    'appropriate '
                                                                                    'error '
                                                                                    'handling.',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                'f"Error '
                                                                                'during '
                                                                                'safety '
                                                                                'analysis: '
                                                                                '{str(e)}\\n"'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'with safety '
                                                              'analysis and '
                                                              'recommendations',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Analyze interaction mechanisms between two specific drugs '
                   'providing detailed mechanistic insights and clinical '
                   'significance assessment.',
    'name': 'analyze_interaction_mechanisms',
    'optional_parameters': [   {   'default': True,
                                   'description': 'Include detailed '
                                                  'mechanistic information in '
                                                  'analysis',
                                   'name': 'detailed_analysis',
                                   'type': 'bool'},
                               {   'default': None,
                                   'description': 'Path to data lake directory '
                                                  'containing DDInter data',
                                   'name': 'data_lake_path',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Pair of drug names to '
                                                  'analyze (drug1, drug2)',
                                   'name': 'drug_pair',
                                   'type': 'Tuple[str, str]'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Drug '
                                                                                   'not '
                                                                                   'found '
                                                                                   'in '
                                                                                   'DDInter '
                                                                                   'database',
                                                                      'resolution': 'Ensure '
                                                                                    'drug '
                                                                                    'names '
                                                                                    'are '
                                                                                    'valid '
                                                                                    'and '
                                                                                    'present '
                                                                                    'in '
                                                                                    'the '
                                                                                    'DDInter '
                                                                                    'database.',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                'f"Error: '
                                                                                'Drug '
                                                                                "'{drug_a}' "
                                                                                'not '
                                                                                'found '
                                                                                'in '
                                                                                'DDInter '
                                                                                'database\\n"'},
                                                                  {   'condition': 'Drug '
                                                                                   'not '
                                                                                   'found '
                                                                                   'in '
                                                                                   'DDInter '
                                                                                   'database',
                                                                      'resolution': 'Ensure '
                                                                                    'drug '
                                                                                    'names '
                                                                                    'are '
                                                                                    'valid '
                                                                                    'and '
                                                                                    'present '
                                                                                    'in '
                                                                                    'the '
                                                                                    'DDInter '
                                                                                    'database.',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                'f"Error: '
                                                                                'Drug '
                                                                                "'{drug_b}' "
                                                                                'not '
                                                                                'found '
                                                                                'in '
                                                                                'DDInter '
                                                                                'database\\n"'},
                                                                  {   'condition': 'Error '
                                                                                   'during '
                                                                                   'mechanism '
                                                                                   'analysis',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'exception '
                                                                                    'message '
                                                                                    'for '
                                                                                    'the '
                                                                                    'specific '
                                                                                    'error '
                                                                                    'and '
                                                                                    'address '
                                                                                    'the '
                                                                                    'underlying '
                                                                                    'issue '
                                                                                    '(e.g., '
                                                                                    'data '
                                                                                    'loading, '
                                                                                    'data '
                                                                                    'format).',
                                                                      'source': 'log '
                                                                                '+= '
                                                                                'f"Error '
                                                                                'during '
                                                                                'mechanism '
                                                                                'analysis: '
                                                                                '{str(e)}\\n"'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'with mechanism '
                                                              'analysis',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': "Find alternative drugs that don't interact with "
                   'contraindicated drugs using DDInter database for safer '
                   'therapeutic substitutions.',
    'name': 'find_alternative_drugs_ddinter',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Limit search to specific '
                                                  'therapeutic class',
                                   'name': 'therapeutic_class',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Path to data lake directory '
                                                  'containing DDInter data',
                                   'name': 'data_lake_path',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Drug to find alternatives '
                                                  'for',
                                   'name': 'target_drug',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'List of drugs to avoid '
                                                  'interactions with',
                                   'name': 'contraindicated_drugs',
                                   'type': 'List[str]'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Target '
                                                                                   'drug '
                                                                                   'not '
                                                                                   'found '
                                                                                   'in '
                                                                                   'DDInter '
                                                                                   'database',
                                                                      'resolution': 'Ensure '
                                                                                    'target '
                                                                                    'drug '
                                                                                    'is '
                                                                                    'in '
                                                                                    'the '
                                                                                    'database.',
                                                                      'source': 'return '
                                                                                'log'},
                                                                  {   'condition': 'Error '
                                                                                   'during '
                                                                                   'alternative '
                                                                                   'drug '
                                                                                   'search',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'exception '
                                                                                    'message '
                                                                                    'for '
                                                                                    'details '
                                                                                    'and '
                                                                                    'resolve '
                                                                                    'the '
                                                                                    'underlying '
                                                                                    'issue.',
                                                                      'source': 'str(e)'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'with '
                                                              'alternative '
                                                              'drug '
                                                              'recommendations',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}},
{   'description': 'Query FDA adverse event reports for specific drugs from '
                   'the OpenFDA database to identify potential safety signals, '
                   'reaction patterns, and regulatory intelligence.',
    'name': 'query_fda_adverse_events',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Optional date range as '
                                                  '(start_date, end_date) in '
                                                  'YYYY-MM-DD format',
                                   'name': 'date_range',
                                   'type': 'Tuple[str, str]'},
                               {   'default': None,
                                   'description': 'Optional filter by severity '
                                                  "levels ['serious', "
                                                  "'non_serious']",
                                   'name': 'severity_filter',
                                   'type': 'List[str]'},
                               {   'default': None,
                                   'description': 'Optional filter by outcomes '
                                                  "['life_threatening', "
                                                  "'hospitalization', 'death']",
                                   'name': 'outcome_filter',
                                   'type': 'List[str]'},
                               {   'default': 100,
                                   'description': 'Maximum number of results '
                                                  'to return',
                                   'name': 'limit',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Name of the drug to query '
                                                  'for adverse events',
                                   'name': 'drug_name',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Formatted '
                                                              'string with '
                                                              'adverse event '
                                                              'analysis',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'pharmacology'}}},
{   'description': 'Retrieve FDA drug label information including indications, '
                   'contraindications, warnings, and dosage information from '
                   'the OpenFDA database.',
    'name': 'get_fda_drug_label_info',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Optional list of specific '
                                                  'sections to retrieve '
                                                  "['indications_and_usage', "
                                                  "'contraindications', "
                                                  "'warnings', "
                                                  "'dosage_and_administration']",
                                   'name': 'sections',
                                   'type': 'List[str]'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Name of the drug to query '
                                                  'for label information',
                                   'name': 'drug_name',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'drug_name '
                                                                                   'is '
                                                                                   'empty '
                                                                                   'or '
                                                                                   'whitespace '
                                                                                   'only',
                                                                      'resolution': 'Provide '
                                                                                    'a '
                                                                                    'valid '
                                                                                    'drug '
                                                                                    'name',
                                                                      'source': 'return '
                                                                                '"Error: '
                                                                                'Drug '
                                                                                'name '
                                                                                'cannot '
                                                                                'be '
                                                                                'empty"'},
                                                                  {   'condition': 'Unable '
                                                                                   'to '
                                                                                   'standardize '
                                                                                   'drug '
                                                                                   'name',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'drug '
                                                                                    'name '
                                                                                    'and/or '
                                                                                    'the '
                                                                                    'standardization '
                                                                                    'process',
                                                                      'source': 'return '
                                                                                'f"Error: '
                                                                                'Unable '
                                                                                'to '
                                                                                'standardize '
                                                                                'drug '
                                                                                'name '
                                                                                '\'{drug_name}\'"'},
                                                                  {   'condition': 'No '
                                                                                   'label '
                                                                                   'information '
                                                                                   'found',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'drug '
                                                                                    'name '
                                                                                    'and/or '
                                                                                    'the '
                                                                                    'availability '
                                                                                    'of '
                                                                                    'label '
                                                                                    'information',
                                                                      'source': 'return '
                                                                                'f"No '
                                                                                'label '
                                                                                'information '
                                                                                'found '
                                                                                'for '
                                                                                'drug: '
                                                                                '{drug_name}"'},
                                                                  {   'condition': 'Exception '
                                                                                   'during '
                                                                                   'retrieval',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'exception '
                                                                                    'message '
                                                                                    'for '
                                                                                    'details '
                                                                                    'and '
                                                                                    'resolve '
                                                                                    'the '
                                                                                    'underlying '
                                                                                    'issue '
                                                                                    '(e.g., '
                                                                                    'network '
                                                                                    'connectivity, '
                                                                                    'API '
                                                                                    'errors)',
                                                                      'source': 'return '
                                                                                'f"Error '
                                                                                'retrieving '
                                                                                'FDA '
                                                                                'drug '
                                                                                'label '
                                                                                'for '
                                                                                '{drug_name}: '
                                                                                '{str(e)}"'}]},
                          'return_schema': {   'description': 'Formatted '
                                                              'string with '
                                                              'drug label '
                                                              'information',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'pharmacology'}}},
{   'description': 'Check for FDA drug recalls and enforcement actions from '
                   'the OpenFDA database to identify safety concerns and '
                   'regulatory actions.',
    'name': 'check_fda_drug_recalls',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Optional filter by recall '
                                                  "class ['Class I', 'Class "
                                                  "II', 'Class III']",
                                   'name': 'classification',
                                   'type': 'List[str]'},
                               {   'default': None,
                                   'description': 'Optional date range for '
                                                  'recalls as (start_date, '
                                                  'end_date)',
                                   'name': 'date_range',
                                   'type': 'Tuple[str, str]'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Name of the drug to check '
                                                  'for recalls',
                                   'name': 'drug_name',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Formatted '
                                                              'string with '
                                                              'recall '
                                                              'information',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'pharmacology'}}},
{   'description': 'Analyze safety signals across multiple drugs using OpenFDA '
                   'adverse event data to identify patterns and comparative '
                   'risk profiles.',
    'name': 'analyze_fda_safety_signals',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Optional comparison time '
                                                  'period as (start_date, '
                                                  'end_date)',
                                   'name': 'comparison_period',
                                   'type': 'Tuple[str, str]'},
                               {   'default': 2.0,
                                   'description': 'Threshold for signal '
                                                  'detection',
                                   'name': 'signal_threshold',
                                   'type': 'float'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'List of drug names to '
                                                  'analyze for safety signals',
                                   'name': 'drug_list',
                                   'type': 'List[str]'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Formatted '
                                                              'string with '
                                                              'safety signal '
                                                              'analysis',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'pharmacology'}}}
]
