description = [
{   'description': 'Analyzes circular dichroism (CD) spectroscopy data to '
                   'determine secondary structure and thermal stability.',
    'name': 'analyze_circular_dichroism_spectra',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Temperature values (°C) for '
                                                  'thermal denaturation '
                                                  'experiment',
                                   'name': 'temperature_data',
                                   'type': 'list or numpy.ndarray'},
                               {   'default': None,
                                   'description': 'CD signal values at '
                                                  'specific wavelength across '
                                                  'different temperatures',
                                   'name': 'thermal_cd_data',
                                   'type': 'list or numpy.ndarray'},
                               {   'default': './',
                                   'description': 'Directory to save result '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Name of the biomolecule '
                                                  'sample (e.g., "Znf706", '
                                                  '"G-quadruplex")',
                                   'name': 'sample_name',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Type of biomolecule '
                                                  '("protein" or '
                                                  '"nucleic_acid")',
                                   'name': 'sample_type',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Wavelength values in nm for '
                                                  'CD spectrum',
                                   'name': 'wavelength_data',
                                   'type': 'list or numpy.ndarray'},
                               {   'default': None,
                                   'description': 'CD signal intensity values '
                                                  '(typically in mdeg or Δε)',
                                   'name': 'cd_signal_data',
                                   'type': 'list or numpy.ndarray'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'CD analysis '
                                                              'steps and '
                                                              'results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'biochemistry'}}},
{   'description': 'Calculate numeric values for various structural features '
                   'of an RNA secondary structure.',
    'name': 'analyze_rna_secondary_structure_features',
    'optional_parameters': [   {   'default': None,
                                   'description': 'The RNA sequence '
                                                  'corresponding to the '
                                                  'structure. If provided, '
                                                  'sequence-dependent energy '
                                                  'calculations will be '
                                                  'performed.',
                                   'name': 'sequence',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'RNA secondary structure in '
                                                  'dot-bracket notation (e.g., '
                                                  '"(((...)))"). Parentheses '
                                                  'represent base pairs, dots '
                                                  'represent unpaired bases.',
                                   'name': 'dot_bracket_structure',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Invalid '
                                                                                   'dot-bracket '
                                                                                   'notation',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'input '
                                                                                    'dot-bracket '
                                                                                    'structure '
                                                                                    'only '
                                                                                    'contains '
                                                                                    'valid '
                                                                                    'characters.',
                                                                      'source': 'return '
                                                                                '"Error: '
                                                                                'Invalid '
                                                                                'dot-bracket '
                                                                                'notation. '
                                                                                'Use '
                                                                                'only '
                                                                                "'()', "
                                                                                "'[]', "
                                                                                "'{}', "
                                                                                'and '
                                                                                '\'.\'"'},
                                                                  {   'condition': 'Sequence '
                                                                                   'and '
                                                                                   'structure '
                                                                                   'lengths '
                                                                                   'do '
                                                                                   'not '
                                                                                   'match.',
                                                                      'resolution': 'Provide '
                                                                                    'a '
                                                                                    'sequence '
                                                                                    'with '
                                                                                    'the '
                                                                                    'same '
                                                                                    'length '
                                                                                    'as '
                                                                                    'the '
                                                                                    'dot-bracket '
                                                                                    'structure.',
                                                                      'source': 'return '
                                                                                '"Error: '
                                                                                'Sequence '
                                                                                'and '
                                                                                'structure '
                                                                                'lengths '
                                                                                'do '
                                                                                'not '
                                                                                'match."'},
                                                                  {   'condition': 'Unbalanced '
                                                                                   'structure '
                                                                                   '(more '
                                                                                   'closing '
                                                                                   'than '
                                                                                   'opening '
                                                                                   'brackets).',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'dot-bracket '
                                                                                    'structure '
                                                                                    'has '
                                                                                    'a '
                                                                                    'balanced '
                                                                                    'number '
                                                                                    'of '
                                                                                    'opening '
                                                                                    'and '
                                                                                    'closing '
                                                                                    'brackets.',
                                                                      'source': 'return '
                                                                                '"Error: '
                                                                                'Unbalanced '
                                                                                'structure. '
                                                                                'More '
                                                                                'closing '
                                                                                'than '
                                                                                'opening '
                                                                                'brackets."'},
                                                                  {   'condition': 'Mismatched '
                                                                                   'bracket '
                                                                                   'types.',
                                                                      'resolution': 'Ensure '
                                                                                    'that '
                                                                                    'opening '
                                                                                    'and '
                                                                                    'closing '
                                                                                    'brackets '
                                                                                    'match '
                                                                                    '(e.g., '
                                                                                    "'(' "
                                                                                    'with '
                                                                                    "')').",
                                                                      'source': 'return '
                                                                                '"Error: '
                                                                                'Mismatched '
                                                                                'bracket '
                                                                                'types. '
                                                                                'Opening '
                                                                                'and '
                                                                                'closing '
                                                                                'brackets '
                                                                                'must '
                                                                                'match."'},
                                                                  {   'condition': 'Unbalanced '
                                                                                   'structure '
                                                                                   '(more '
                                                                                   'opening '
                                                                                   'than '
                                                                                   'closing '
                                                                                   'brackets).',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'dot-bracket '
                                                                                    'structure '
                                                                                    'has '
                                                                                    'a '
                                                                                    'balanced '
                                                                                    'number '
                                                                                    'of '
                                                                                    'opening '
                                                                                    'and '
                                                                                    'closing '
                                                                                    'brackets.',
                                                                      'source': 'return '
                                                                                '"Error: '
                                                                                'Unbalanced '
                                                                                'structure. '
                                                                                'More '
                                                                                'opening '
                                                                                'than '
                                                                                'closing '
                                                                                'brackets."'}]},
                          'return_schema': {   'description': 'A research log '
                                                              'summarizing the '
                                                              'calculated '
                                                              'structural '
                                                              'features and '
                                                              'analysis steps.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'biochemistry'}}},
{   'description': 'Analyze protease kinetics data from fluorogenic peptide '
                   'cleavage assays, fit the data to Michaelis-Menten '
                   'kinetics, and determine key kinetic parameters.',
    'name': 'analyze_protease_kinetics',
    'optional_parameters': [   {   'default': 'protease_kinetics',
                                   'description': 'Prefix for output files',
                                   'name': 'output_prefix',
                                   'type': 'str'},
                               {   'default': './',
                                   'description': 'Directory to save output '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Array of time points (in '
                                                  'seconds) at which '
                                                  'measurements were taken',
                                   'name': 'time_points',
                                   'type': 'numpy.ndarray'},
                               {   'default': None,
                                   'description': '2D array of fluorescence '
                                                  'measurements where each row '
                                                  'corresponds to a different '
                                                  'substrate concentration and '
                                                  'each column corresponds to '
                                                  'a time point',
                                   'name': 'fluorescence_data',
                                   'type': 'numpy.ndarray'},
                               {   'default': None,
                                   'description': 'Array of substrate '
                                                  'concentrations (in μM) '
                                                  'corresponding to each row '
                                                  'in fluorescence_data',
                                   'name': 'substrate_concentrations',
                                   'type': 'numpy.ndarray'},
                               {   'default': None,
                                   'description': 'Concentration of the '
                                                  'protease enzyme (in μM)',
                                   'name': 'enzyme_concentration',
                                   'type': 'float'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'A research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'biochemistry'}}},
{   'description': 'Performs in vitro enzyme kinetics assay and analyzes the '
                   'dose-dependent effects of modulators.',
    'name': 'analyze_enzyme_kinetics_assay',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Dictionary of modulators '
                                                  'where keys are modulator '
                                                  'names and values are lists '
                                                  'of concentrations in μM',
                                   'name': 'modulators',
                                   'type': 'dict'},
                               {   'default': None,
                                   'description': 'Time points in minutes for '
                                                  'time-course measurements',
                                   'name': 'time_points',
                                   'type': 'list or numpy.ndarray'},
                               {   'default': './',
                                   'description': 'Directory to save output '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Name of the purified enzyme '
                                                  'being tested',
                                   'name': 'enzyme_name',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'List of substrate '
                                                  'concentrations in μM for '
                                                  'kinetic analysis',
                                   'name': 'substrate_concentrations',
                                   'type': 'list or numpy.ndarray'},
                               {   'default': None,
                                   'description': 'Concentration of the enzyme '
                                                  'in nM',
                                   'name': 'enzyme_concentration',
                                   'type': 'float'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'enzyme kinetics '
                                                              'assay procedure '
                                                              'and results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'biochemistry'}}},
{   'description': 'Analyzes isothermal titration calorimetry (ITC) data to '
                   'determine binding affinity and thermodynamic parameters.',
    'name': 'analyze_itc_binding_thermodynamics',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Path to CSV or TSV file '
                                                  'containing ITC thermogram '
                                                  'data with columns for '
                                                  'injection number, injection '
                                                  'volume, and heat '
                                                  'released/absorbed.',
                                   'name': 'itc_data_path',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Raw ITC thermogram data as '
                                                  'a numpy array with shape '
                                                  '(n_injections, 3) '
                                                  'containing injection '
                                                  'number, injection volume, '
                                                  'and heat.',
                                   'name': 'itc_data',
                                   'type': 'numpy.ndarray'},
                               {   'default': 298.15,
                                   'description': 'Temperature in Kelvin at '
                                                  'which the experiment was '
                                                  'conducted.',
                                   'name': 'temperature',
                                   'type': 'float'},
                               {   'default': None,
                                   'description': 'Initial concentration of '
                                                  'protein in the cell in '
                                                  'molar (M).',
                                   'name': 'protein_concentration',
                                   'type': 'float'},
                               {   'default': None,
                                   'description': 'Concentration of ligand in '
                                                  'the syringe in molar (M).',
                                   'name': 'ligand_concentration',
                                   'type': 'float'}],
    'required_parameters': [],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'A research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results, '
                                                              'including '
                                                              'binding '
                                                              'affinity (Kd), '
                                                              'binding '
                                                              'enthalpy (ΔH), '
                                                              'binding entropy '
                                                              '(ΔS), and Gibbs '
                                                              'free energy '
                                                              '(ΔG).',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'biochemistry'}}},
{   'description': 'Perform multiple sequence alignment and phylogenetic '
                   'analysis to identify conserved protein regions.',
    'name': 'analyze_protein_conservation',
    'optional_parameters': [   {   'default': './',
                                   'description': 'Directory to save output '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'List of protein sequences '
                                                  'in FASTA format from '
                                                  'multiple organisms.',
                                   'name': 'protein_sequences',
                                   'type': 'list of str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'MUSCLE '
                                                                                   'alignment '
                                                                                   'fails',
                                                                      'resolution': 'Use '
                                                                                    "Biopython's "
                                                                                    'built-in '
                                                                                    'alignment '
                                                                                    'methods '
                                                                                    'as '
                                                                                    'a '
                                                                                    'fallback.',
                                                                      'source': 'str(e)'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results, '
                                                              'including '
                                                              'filenames of '
                                                              'saved outputs.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'biochemistry'}}}
]
