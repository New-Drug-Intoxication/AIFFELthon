description = [
{   'description': 'Query the UniProt REST API using either natural language '
                   'or a direct endpoint.',
    'name': 'query_uniprot',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Full or partial UniProt API '
                                                  'endpoint URL to query '
                                                  'directly (e.g., '
                                                  "'https://rest.uniprot.org/uniprotkb/P01308')",
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': 5,
                                   'description': 'Maximum number of results '
                                                  'to return',
                                   'name': 'max_results',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about proteins (e.g., "Find '
                                                  'information about human '
                                                  'insulin")',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query '
                                                              'information and '
                                                              'the UniProt API '
                                                              'results',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the AlphaFold Database API for protein structure '
                   'predictions or metadata; optionally download structures.',
    'name': 'query_alphafold',
    'optional_parameters': [   {   'default': 'prediction',
                                   'description': "Endpoint: 'prediction', "
                                                  "'summary', or 'annotations'",
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Residue range as '
                                                  "'start-end'",
                                   'name': 'residue_range',
                                   'type': 'str'},
                               {   'default': False,
                                   'description': 'Whether to download '
                                                  'structure file',
                                   'name': 'download',
                                   'type': 'bool'},
                               {   'default': None,
                                   'description': 'Directory to save '
                                                  'downloaded files',
                                   'name': 'output_dir',
                                   'type': 'str'},
                               {   'default': 'pdb',
                                   'description': "Download format 'pdb' or "
                                                  "'cif'",
                                   'name': 'file_format',
                                   'type': 'str'},
                               {   'default': 'v4',
                                   'description': 'AlphaFold model version '
                                                  '(e.g., v4)',
                                   'name': 'model_version',
                                   'type': 'str'},
                               {   'default': 1,
                                   'description': 'Model number (1-5)',
                                   'name': 'model_number',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'UniProt accession ID (e.g., '
                                                  "'P12345')",
                                   'name': 'uniprot_id',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing both '
                                                              'the query '
                                                              'information and '
                                                              'the AlphaFold '
                                                              'results',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the InterPro REST API using natural language or a '
                   'direct endpoint.',
    'name': 'query_interpro',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Endpoint path or full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': 3,
                                   'description': 'Max results per page',
                                   'name': 'max_results',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about protein '
                                                  'domains/families',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing both '
                                                              'the query '
                                                              'information and '
                                                              'the InterPro '
                                                              'API results',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the RCSB PDB database using natural language or a '
                   'direct structured query.',
    'name': 'query_pdb',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct RCSB Search API '
                                                  'query JSON',
                                   'name': 'query',
                                   'type': 'dict'},
                               {   'default': 3,
                                   'description': 'Maximum results to return',
                                   'name': 'max_results',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about protein structures',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'structured '
                                                              'query, search '
                                                              'results, and '
                                                              'identifiers',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Retrieve detailed data and/or download files for PDB '
                   'identifiers.',
    'name': 'query_pdb_identifiers',
    'optional_parameters': [   {   'default': 'entry',
                                   'description': "'entry', 'assembly', "
                                                  "'polymer_entity', etc.",
                                   'name': 'return_type',
                                   'type': 'str'},
                               {   'default': False,
                                   'description': 'Download PDB structure '
                                                  'files',
                                   'name': 'download',
                                   'type': 'bool'},
                               {   'default': None,
                                   'description': 'Specific attributes to '
                                                  'retrieve',
                                   'name': 'attributes',
                                   'type': 'List[str]'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'List of PDB identifiers',
                                   'name': 'identifiers',
                                   'type': 'List[str]'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'No '
                                                                                   'identifiers '
                                                                                   'provided',
                                                                      'resolution': 'Provide '
                                                                                    'a '
                                                                                    'list '
                                                                                    'of '
                                                                                    'PDB '
                                                                                    'identifiers.',
                                                                      'source': 'return '
                                                                                '{"error": '
                                                                                '"No '
                                                                                'identifiers '
                                                                                'provided"}'},
                                                                  {   'condition': 'Error '
                                                                                   'retrieving '
                                                                                   'PDB '
                                                                                   'details',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'error '
                                                                                    'message '
                                                                                    'for '
                                                                                    'details '
                                                                                    'and '
                                                                                    'address '
                                                                                    'the '
                                                                                    'underlying '
                                                                                    'issue '
                                                                                    '(e.g., '
                                                                                    'network '
                                                                                    'connectivity, '
                                                                                    'invalid '
                                                                                    'identifier).',
                                                                      'source': 'return '
                                                                                '{"error": '
                                                                                'f"Error '
                                                                                'retrieving '
                                                                                'PDB '
                                                                                'details: '
                                                                                '{str(e)}"}'}]},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'detailed data '
                                                              'and file paths '
                                                              'if downloaded',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Take a natural language prompt and convert it to a '
                   'structured KEGG API query.',
    'name': 'query_kegg',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct KEGG endpoint to '
                                                  'query',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about KEGG data',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Failed '
                                                                                   'to '
                                                                                   'generate '
                                                                                   'a '
                                                                                   'valid '
                                                                                   'endpoint '
                                                                                   'from '
                                                                                   'the '
                                                                                   'prompt',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'prompt '
                                                                                    'is '
                                                                                    'clear '
                                                                                    'and '
                                                                                    'relevant '
                                                                                    'to '
                                                                                    'KEGG '
                                                                                    'data. '
                                                                                    'Check '
                                                                                    'the '
                                                                                    'LLM '
                                                                                    'response '
                                                                                    'for '
                                                                                    'any '
                                                                                    'clues '
                                                                                    'about '
                                                                                    'the '
                                                                                    'failure.',
                                                                      'source': 'return '
                                                                                '{"error": '
                                                                                '"Failed '
                                                                                'to '
                                                                                'generate '
                                                                                'a '
                                                                                'valid '
                                                                                'endpoint '
                                                                                'from '
                                                                                'the '
                                                                                'prompt", '
                                                                                '"llm_response": '
                                                                                'llm_result.get("raw_response", '
                                                                                '"No '
                                                                                'response")}'},
                                                                  {   'condition': 'Either '
                                                                                   'a '
                                                                                   'prompt '
                                                                                   'or '
                                                                                   'an '
                                                                                   'endpoint '
                                                                                   'must '
                                                                                   'be '
                                                                                   'provided',
                                                                      'resolution': 'Provide '
                                                                                    'either '
                                                                                    'a '
                                                                                    'prompt '
                                                                                    'or '
                                                                                    'an '
                                                                                    'endpoint '
                                                                                    'as '
                                                                                    'input.',
                                                                      'source': 'return '
                                                                                '{"error": '
                                                                                '"Either '
                                                                                'a '
                                                                                'prompt '
                                                                                'or '
                                                                                'an '
                                                                                'endpoint '
                                                                                'must '
                                                                                'be '
                                                                                'provided"}'}]},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing both '
                                                              'the structured '
                                                              'query and the '
                                                              'KEGG results',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the STRING protein interaction database using '
                   'natural language or direct endpoint.',
    'name': 'query_stringdb',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Full URL to query directly',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': False,
                                   'description': 'Download image results if '
                                                  'endpoint is image',
                                   'name': 'download_image',
                                   'type': 'bool'},
                               {   'default': None,
                                   'description': 'Directory to save '
                                                  'downloaded files',
                                   'name': 'output_dir',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about protein interactions',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the IUCN Red List API using natural language or a '
                   'direct endpoint.',
    'name': 'query_iucn',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about species conservation '
                                                  'status',
                                   'name': 'prompt',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Endpoint name or full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': '',
                                   'description': 'IUCN API token',
                                   'name': 'token',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the Paleobiology Database (PBDB) API using natural '
                   'language or a direct endpoint.',
    'name': 'query_paleobiology',
    'optional_parameters': [   {   'default': None,
                                   'description': 'API endpoint name or full '
                                                  'URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about fossil records',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the JASPAR REST API for transcription factor binding '
                   'profiles.',
    'name': 'query_jaspar',
    'optional_parameters': [   {   'default': None,
                                   'description': 'API endpoint path or full '
                                                  'URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about TF binding profiles',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the World Register of Marine Species (WoRMS) REST '
                   'API using natural language or a direct endpoint.',
    'name': 'query_worms',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Full URL or endpoint '
                                                  'specification',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about marine species',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the cBioPortal REST API using natural language or a '
                   'direct endpoint.',
    'name': 'query_cbioportal',
    'optional_parameters': [   {   'default': None,
                                   'description': 'API endpoint path or full '
                                                  'URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about cancer genomics',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Convert a natural language prompt into a structured '
                   'ClinVar search query and run it.',
    'name': 'query_clinvar',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct ClinVar search term',
                                   'name': 'search_term',
                                   'type': 'str'},
                               {   'default': 3,
                                   'description': 'Maximum number of results',
                                   'name': 'max_results',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about genetic variants',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing both '
                                                              'the structured '
                                                              'query and the '
                                                              'ClinVar results',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the NCBI GEO database (GDS/GEOPROFILES) using '
                   'natural language or direct search term.',
    'name': 'query_geo',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct GEO search term',
                                   'name': 'search_term',
                                   'type': 'str'},
                               {   'default': 3,
                                   'description': 'Maximum number of results',
                                   'name': 'max_results',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about expression data',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the NCBI dbSNP database using natural language or '
                   'direct search term.',
    'name': 'query_dbsnp',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct dbSNP search term',
                                   'name': 'search_term',
                                   'type': 'str'},
                               {   'default': 3,
                                   'description': 'Maximum number of results',
                                   'name': 'max_results',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about SNPs/variants',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'genetics'}}},
{   'description': 'Query the UCSC Genome Browser API using natural language '
                   'or a direct endpoint.',
    'name': 'query_ucsc',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Full URL or endpoint spec',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about genomic data',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the Ensembl REST API using natural language or a '
                   'direct endpoint.',
    'name': 'query_ensembl',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct Ensembl endpoint or '
                                                  'full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about genomic data',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the OpenTargets Platform API using natural language '
                   'or a direct GraphQL query.',
    'name': 'query_opentarget',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct GraphQL query string',
                                   'name': 'query',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Variables for GraphQL',
                                   'name': 'variables',
                                   'type': 'dict'},
                               {   'default': False,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about targets/diseases',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the Monarch Initiative API using natural language or '
                   'a direct endpoint.',
    'name': 'query_monarch',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct endpoint or full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': 2,
                                   'description': 'Max results (adds limit '
                                                  'param)',
                                   'name': 'max_results',
                                   'type': 'int'},
                               {   'default': False,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about '
                                                  'genes/diseases/phenotypes',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the OpenFDA API using natural language or direct '
                   'parameters.',
    'name': 'query_openfda',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct endpoint or full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': 100,
                                   'description': 'Max results (limit)',
                                   'name': 'max_results',
                                   'type': 'int'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'},
                               {   'default': None,
                                   'description': 'Search parameters mapping',
                                   'name': 'search_params',
                                   'type': 'dict'},
                               {   'default': None,
                                   'description': 'Sort parameters mapping',
                                   'name': 'sort_params',
                                   'type': 'dict'},
                               {   'default': None,
                                   'description': 'Field to count',
                                   'name': 'count_params',
                                   'type': 'str'},
                               {   'default': 0,
                                   'description': 'Skip for pagination',
                                   'name': 'skip_results',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about OpenFDA data',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the GWAS Catalog API using natural language or a '
                   'direct endpoint.',
    'name': 'query_gwas_catalog',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Endpoint name (e.g., '
                                                  "'studies')",
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': 3,
                                   'description': 'Max results per page (size)',
                                   'name': 'max_results',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about GWAS data',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query gnomAD for variants in a gene using natural language '
                   'or direct gene symbol.',
    'name': 'query_gnomad',
    'optional_parameters': [   {   'default': None,
                                   'description': "Gene symbol (e.g., 'BRCA1')",
                                   'name': 'gene_symbol',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about genetic variants',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'genetics'}}},
{   'description': 'Identify a DNA or protein sequence using NCBI BLAST.',
    'name': 'blast_sequence',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'Query sequence',
                                   'name': 'sequence',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'BLAST database (e.g., '
                                                  'core_nt or nr)',
                                   'name': 'database',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'BLAST program (blastn or '
                                                  'blastp)',
                                   'name': 'program',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'BLAST '
                                                                                   'job '
                                                                                   'timeout '
                                                                                   'exceeded',
                                                                      'resolution': 'Retry '
                                                                                    'the '
                                                                                    'BLAST '
                                                                                    'search '
                                                                                    'or '
                                                                                    'increase '
                                                                                    'the '
                                                                                    'timeout.',
                                                                      'source': 'return '
                                                                                '"BLAST '
                                                                                'search '
                                                                                'failed '
                                                                                'after '
                                                                                'maximum '
                                                                                'attempts '
                                                                                'due '
                                                                                'to '
                                                                                'timeout"'},
                                                                  {   'condition': 'No '
                                                                                   'BLAST '
                                                                                   'results '
                                                                                   'found',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'input '
                                                                                    'sequence '
                                                                                    'and '
                                                                                    'database.',
                                                                      'source': 'return '
                                                                                '"No '
                                                                                'BLAST '
                                                                                'results '
                                                                                'found"'},
                                                                  {   'condition': 'No '
                                                                                   'alignments '
                                                                                   'found',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'input '
                                                                                    'sequence '
                                                                                    'and '
                                                                                    'database.',
                                                                      'source': 'return '
                                                                                '"No '
                                                                                'alignments '
                                                                                'found '
                                                                                '- '
                                                                                'sequence '
                                                                                'might '
                                                                                'be '
                                                                                'too '
                                                                                'short '
                                                                                'or '
                                                                                'low '
                                                                                'complexity"'},
                                                                  {   'condition': 'Error '
                                                                                   'during '
                                                                                   'BLAST '
                                                                                   'search',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'error '
                                                                                    'message '
                                                                                    'and '
                                                                                    'the '
                                                                                    'input '
                                                                                    'parameters.',
                                                                      'source': 'return '
                                                                                'f"Error '
                                                                                'during '
                                                                                'BLAST '
                                                                                'search '
                                                                                'after '
                                                                                'maximum '
                                                                                'attempts: '
                                                                                '{str(e)}"'},
                                                                  {   'condition': 'BLAST '
                                                                                   'search '
                                                                                   'failed '
                                                                                   'after '
                                                                                   'maximum '
                                                                                   'attempts',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'input '
                                                                                    'sequence '
                                                                                    'and '
                                                                                    'database.',
                                                                      'source': 'return '
                                                                                '"BLAST '
                                                                                'search '
                                                                                'failed '
                                                                                'after '
                                                                                'maximum '
                                                                                'attempts"'}]},
                          'return_schema': {   'description': 'A dictionary '
                                                              'containing the '
                                                              'title, e-value, '
                                                              'identity '
                                                              'percentage, and '
                                                              'coverage '
                                                              'percentage of '
                                                              'the best '
                                                              'alignment',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the Reactome database using natural language or a '
                   'direct endpoint; optionally download pathway diagrams.',
    'name': 'query_reactome',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct endpoint or full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': False,
                                   'description': 'Download pathway diagram if '
                                                  'available',
                                   'name': 'download',
                                   'type': 'bool'},
                               {   'default': None,
                                   'description': 'Directory to save downloads',
                                   'name': 'output_dir',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about biological pathways',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the RegulomeDB database using natural language or '
                   'direct endpoint.',
    'name': 'query_regulomedb',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct RegulomeDB endpoint '
                                                  'URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': False,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about regulatory elements',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the PRIDE proteomics database using natural language '
                   'or a direct endpoint.',
    'name': 'query_pride',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Full endpoint to query',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': 3,
                                   'description': 'Maximum number of results',
                                   'name': 'max_results',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about proteomics data',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the Guide to PHARMACOLOGY (GtoPdb) database using '
                   'natural language or a direct endpoint.',
    'name': 'query_gtopdb',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Full API endpoint to query',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about drug '
                                                  'targets/ligands/interactions',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the ReMap database for regulatory elements and '
                   'transcription factor binding.',
    'name': 'query_remap',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Full API endpoint to query',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about TF binding sites',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the Mouse Phenome Database (MPD) using natural '
                   'language or a direct endpoint.',
    'name': 'query_mpd',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Full API endpoint to query',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about mouse '
                                                  'phenotypes/strains',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the Electron Microscopy Data Bank (EMDB) using '
                   'natural language or a direct endpoint.',
    'name': 'query_emdb',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Full API endpoint to query',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about EM structures',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query Synapse REST API for biomedical datasets/files using '
                   'natural language or structured search parameters. Supports '
                   'optional authentication via SYNAPSE_AUTH_TOKEN.',
    'name': 'query_synapse',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Search term(s) (AND logic '
                                                  'across list)',
                                   'name': 'query_term',
                                   'type': 'str|list[str]'},
                               {   'default': [   'name',
                                                  'node_type',
                                                  'description'],
                                   'description': 'Fields to return',
                                   'name': 'return_fields',
                                   'type': 'list[str]'},
                               {   'default': 20,
                                   'description': 'Max results (20 typical, up '
                                                  'to 50)',
                                   'name': 'max_results',
                                   'type': 'int'},
                               {   'default': 'dataset',
                                   'description': "'dataset', 'file', or "
                                                  "'folder'",
                                   'name': 'query_type',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return full API response or '
                                                  'formatted',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about biomedical data',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing '
                                                              'query '
                                                              'information and '
                                                              'Synapse API '
                                                              'results',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the PubChem PUG-REST API using natural language or a '
                   'direct endpoint.',
    'name': 'query_pubchem',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct PubChem API endpoint '
                                                  'or full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': 5,
                                   'description': 'Max results (rate-limited '
                                                  'to 5 rps)',
                                   'name': 'max_results',
                                   'type': 'int'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about chemical compounds',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the ChEMBL REST API via natural language, direct '
                   'endpoint, or identifiers (chembl_id, smiles, '
                   'molecule_name).',
    'name': 'query_chembl',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct ChEMBL API endpoint '
                                                  'or full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'ChEMBL ID (e.g., '
                                                  "'CHEMBL25')",
                                   'name': 'chembl_id',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'SMILES for '
                                                  'similarity/substructure',
                                   'name': 'smiles',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Molecule name to search',
                                   'name': 'molecule_name',
                                   'type': 'str'},
                               {   'default': 20,
                                   'description': 'Max results',
                                   'name': 'max_results',
                                   'type': 'int'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about bioactivity data',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the UniChem 2.0 REST API using natural language or a '
                   'direct endpoint.',
    'name': 'query_unichem',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct UniChem endpoint or '
                                                  'full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about chemical '
                                                  'cross-references',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the ClinicalTrials.gov API v2 using natural language '
                   'or a direct endpoint.',
    'name': 'query_clinicaltrials',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct ClinicalTrials.gov '
                                                  'endpoint or full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': 10,
                                   'description': 'Page size for results '
                                                  '(pageSize)',
                                   'name': 'max_results',
                                   'type': 'int'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about clinical trials',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the DailyMed RESTful API using natural language or a '
                   'direct endpoint.',
    'name': 'query_dailymed',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct DailyMed endpoint or '
                                                  'full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': 'json',
                                   'description': "'json' or 'xml'",
                                   'name': 'format',
                                   'type': 'str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about drug labeling',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the QuickGO API using natural language or a direct '
                   'endpoint.',
    'name': 'query_quickgo',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct QuickGO endpoint or '
                                                  'full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': 25,
                                   'description': 'Max results (limit, up to '
                                                  '100)',
                                   'name': 'max_results',
                                   'type': 'int'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about GO terms/annotations',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'or error '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Query the ENCODE Portal API to locate functional genomics '
                   'data (experiments, files, biosamples, datasets).',
    'name': 'query_encode',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Direct ENCODE Portal '
                                                  'endpoint or full URL',
                                   'name': 'endpoint',
                                   'type': 'str'},
                               {   'default': 25,
                                   'description': 'Limit for search endpoints '
                                                  "(number or 'all')",
                                   'name': 'max_results',
                                   'type': 'int|str'},
                               {   'default': True,
                                   'description': 'Return detailed results',
                                   'name': 'verbose',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Natural language query '
                                                  'about functional genomics '
                                                  'data',
                                   'name': 'prompt',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'query results '
                                                              'with data '
                                                              'location '
                                                              'information',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Given genomic coordinates, retrieve intersecting ENCODE '
                   'SCREEN cCREs.',
    'name': 'region_to_ccre_screen',
    'optional_parameters': [   {   'default': 'GRCh38',
                                   'description': 'Genome assembly (e.g., '
                                                  "'GRCh38')",
                                   'name': 'assembly',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': "Chromosome (e.g., 'chr12')",
                                   'name': 'coord_chrom',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Start coordinate',
                                   'name': 'coord_start',
                                   'type': 'int'},
                               {   'default': None,
                                   'description': 'End coordinate',
                                   'name': 'coord_end',
                                   'type': 'int'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Request '
                                                                                   'failed',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'API '
                                                                                    'status '
                                                                                    'and '
                                                                                    'the '
                                                                                    'provided '
                                                                                    'data.',
                                                                      'source': 'raise '
                                                                                'Exception(f"Request '
                                                                                'failed '
                                                                                'with '
                                                                                'status '
                                                                                'code '
                                                                                '{response.status_code}. '
                                                                                'Response: '
                                                                                '{response.text}")'},
                                                                  {   'condition': 'API '
                                                                                   'error',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'API '
                                                                                    'error '
                                                                                    'message.',
                                                                      'source': 'raise '
                                                                                'Exception(f"API '
                                                                                'error: '
                                                                                '{response_json[\'errors\']}")'},
                                                                  {   'condition': 'General '
                                                                                   'exception',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'exception '
                                                                                    'message.',
                                                                      'source': 'steps.append(f"Exception '
                                                                                'encountered: '
                                                                                '{str(e)}")'}]},
                          'return_schema': {   'description': 'A detailed '
                                                              'string '
                                                              'explaining the '
                                                              'steps and the '
                                                              'intersecting '
                                                              'cCRE data or '
                                                              'any error '
                                                              'encountered.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}},
{   'description': 'Given a cCRE accession, return k nearest genes sorted by '
                   'distance.',
    'name': 'get_genes_near_ccre',
    'optional_parameters': [   {   'default': 10,
                                   'description': 'Number of nearby genes to '
                                                  'return',
                                   'name': 'k',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'ENCODE cCRE accession ID '
                                                  "(e.g., 'EH38E1516980')",
                                   'name': 'accession',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Genome assembly (e.g., '
                                                  "'GRCh38')",
                                   'name': 'assembly',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Chromosome of the cCRE '
                                                  "(e.g., 'chr12')",
                                   'name': 'chromosome',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'API '
                                                                                   'request '
                                                                                   'fails',
                                                                      'resolution': 'Check '
                                                                                    'API '
                                                                                    'status '
                                                                                    'and '
                                                                                    'input '
                                                                                    'parameters.',
                                                                      'source': 'response.ok'},
                                                                  {   'condition': 'API '
                                                                                   'returns '
                                                                                   'errors',
                                                                      'resolution': 'Check '
                                                                                    'API '
                                                                                    'response '
                                                                                    'for '
                                                                                    'error '
                                                                                    'details '
                                                                                    'and '
                                                                                    'input '
                                                                                    'parameters.',
                                                                      'source': 'if '
                                                                                '"errors" '
                                                                                'in '
                                                                                'response_json:'},
                                                                  {   'condition': 'No '
                                                                                   'nearby '
                                                                                   'genes '
                                                                                   'found',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'input '
                                                                                    'accession '
                                                                                    'and '
                                                                                    'assembly, '
                                                                                    'or '
                                                                                    'the '
                                                                                    'availability '
                                                                                    'of '
                                                                                    'nearby '
                                                                                    'genes '
                                                                                    'in '
                                                                                    'the '
                                                                                    'database.',
                                                                      'source': 'if '
                                                                                'not '
                                                                                'nearby_genes:'}]},
                          'return_schema': {   'description': 'Steps performed '
                                                              'and the result.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'database'}}}
]
