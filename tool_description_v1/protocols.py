description = [
{   'description': 'Search protocols.io for public protocols matching a '
                   'keyword.',
    'name': 'search_protocols',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'Most important keyword or '
                                                  'phrase to search (title, '
                                                  'description, authors)',
                                   'name': 'query',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'API '
                                                                                   'request '
                                                                                   'fails',
                                                                      'resolution': 'N/A',
                                                                      'source': 'requests.RequestException: '
                                                                                'If '
                                                                                'API '
                                                                                'request '
                                                                                'fails'},
                                                                  {   'condition': 'Invalid '
                                                                                   'parameters '
                                                                                   'are '
                                                                                   'provided',
                                                                      'resolution': 'N/A',
                                                                      'source': 'ValueError: '
                                                                                'If '
                                                                                'invalid '
                                                                                'parameters '
                                                                                'are '
                                                                                'provided'}]},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing:\n'
                                                              '        - '
                                                              'protocols: List '
                                                              'of protocol '
                                                              'dictionaries '
                                                              'with title, '
                                                              'description, '
                                                              'url, etc.\n'
                                                              '        - '
                                                              'pagination: '
                                                              'Pagination '
                                                              'information\n'
                                                              '        - '
                                                              'total_results: '
                                                              'Total number of '
                                                              'matching '
                                                              'protocols\n'
                                                              '        - '
                                                              'status_code: '
                                                              'API status code '
                                                              '(0 = success)',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'protocols'}}},
{   'description': 'Retrieve detailed metadata for a specific protocols.io '
                   'protocol by ID.',
    'name': 'get_protocol_details',
    'optional_parameters': [   {   'default': 30,
                                   'description': 'Request timeout in seconds',
                                   'name': 'timeout',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Numeric protocol ID from '
                                                  'protocols.io',
                                   'name': 'protocol_id',
                                   'type': 'int'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'API '
                                                                                   'request '
                                                                                   'fails',
                                                                      'resolution': 'Check '
                                                                                    'network '
                                                                                    'connection, '
                                                                                    'API '
                                                                                    'availability, '
                                                                                    'and '
                                                                                    'provided '
                                                                                    'protocol '
                                                                                    'ID.',
                                                                      'source': 'raise '
                                                                                'requests.RequestException(f"Failed '
                                                                                'to '
                                                                                'get '
                                                                                'protocol '
                                                                                'details: '
                                                                                '{str(e)}") '
                                                                                'from '
                                                                                'e'},
                                                                  {   'condition': 'Protocols.io '
                                                                                   'access '
                                                                                   'token '
                                                                                   'is '
                                                                                   'not '
                                                                                   'configured',
                                                                      'resolution': 'Set '
                                                                                    'the '
                                                                                    'Protocols.io '
                                                                                    'access '
                                                                                    'token '
                                                                                    'in '
                                                                                    'the '
                                                                                    'environment '
                                                                                    'variable '
                                                                                    'or '
                                                                                    'BiomniConfig.',
                                                                      'source': 'raise '
                                                                                'ValueError(\n'
                                                                                '            '
                                                                                '"Protocols.io '
                                                                                'access '
                                                                                'token '
                                                                                'is '
                                                                                'not '
                                                                                'configured. '
                                                                                'Set '
                                                                                'PROTOCOLS_IO_ACCESS_TOKEN '
                                                                                'or '
                                                                                'BIOMNI_PROTOCOLS_IO_ACCESS_TOKEN '
                                                                                'env '
                                                                                'var, '
                                                                                'or '
                                                                                'configure '
                                                                                'BiomniConfig.protocols_io_access_token."\n'
                                                                                '        '
                                                                                ')'},
                                                                  {   'condition': 'API '
                                                                                   'returns '
                                                                                   'an '
                                                                                   'error',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'status_code '
                                                                                    'and '
                                                                                    'error_message '
                                                                                    'in '
                                                                                    'the '
                                                                                    'returned '
                                                                                    'dictionary.',
                                                                      'source': 'return '
                                                                                '{"error": '
                                                                                'data.get("error_message", '
                                                                                '"Unknown '
                                                                                'error"), '
                                                                                '"status_code": '
                                                                                'data.get("status_code")}'}]},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing '
                                                              'detailed '
                                                              'protocol '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'protocols'}}},
{   'description': 'List available protocol files in the local '
                   'biomni/tool/protocols/ directory. Includes protocols from '
                   'Addgene and Thermo Fisher Scientific.',
    'name': 'list_local_protocols',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Filter by source directory '
                                                  "(e.g., 'addgene' or "
                                                  "'thermofisher'). If None, "
                                                  'lists all protocols.',
                                   'name': 'source',
                                   'type': 'str'}],
    'required_parameters': [],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Protocols '
                                                                                   'directory '
                                                                                   'does '
                                                                                   'not '
                                                                                   'exist',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'protocols '
                                                                                    'directory '
                                                                                    'exists.',
                                                                      'source': 'return '
                                                                                '{\n'
                                                                                '            '
                                                                                '"protocols": '
                                                                                '[],\n'
                                                                                '            '
                                                                                '"total_count": '
                                                                                '0,\n'
                                                                                '            '
                                                                                '"sources": '
                                                                                '[],\n'
                                                                                '            '
                                                                                '"error": '
                                                                                'f"Protocols '
                                                                                'directory '
                                                                                'not '
                                                                                'found: '
                                                                                '{protocols_dir}",\n'
                                                                                '        '
                                                                                '}'}]},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing:\n'
                                                              '        - '
                                                              'protocols: List '
                                                              'of protocol '
                                                              'file '
                                                              'information '
                                                              'with name, '
                                                              'source, and '
                                                              'path\n'
                                                              '        - '
                                                              'total_count: '
                                                              'Total number of '
                                                              'protocols '
                                                              'found\n'
                                                              '        - '
                                                              'sources: List '
                                                              'of available '
                                                              'source '
                                                              'directories',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'protocols'}}},
{   'description': 'Read the contents of a local protocol file from '
                   'biomni/tool/protocols/. Use list_local_protocols() first '
                   'to find available protocol filenames.',
    'name': 'read_local_protocol',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Source directory (e.g., '
                                                  "'addgene' or "
                                                  "'thermofisher'). If None, "
                                                  'searches all sources.',
                                   'name': 'source',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Name of the protocol file '
                                                  "(e.g., 'Addgene_ Protocol - "
                                                  'How to Run an Agarose '
                                                  "Gel.txt')",
                                   'name': 'filename',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Filename '
                                                                                   'is '
                                                                                   'empty',
                                                                      'resolution': 'Provide '
                                                                                    'a '
                                                                                    'valid '
                                                                                    'filename.',
                                                                      'source': 'raise '
                                                                                'ValueError("Filename '
                                                                                'cannot '
                                                                                'be '
                                                                                'empty")'},
                                                                  {   'condition': 'Protocols '
                                                                                   'directory '
                                                                                   'not '
                                                                                   'found',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'protocols '
                                                                                    'directory '
                                                                                    'exists '
                                                                                    'and '
                                                                                    'is '
                                                                                    'accessible.',
                                                                      'source': 'raise '
                                                                                'FileNotFoundError(f"Protocols '
                                                                                'directory '
                                                                                'not '
                                                                                'found: '
                                                                                '{protocols_dir}")'},
                                                                  {   'condition': 'Protocol '
                                                                                   'file '
                                                                                   'not '
                                                                                   'found '
                                                                                   'in '
                                                                                   'a '
                                                                                   'specific '
                                                                                   'source '
                                                                                   'directory',
                                                                      'resolution': 'Verify '
                                                                                    'the '
                                                                                    'filename '
                                                                                    'and '
                                                                                    'source '
                                                                                    'directory '
                                                                                    'are '
                                                                                    'correct.',
                                                                      'source': 'raise '
                                                                                'FileNotFoundError(f"Protocol '
                                                                                'file '
                                                                                'not '
                                                                                'found: '
                                                                                '{source}/{filename}")'},
                                                                  {   'condition': 'Protocol '
                                                                                   'file '
                                                                                   'not '
                                                                                   'found '
                                                                                   'in '
                                                                                   'any '
                                                                                   'source '
                                                                                   'directory',
                                                                      'resolution': 'Verify '
                                                                                    'the '
                                                                                    'filename '
                                                                                    'and '
                                                                                    'that '
                                                                                    'the '
                                                                                    'file '
                                                                                    'exists '
                                                                                    'in '
                                                                                    'one '
                                                                                    'of '
                                                                                    'the '
                                                                                    'source '
                                                                                    'directories.',
                                                                      'source': 'raise '
                                                                                'FileNotFoundError(f"Protocol '
                                                                                'file '
                                                                                'not '
                                                                                'found '
                                                                                'in '
                                                                                'any '
                                                                                'source '
                                                                                'directory: '
                                                                                '{filename}")'}]},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing:\n'
                                                              '        - '
                                                              'content: Full '
                                                              'text content of '
                                                              'the protocol '
                                                              'file\n'
                                                              '        - '
                                                              'filename: Name '
                                                              'of the file\n'
                                                              '        - '
                                                              'source: Source '
                                                              'directory where '
                                                              'the file was '
                                                              'found\n'
                                                              '        - path: '
                                                              'Full path to '
                                                              'the file',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'protocols'}}}
]
