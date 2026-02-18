description = [
{   'description': 'Test a PyLabRobot script based on the script content.',
    'name': 'test_pylabrobot_script',
    'optional_parameters': [   {   'default': False,
                                   'description': 'If True, enable tracking of '
                                                  'the script execution',
                                   'name': 'enable_tracking',
                                   'type': 'bool'},
                               {   'default': 60,
                                   'description': 'Timeout in seconds for the '
                                                  'script execution',
                                   'name': 'timeout_seconds',
                                   'type': 'int'},
                               {   'default': False,
                                   'description': 'If True, save the test '
                                                  'results as a .json file',
                                   'name': 'save_test_report',
                                   'type': 'bool'},
                               {   'default': None,
                                   'description': 'Directory to save the test '
                                                  'results. If provided, the '
                                                  'test results will be saved '
                                                  'as a .json file in this '
                                                  'directory',
                                   'name': 'test_report_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Script content to test',
                                   'name': 'script_input',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing:\n'
                                                              '        - '
                                                              'success (bool): '
                                                              'Whether the '
                                                              'script passed '
                                                              'all tests\n'
                                                              '        - '
                                                              'test_results '
                                                              '(dict): '
                                                              'Detailed test '
                                                              'results for '
                                                              'each validation '
                                                              'step\n'
                                                              '        - '
                                                              'execution_summary '
                                                              '(dict): Summary '
                                                              'of operations '
                                                              'performed\n'
                                                              '        - '
                                                              'errors (list): '
                                                              'List of errors '
                                                              'encountered\n'
                                                              '        - '
                                                              'warnings '
                                                              '(list): List of '
                                                              'warnings\n'
                                                              '        - '
                                                              'test_report_path '
                                                              '(str): Path to '
                                                              'saved report if '
                                                              'requested',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'simulation',
                                           'domain': 'lab_automation'}}},
{   'description': 'Get the documentation for the liquid handling section of '
                   'the PyLabRobot tutorial.',
    'name': 'get_pylabrobot_documentation_liquid',
    'optional_parameters': [],
    'required_parameters': [],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Documentation '
                                                              'for a specific '
                                                              'section of the '
                                                              'PyLabRobot '
                                                              'tutorial.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'lab_automation'}}},
{   'description': 'Get the documentation for the material handling section of '
                   'the PyLabRobot tutorial.',
    'name': 'get_pylabrobot_documentation_material',
    'optional_parameters': [],
    'required_parameters': [],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'The content of '
                                                              'the pylabrobot '
                                                              'tutorial '
                                                              'material.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'lab_automation'}}}
]
