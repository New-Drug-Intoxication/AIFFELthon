description = [
{   'description': 'Fetches supplementary information for a paper given its '
                   'DOI and saves it to a specified directory.',
    'name': 'fetch_supplementary_info_from_doi',
    'optional_parameters': [   {   'default': 'supplementary_info',
                                   'description': 'Directory to save '
                                                  'supplementary files',
                                   'name': 'output_dir',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'The paper DOI',
                                   'name': 'doi',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Failed '
                                                                                   'to '
                                                                                   'resolve '
                                                                                   'DOI',
                                                                      'resolution': 'Check '
                                                                                    'DOI '
                                                                                    'and '
                                                                                    'network '
                                                                                    'connection.',
                                                                      'source': 'return '
                                                                                '{"log": '
                                                                                'research_log, '
                                                                                '"files": '
                                                                                '[]}'},
                                                                  {   'condition': 'Failed '
                                                                                   'to '
                                                                                   'access '
                                                                                   'publisher '
                                                                                   'page',
                                                                      'resolution': 'Check '
                                                                                    'network '
                                                                                    'connection '
                                                                                    'and '
                                                                                    'publisher '
                                                                                    'site '
                                                                                    'availability.',
                                                                      'source': 'return '
                                                                                '{"log": '
                                                                                'research_log, '
                                                                                '"files": '
                                                                                '[]}'},
                                                                  {   'condition': 'No '
                                                                                   'supplementary '
                                                                                   'materials '
                                                                                   'found',
                                                                      'resolution': 'Check '
                                                                                    'if '
                                                                                    'supplementary '
                                                                                    'materials '
                                                                                    'exist '
                                                                                    'for '
                                                                                    'the '
                                                                                    'DOI.',
                                                                      'source': 'return '
                                                                                'research_log'},
                                                                  {   'condition': 'Failed '
                                                                                   'to '
                                                                                   'download '
                                                                                   'file',
                                                                      'resolution': 'Check '
                                                                                    'file '
                                                                                    'availability '
                                                                                    'and '
                                                                                    'network '
                                                                                    'connection.',
                                                                      'source': 'research_log.append(f"Failed '
                                                                                'to '
                                                                                'download '
                                                                                'file '
                                                                                'from '
                                                                                '{link}")'}]},
                          'return_schema': {   'description': 'A string '
                                                              'containing the '
                                                              'research log.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'literature'}}},
{   'description': 'Query arXiv for papers based on the provided search query.',
    'name': 'query_arxiv',
    'optional_parameters': [   {   'default': 10,
                                   'description': 'The maximum number of '
                                                  'papers to retrieve.',
                                   'name': 'max_papers',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'The search query string.',
                                   'name': 'query',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Exception '
                                                                                   'during '
                                                                                   'arXiv '
                                                                                   'query',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'query '
                                                                                    'and '
                                                                                    'arXiv '
                                                                                    'service '
                                                                                    'availability.',
                                                                      'source': 'return '
                                                                                'f"Error '
                                                                                'querying '
                                                                                'arXiv: '
                                                                                '{e}"'}]},
                          'return_schema': {   'description': 'The formatted '
                                                              'search results '
                                                              'or an error '
                                                              'message.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'literature'}}},
{   'description': 'Query Google Scholar for papers based on the provided '
                   'search query and return the first search result.',
    'name': 'query_scholar',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'The search query string.',
                                   'name': 'query',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'An '
                                                                                   'exception '
                                                                                   'occurs '
                                                                                   'during '
                                                                                   'the '
                                                                                   'Google '
                                                                                   'Scholar '
                                                                                   'query.',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'query '
                                                                                    'string, '
                                                                                    'network '
                                                                                    'connection, '
                                                                                    'or '
                                                                                    'Google '
                                                                                    "Scholar's "
                                                                                    'availability.',
                                                                      'source': 'return '
                                                                                'f"Error '
                                                                                'querying '
                                                                                'Google '
                                                                                'Scholar: '
                                                                                '{e}"'}]},
                          'return_schema': {   'description': 'The first '
                                                              'search result '
                                                              'formatted or an '
                                                              'error message.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'literature'}}},
{   'description': 'Query PubMed for papers based on the provided search '
                   'query.',
    'name': 'query_pubmed',
    'optional_parameters': [   {   'default': 10,
                                   'description': 'The maximum number of '
                                                  'papers to retrieve.',
                                   'name': 'max_papers',
                                   'type': 'int'},
                               {   'default': 3,
                                   'description': 'Maximum number of retry '
                                                  'attempts with modified '
                                                  'queries.',
                                   'name': 'max_retries',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'The search query string.',
                                   'name': 'query',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'PubMed '
                                                                                   'query '
                                                                                   'fails',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'query, '
                                                                                    'network '
                                                                                    'connection, '
                                                                                    'or '
                                                                                    'PubMed '
                                                                                    'service '
                                                                                    'availability.',
                                                                      'source': 'return '
                                                                                'f"Error '
                                                                                'querying '
                                                                                'PubMed: '
                                                                                '{e}"'},
                                                                  {   'condition': 'No '
                                                                                   'papers '
                                                                                   'found '
                                                                                   'after '
                                                                                   'multiple '
                                                                                   'query '
                                                                                   'attempts',
                                                                      'resolution': 'Refine '
                                                                                    'the '
                                                                                    'search '
                                                                                    'query '
                                                                                    'or '
                                                                                    'increase '
                                                                                    'the '
                                                                                    'max_retries '
                                                                                    'parameter.',
                                                                      'source': 'return '
                                                                                '"No '
                                                                                'papers '
                                                                                'found '
                                                                                'on '
                                                                                'PubMed '
                                                                                'after '
                                                                                'multiple '
                                                                                'query '
                                                                                'attempts."'}]},
                          'return_schema': {   'description': 'The formatted '
                                                              'search results '
                                                              'or an error '
                                                              'message.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'literature'}}},
{   'description': 'Search using Google search and return formatted results.',
    'name': 'search_google',
    'optional_parameters': [   {   'default': 3,
                                   'description': 'Number of results to return',
                                   'name': 'num_results',
                                   'type': 'int'},
                               {   'default': 'en',
                                   'description': 'Language code for search '
                                                  'results',
                                   'name': 'language',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'The search query (e.g., '
                                                  '"protocol text or search '
                                                  'question")',
                                   'name': 'query',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Exception '
                                                                                   'during '
                                                                                   'search',
                                                                      'resolution': 'N/A',
                                                                      'source': 'str(e)'}]},
                          'return_schema': {   'description': 'List of '
                                                              'dictionaries '
                                                              'containing '
                                                              'search results '
                                                              'with title and '
                                                              'URL',
                                               'type': 'list'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'literature'}}},
{   'description': 'Extract the text content of a webpage using requests and '
                   'BeautifulSoup.',
    'name': 'extract_url_content',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'Webpage URL to extract '
                                                  'content from',
                                   'name': 'url',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Text content of '
                                                              'the webpage',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'general'}}},
{   'description': 'Extract text content from a PDF file.',
    'name': 'extract_pdf_content',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'URL of the PDF file',
                                   'name': 'url',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'The '
                                                                                   'URL '
                                                                                   'does '
                                                                                   'not '
                                                                                   'end '
                                                                                   'with '
                                                                                   '.pdf '
                                                                                   'and '
                                                                                   'no '
                                                                                   'PDF '
                                                                                   'link '
                                                                                   'is '
                                                                                   'found.',
                                                                      'resolution': 'Provide '
                                                                                    'a '
                                                                                    'direct '
                                                                                    'link '
                                                                                    'to '
                                                                                    'a '
                                                                                    'PDF '
                                                                                    'file.',
                                                                      'source': 'return '
                                                                                'f"No '
                                                                                'PDF '
                                                                                'file '
                                                                                'found '
                                                                                'at '
                                                                                '{url}. '
                                                                                'Please '
                                                                                'provide '
                                                                                'a '
                                                                                'direct '
                                                                                'link '
                                                                                'to '
                                                                                'a '
                                                                                'PDF '
                                                                                'file."'},
                                                                  {   'condition': 'The '
                                                                                   'URL '
                                                                                   'does '
                                                                                   'not '
                                                                                   'return '
                                                                                   'a '
                                                                                   'valid '
                                                                                   'PDF '
                                                                                   'file.',
                                                                      'resolution': 'Ensure '
                                                                                    'the '
                                                                                    'URL '
                                                                                    'points '
                                                                                    'to '
                                                                                    'a '
                                                                                    'valid '
                                                                                    'PDF '
                                                                                    'file.',
                                                                      'source': 'return '
                                                                                'f"The '
                                                                                'URL '
                                                                                'did '
                                                                                'not '
                                                                                'return '
                                                                                'a '
                                                                                'valid '
                                                                                'PDF '
                                                                                'file. '
                                                                                'Content '
                                                                                'type: '
                                                                                '{content_type}"'},
                                                                  {   'condition': 'The '
                                                                                   'PDF '
                                                                                   'file '
                                                                                   'does '
                                                                                   'not '
                                                                                   'contain '
                                                                                   'any '
                                                                                   'extractable '
                                                                                   'text.',
                                                                      'resolution': 'The '
                                                                                    'PDF '
                                                                                    'may '
                                                                                    'be '
                                                                                    'image-based '
                                                                                    'and '
                                                                                    'require '
                                                                                    'OCR.',
                                                                      'source': 'return '
                                                                                '"The '
                                                                                'PDF '
                                                                                'file '
                                                                                'did '
                                                                                'not '
                                                                                'contain '
                                                                                'any '
                                                                                'extractable '
                                                                                'text. '
                                                                                'It '
                                                                                'may '
                                                                                'be '
                                                                                'an '
                                                                                'image-based '
                                                                                'PDF '
                                                                                'requiring '
                                                                                'OCR."'},
                                                                  {   'condition': 'Error '
                                                                                   'downloading '
                                                                                   'PDF.',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'URL '
                                                                                    'and '
                                                                                    'network '
                                                                                    'connection.',
                                                                      'source': 'return '
                                                                                'f"Error '
                                                                                'downloading '
                                                                                'PDF: '
                                                                                '{str(e)}"'},
                                                                  {   'condition': 'Error '
                                                                                   'extracting '
                                                                                   'text '
                                                                                   'from '
                                                                                   'PDF.',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'PDF '
                                                                                    'file '
                                                                                    'and '
                                                                                    'the '
                                                                                    'PyPDF2 '
                                                                                    'library.',
                                                                      'source': 'return '
                                                                                'f"Error '
                                                                                'extracting '
                                                                                'text '
                                                                                'from '
                                                                                'PDF: '
                                                                                '{str(e)}"'}]},
                          'return_schema': {   'description': 'The extracted '
                                                              'text content '
                                                              'from the PDF',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'transformation',
                                           'domain': 'general'}}},
{   'description': 'Initiate an advanced web search by launching a specialized '
                   'agent to collect relevant information and citations '
                   'through multiple rounds of web searches for a given query.',
    'name': 'advanced_web_search_claude',
    'optional_parameters': [   {   'default': 1,
                                   'description': 'Maximum number of searches',
                                   'name': 'max_searches',
                                   'type': 'int'},
                               {   'default': 3,
                                   'description': 'Maximum number of retry '
                                                  'attempts with modified '
                                                  'queries.',
                                   'name': 'max_retries',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'The search query string.',
                                   'name': 'query',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'A formatted '
                                                              'string '
                                                              'containing the '
                                                              'full text '
                                                              'response from '
                                                              'Claude and the '
                                                              'citations.',
                                               'type': 'str'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': None}}}
]
