description = [
{   'description': 'Predicts intrinsically disordered regions (IDRs) in a '
                   'protein sequence using IUPred2A.',
    'name': 'predict_protein_disorder_regions',
    'optional_parameters': [   {   'default': 0.5,
                                   'description': 'The disorder score '
                                                  'threshold above which a '
                                                  'residue is considered '
                                                  'disordered',
                                   'name': 'threshold',
                                   'type': 'float'},
                               {   'default': 'disorder_prediction_results.csv',
                                   'description': 'Filename to save the '
                                                  'per-residue disorder scores',
                                   'name': 'output_file',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'The amino acid sequence of '
                                                  'the protein to analyze',
                                   'name': 'protein_sequence',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Error '
                                                                                   'accessing '
                                                                                   'IUPred2A '
                                                                                   'server',
                                                                      'resolution': 'Check '
                                                                                    'network '
                                                                                    'connection '
                                                                                    'and '
                                                                                    'server '
                                                                                    'availability.',
                                                                      'source': 'return '
                                                                                'f"Error '
                                                                                'accessing '
                                                                                'IUPred2A '
                                                                                'server: '
                                                                                '{str(e)}"'},
                                                                  {   'condition': 'No '
                                                                                   'valid '
                                                                                   'prediction '
                                                                                   'data '
                                                                                   'was '
                                                                                   'returned '
                                                                                   'from '
                                                                                   'the '
                                                                                   'server.',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'input '
                                                                                    'sequence '
                                                                                    'and '
                                                                                    'server '
                                                                                    'response.',
                                                                      'source': 'return '
                                                                                '"No '
                                                                                'valid '
                                                                                'prediction '
                                                                                'data '
                                                                                'was '
                                                                                'returned '
                                                                                'from '
                                                                                'the '
                                                                                'server."'}]},
                          'return_schema': {   'description': 'A research log '
                                                              'summarizing the '
                                                              'prediction '
                                                              'process and '
                                                              'results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'biophysics'}}},
{   'description': 'Quantifies cell morphology and cytoskeletal organization '
                   'from fluorescence microscopy images.',
    'name': 'analyze_cell_morphology_and_cytoskeleton',
    'optional_parameters': [   {   'default': './results',
                                   'description': 'Directory to save output '
                                                  'files',
                                   'name': 'output_dir',
                                   'type': 'str'},
                               {   'default': 'otsu',
                                   'description': 'Method for cell '
                                                  "segmentation ('otsu', "
                                                  "'adaptive', or 'manual')",
                                   'name': 'threshold_method',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Path to the fluorescence '
                                                  'microscopy image file',
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
                                                                                    'image '
                                                                                    'file '
                                                                                    'is '
                                                                                    'valid.',
                                                                      'source': 'return '
                                                                                'f"Error '
                                                                                'loading '
                                                                                'image: '
                                                                                '{str(e)}"'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'biophysics'}}},
{   'description': 'Quantify tissue deformation and flow dynamics from '
                   'microscopy image sequence.',
    'name': 'analyze_tissue_deformation_flow',
    'optional_parameters': [   {   'default': 'results',
                                   'description': 'Directory to save results',
                                   'name': 'output_dir',
                                   'type': 'str'},
                               {   'default': 1.0,
                                   'description': 'Physical scale of pixels '
                                                  '(e.g., μm/pixel) for proper '
                                                  'scaling of metrics',
                                   'name': 'pixel_scale',
                                   'type': 'float'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Sequence of microscopy '
                                                  'images (either a list of '
                                                  'file paths or a 3D numpy '
                                                  'array [time, height, '
                                                  'width])',
                                   'name': 'image_sequence',
                                   'type': 'list or numpy.ndarray'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Could '
                                                                                   'not '
                                                                                   'load '
                                                                                   'an '
                                                                                   'image '
                                                                                   'file',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'image '
                                                                                    'file '
                                                                                    'path '
                                                                                    'is '
                                                                                    'correct '
                                                                                    'and '
                                                                                    'the '
                                                                                    'image '
                                                                                    'file '
                                                                                    'is '
                                                                                    'valid.',
                                                                      'source': 'return '
                                                                                'f"Error: '
                                                                                'Could '
                                                                                'not '
                                                                                'load '
                                                                                'image '
                                                                                '{img_path}"'}]},
                          'return_schema': {   'description': 'Research log '
                                                              'summarizing the '
                                                              'analysis steps '
                                                              'and results',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'biophysics'}}}
]
