description = [
{   'description': 'Scan a protein sequence for canonical N-glycosylation '
                   'sequons (N-X-[S/T], X≠P). Returns positions and motifs.',
    'name': 'find_n_glycosylation_motifs',
    'optional_parameters': [   {   'default': False,
                                   'description': 'Allow overlapping motif '
                                                  'detections',
                                   'name': 'allow_overlap',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Protein sequence '
                                                  '(one-letter AA codes)',
                                   'name': 'sequence',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'string '
                                                              'summarizing '
                                                              'motif locations '
                                                              'and counts',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'glycoengineering'}}},
{   'description': 'Heuristic O-glycosite hotspot prediction using local S/T '
                   'density (lightweight baseline; see NetOGlyc 4.0 for SOTA).',
    'name': 'predict_o_glycosylation_hotspots',
    'optional_parameters': [   {   'default': 7,
                                   'description': 'Odd-sized window for local '
                                                  'density (>=3)',
                                   'name': 'window',
                                   'type': 'int'},
                               {   'default': 0.4,
                                   'description': 'Min S/T fraction in window '
                                                  'to flag site',
                                   'name': 'min_st_fraction',
                                   'type': 'float'},
                               {   'default': True,
                                   'description': 'Avoid S/T immediately '
                                                  'followed by Proline',
                                   'name': 'disallow_proline_next',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Protein sequence '
                                                  '(one-letter AA codes)',
                                   'name': 'sequence',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Research log '
                                                              'string with '
                                                              'candidate sites '
                                                              'and scores',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'glycoengineering'}}},
{   'description': 'Curated list of external glycoengineering tools and '
                   'resources (links and notes) as referenced in issue #198.',
    'name': 'list_glycoengineering_resources',
    'optional_parameters': [],
    'required_parameters': [],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Returns a '
                                                              'research-log '
                                                              'style summary '
                                                              'with URLs for '
                                                              'further use.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'general',
                                           'domain': 'glycoengineering'}}}
]
