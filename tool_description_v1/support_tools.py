description = [
{   'description': 'Executes the provided Python command in the notebook '
                   'environment and returns the output.',
    'name': 'run_python_repl',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'Python command to execute '
                                                  'in the notebook environment',
                                   'name': 'command',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'An '
                                                                                   'exception '
                                                                                   'occurs '
                                                                                   'during '
                                                                                   'the '
                                                                                   'execution '
                                                                                   'of '
                                                                                   'the '
                                                                                   'Python '
                                                                                   'command.',
                                                                      'resolution': 'Inspect '
                                                                                    'the '
                                                                                    'error '
                                                                                    'message '
                                                                                    'to '
                                                                                    'identify '
                                                                                    'and '
                                                                                    'correct '
                                                                                    'the '
                                                                                    'issue '
                                                                                    'in '
                                                                                    'the '
                                                                                    'Python '
                                                                                    'command.',
                                                                      'source': 'output '
                                                                                '= '
                                                                                'f"Error: '
                                                                                '{str(e)}"'}]},
                          'return_schema': {   'description': 'The output of '
                                                              'the executed '
                                                              'Python command.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'general',
                                           'domain': 'support_tools'}}},
{   'description': 'Read the source code of a function from any module path.',
    'name': 'read_function_source_code',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'Fully qualified function '
                                                  'name (e.g., '
                                                  "'bioagentos.tool.support_tools.write_python_code')",
                                   'name': 'function_name',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'ImportError '
                                                                                   'or '
                                                                                   'AttributeError '
                                                                                   'occurs',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'module '
                                                                                    'path '
                                                                                    'and '
                                                                                    'function '
                                                                                    'name '
                                                                                    'are '
                                                                                    'correct '
                                                                                    'and '
                                                                                    'that '
                                                                                    'the '
                                                                                    'module '
                                                                                    'is '
                                                                                    'installed.',
                                                                      'source': 'return '
                                                                                'f"Error: '
                                                                                'Could '
                                                                                'not '
                                                                                'find '
                                                                                'function '
                                                                                "'{function_name}'. "
                                                                                'Details: '
                                                                                '{str(e)}"'}]},
                          'return_schema': {   'description': 'The source code '
                                                              'of the function',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'general',
                                           'domain': 'support_tools'}}},
{   'description': 'Download data from Synapse using entity IDs. Requires '
                   'SYNAPSE_AUTH_TOKEN environment variable for '
                   'authentication. CRITICAL: Always specify entity_type '
                   "parameter based on what you're downloading (file, dataset, "
                   "folder, project). Check user hints like 'files' or search "
                   'results to determine correct type. Multiple IDs only work '
                   "with entity_type='file'. Recursive only works with "
                   "entity_type='folder'.",
    'name': 'download_synapse_data',
    'optional_parameters': [   {   'default': '.',
                                   'description': 'Directory where files will '
                                                  'be downloaded',
                                   'name': 'download_location',
                                   'type': 'str'},
                               {   'default': False,
                                   'description': 'Whether to follow links to '
                                                  'download the linked entity',
                                   'name': 'follow_link',
                                   'type': 'bool'},
                               {   'default': False,
                                   'description': 'Whether to recursively '
                                                  'download folders and their '
                                                  'contents. ONLY valid with '
                                                  "entity_type='folder'",
                                   'name': 'recursive',
                                   'type': 'bool'},
                               {   'default': 300,
                                   'description': 'Timeout in seconds for each '
                                                  'download operation',
                                   'name': 'timeout',
                                   'type': 'int'},
                               {   'default': 'dataset',
                                   'description': 'Type of Synapse entity: '
                                                  "'file', 'dataset', "
                                                  "'folder', or 'project'. "
                                                  'MUST match actual entity '
                                                  'type! Check user hints '
                                                  "(e.g., 'files' means "
                                                  "entity_type='file') or "
                                                  "search results ('node_type' "
                                                  "field). Default 'dataset' "
                                                  'should only be used for '
                                                  'actual datasets.',
                                   'name': 'entity_type',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Synapse entity ID(s) to '
                                                  'download. For files: single '
                                                  'ID or list of IDs. For '
                                                  'datasets/folders/projects: '
                                                  'single ID only',
                                   'name': 'entity_ids',
                                   'type': 'str|list[str]'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing '
                                                              'download '
                                                              'results and any '
                                                              'errors',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'support_tools'}}}
]
