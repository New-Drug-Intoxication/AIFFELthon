description = [
{   'description': 'Find all Open Reading Frames (ORFs) in a DNA sequence '
                   'using Biopython, searching both forward and reverse '
                   'complement strands.',
    'name': 'annotate_open_reading_frames',
    'optional_parameters': [   {   'default': False,
                                   'description': 'Whether to search the '
                                                  'reverse complement strand',
                                   'name': 'search_reverse',
                                   'type': 'bool'},
                               {   'default': False,
                                   'description': 'Whether to filter out ORFs '
                                                  'with same end but later '
                                                  'start',
                                   'name': 'filter_subsets',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'DNA sequence to analyze',
                                   'name': 'sequence',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Minimum length of ORF in '
                                                  'nucleotides',
                                   'name': 'min_length',
                                   'type': 'int'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing:\n'
                                                              '        - '
                                                              'explanation: '
                                                              'Explanation of '
                                                              'the output '
                                                              'fields\n'
                                                              '        - '
                                                              'summary_stats: '
                                                              'Statistical '
                                                              'overview of '
                                                              'found ORFs\n'
                                                              '        - orfs: '
                                                              'List of all '
                                                              'found ORFs, '
                                                              'where each ORF '
                                                              'contains:\n'
                                                              '            - '
                                                              'sequence: '
                                                              'Nucleotide '
                                                              'sequence of the '
                                                              'ORF\n'
                                                              '            - '
                                                              'aa_sequence: '
                                                              'Translated '
                                                              'amino acid '
                                                              'sequence\n'
                                                              '            - '
                                                              'start: Start '
                                                              'position in '
                                                              'original '
                                                              'sequence '
                                                              '(0-based)\n'
                                                              '            - '
                                                              'end: End '
                                                              'position in '
                                                              'original '
                                                              'sequence\n'
                                                              '            - '
                                                              "strand: '+' for "
                                                              'forward strand, '
                                                              "'-' for reverse "
                                                              'complement\n'
                                                              '            - '
                                                              'frame: Reading '
                                                              'frame (1,2,3 '
                                                              'for forward; '
                                                              '-1,-2,-3 for '
                                                              'reverse)',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'molecular_biology'}}},
{   'description': "Annotate a DNA sequence using pLannotate's command-line "
                   'interface.',
    'name': 'annotate_plasmid',
    'optional_parameters': [   {   'default': True,
                                   'description': 'Whether the sequence is '
                                                  'circular',
                                   'name': 'is_circular',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'The DNA sequence to '
                                                  'annotate',
                                   'name': 'sequence',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Annotation '
                                                                                   'fails',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'error '
                                                                                    'message '
                                                                                    'and '
                                                                                    'input '
                                                                                    'sequence.',
                                                                      'source': 'print(f"Error '
                                                                                'during '
                                                                                'annotation: '
                                                                                '{e}")'}]},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing '
                                                              'annotation '
                                                              'results or None '
                                                              'if annotation '
                                                              'fails',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Retrieves the coding sequence(s) of a specified gene from '
                   'NCBI Entrez.',
    'name': 'get_gene_coding_sequence',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Email address for NCBI '
                                                  'Entrez (recommended)',
                                   'name': 'email',
                                   'type': 'str'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Name of the gene',
                                   'name': 'gene_name',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Name of the organism',
                                   'name': 'organism',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'No '
                                                                                   'records '
                                                                                   'found '
                                                                                   'for '
                                                                                   'gene',
                                                                      'resolution': 'Check '
                                                                                    'gene '
                                                                                    'name '
                                                                                    'and '
                                                                                    'organism '
                                                                                    'spelling.',
                                                                      'source': 'raise '
                                                                                'ValueError(f"No '
                                                                                'records '
                                                                                'found '
                                                                                'for '
                                                                                'gene '
                                                                                "'{gene_name}' "
                                                                                'in '
                                                                                'organism '
                                                                                '\'{organism}\'")'},
                                                                  {   'condition': 'Unable '
                                                                                   'to '
                                                                                   'process '
                                                                                   'gene '
                                                                                   'record',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'gene '
                                                                                    'record '
                                                                                    'format '
                                                                                    'from '
                                                                                    'NCBI '
                                                                                    'Entrez.',
                                                                      'source': 'raise '
                                                                                'RuntimeError(f"Unable '
                                                                                'to '
                                                                                'process '
                                                                                'gene '
                                                                                'record: '
                                                                                '{e}") '
                                                                                'from '
                                                                                'None'},
                                                                  {   'condition': 'Failed '
                                                                                   'to '
                                                                                   'retrieve '
                                                                                   'coding '
                                                                                   'sequences',
                                                                      'resolution': 'Check '
                                                                                    'the '
                                                                                    'underlying '
                                                                                    'exception '
                                                                                    'for '
                                                                                    'details.',
                                                                      'source': 'raise '
                                                                                'RuntimeError(f"Failed '
                                                                                'to '
                                                                                'retrieve '
                                                                                'coding '
                                                                                'sequences: '
                                                                                '{str(e)}") '
                                                                                'from '
                                                                                'e'}]},
                          'return_schema': {   'description': 'List of '
                                                              'dictionaries '
                                                              'containing:\n'
                                                              '            - '
                                                              'refseq_id: '
                                                              'RefSeq ID of '
                                                              'the gene\n'
                                                              '            - '
                                                              'sequence: '
                                                              'Coding sequence '
                                                              'of the gene',
                                               'type': 'list'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Unified function to retrieve plasmid sequences from either '
                   'Addgene or NCBI. If is_addgene is True or identifier is '
                   'numeric, uses Addgene. Otherwise searches NCBI using the '
                   'plasmid name.',
    'name': 'get_plasmid_sequence',
    'optional_parameters': [   {   'default': None,
                                   'description': 'Force Addgene lookup if '
                                                  'True, force NCBI if False. '
                                                  'If None, attempts to '
                                                  'auto-detect based on '
                                                  'identifier format.',
                                   'name': 'is_addgene',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Either an Addgene ID or '
                                                  'plasmid name',
                                   'name': 'identifier',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'Failed '
                                                                                   'to '
                                                                                   'retrieve '
                                                                                   'Addgene '
                                                                                   'plasmid',
                                                                      'resolution': 'Check '
                                                                                    'Addgene '
                                                                                    'ID '
                                                                                    'and '
                                                                                    'network '
                                                                                    'connection.',
                                                                      'source': 'print(f"Failed '
                                                                                'to '
                                                                                'retrieve '
                                                                                'Addgene '
                                                                                'plasmid '
                                                                                '{plasmid_id}")'},
                                                                  {   'condition': 'No '
                                                                                   'sequence '
                                                                                   'found '
                                                                                   'for '
                                                                                   'Addgene '
                                                                                   'plasmid',
                                                                      'resolution': 'Check '
                                                                                    'Addgene '
                                                                                    'ID '
                                                                                    'and '
                                                                                    'the '
                                                                                    'availability '
                                                                                    'of '
                                                                                    'the '
                                                                                    'sequence '
                                                                                    'on '
                                                                                    'Addgene.',
                                                                      'source': 'print(f"No '
                                                                                'sequence '
                                                                                'found '
                                                                                'for '
                                                                                'Addgene '
                                                                                'plasmid '
                                                                                '{plasmid_id}")'},
                                                                  {   'condition': 'No '
                                                                                   'results '
                                                                                   'found '
                                                                                   'for '
                                                                                   'plasmid '
                                                                                   'name '
                                                                                   'in '
                                                                                   'NCBI.',
                                                                      'resolution': 'Check '
                                                                                    'plasmid '
                                                                                    'name '
                                                                                    'and '
                                                                                    'NCBI '
                                                                                    'database.',
                                                                      'source': 'print(f"No '
                                                                                'results '
                                                                                'found '
                                                                                'for '
                                                                                '{plasmid_name} '
                                                                                'in '
                                                                                'NCBI.")'},
                                                                  {   'condition': 'Error '
                                                                                   'retrieving '
                                                                                   'sequence '
                                                                                   'for '
                                                                                   'plasmid '
                                                                                   'name',
                                                                      'resolution': 'Check '
                                                                                    'plasmid '
                                                                                    'name, '
                                                                                    'NCBI '
                                                                                    'database, '
                                                                                    'and '
                                                                                    'sequence '
                                                                                    'retrieval '
                                                                                    'process.',
                                                                      'source': 'print(f"Error '
                                                                                'retrieving '
                                                                                'sequence '
                                                                                'for '
                                                                                '{plasmid_name}: '
                                                                                '{str(e)}")'}]},
                          'return_schema': {   'description': 'The plasmid '
                                                              'sequence and '
                                                              'metadata if '
                                                              'found, None '
                                                              'otherwise',
                                               'type': 'Optional[Dict[str, '
                                                       'Any]]'},
                          'test_example': None,
                          'tool_type': {   'category': 'retrieval',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Align short sequences (primers) to a longer sequence, '
                   'allowing for one mismatch. Checks both forward and reverse '
                   'complement strands.',
    'name': 'align_sequences',
    'optional_parameters': [],
    'required_parameters': [   {   'default': None,
                                   'description': 'Target DNA sequence',
                                   'name': 'long_seq',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Single primer or list of '
                                                  'primers',
                                   'name': 'short_seqs',
                                   'type': 'Union[str, List[str]]'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'List of '
                                                              'alignment '
                                                              'results for '
                                                              'each short '
                                                              'sequence, '
                                                              'including:\n'
                                                              '        - '
                                                              'explanation: '
                                                              'Explanation of '
                                                              'the output '
                                                              'fields\n'
                                                              '        - '
                                                              'sequence: the '
                                                              'short sequence '
                                                              'that was '
                                                              'aligned\n'
                                                              '        - '
                                                              'alignments: '
                                                              'list of '
                                                              'dictionaries '
                                                              'containing:\n'
                                                              '            - '
                                                              'position: '
                                                              '0-based start '
                                                              'position in the '
                                                              'target '
                                                              'sequence\n'
                                                              '            - '
                                                              "strand: '+' for "
                                                              'forward strand, '
                                                              "'-' for reverse "
                                                              'complement\n'
                                                              '            - '
                                                              'mismatches: '
                                                              'list of tuples '
                                                              '(position, '
                                                              'expected_base, '
                                                              'found_base)\n'
                                                              '              '
                                                              'for any '
                                                              'mismatches',
                                               'type': 'list[dict]'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Simulate PCR amplification with given primers and '
                   'sequence.',
    'name': 'pcr_simple',
    'optional_parameters': [   {   'default': False,
                                   'description': 'Whether the sequence is '
                                                  'circular',
                                   'name': 'circular',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Either a sequence string or '
                                                  'path to plasmid file',
                                   'name': 'sequence',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': "Forward primer sequence (5' "
                                                  "to 3')",
                                   'name': 'forward_primer',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': "Reverse primer sequence (5' "
                                                  "to 3')",
                                   'name': 'reverse_primer',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'One '
                                                                                   'or '
                                                                                   'both '
                                                                                   'primers '
                                                                                   'do '
                                                                                   'not '
                                                                                   'align '
                                                                                   'to '
                                                                                   'the '
                                                                                   'sequence.',
                                                                      'resolution': 'Ensure '
                                                                                    'primers '
                                                                                    'align '
                                                                                    'to '
                                                                                    'the '
                                                                                    'sequence.',
                                                                      'source': 'return '
                                                                                '{\n'
                                                                                '            '
                                                                                '"explanation": '
                                                                                '(\n'
                                                                                '                '
                                                                                '"Output '
                                                                                'fields:\\n"\n'
                                                                                '                '
                                                                                '"- '
                                                                                'success: '
                                                                                'Boolean '
                                                                                'indicating '
                                                                                'if '
                                                                                'any '
                                                                                'PCR '
                                                                                'products '
                                                                                'were '
                                                                                'found\\n"\n'
                                                                                '                '
                                                                                '"- '
                                                                                'message: '
                                                                                'Error '
                                                                                'message '
                                                                                'if '
                                                                                'no '
                                                                                'products '
                                                                                'found\\n"\n'
                                                                                '                '
                                                                                '"- '
                                                                                'products: '
                                                                                'Empty '
                                                                                'list '
                                                                                'when '
                                                                                'no '
                                                                                'products '
                                                                                'found\\n"\n'
                                                                                '                '
                                                                                '"- '
                                                                                'forward_binding_sites: '
                                                                                'Number '
                                                                                'of '
                                                                                'forward '
                                                                                'primer '
                                                                                'binding '
                                                                                'locations\\n"\n'
                                                                                '                '
                                                                                '"- '
                                                                                'reverse_binding_sites: '
                                                                                'Number '
                                                                                'of '
                                                                                'reverse '
                                                                                'primer '
                                                                                'binding '
                                                                                'locations"\n'
                                                                                '            '
                                                                                '),\n'
                                                                                '            '
                                                                                '"success": '
                                                                                'False,\n'
                                                                                '            '
                                                                                '"message": '
                                                                                '"One '
                                                                                'or '
                                                                                'both '
                                                                                'primers '
                                                                                'do '
                                                                                'not '
                                                                                'align '
                                                                                'to '
                                                                                'the '
                                                                                'sequence.",\n'
                                                                                '            '
                                                                                '"products": '
                                                                                '[],\n'
                                                                                '            '
                                                                                '"forward_binding_sites": '
                                                                                'len(fwd_result),\n'
                                                                                '            '
                                                                                '"reverse_binding_sites": '
                                                                                'len(rev_result),\n'
                                                                                '        '
                                                                                '}'},
                                                                  {   'condition': 'No '
                                                                                   'valid '
                                                                                   'PCR '
                                                                                   'products '
                                                                                   'found '
                                                                                   'with '
                                                                                   'these '
                                                                                   'primers.',
                                                                      'resolution': 'Check '
                                                                                    'primer '
                                                                                    'design '
                                                                                    'and '
                                                                                    'sequence.',
                                                                      'source': 'return '
                                                                                '{\n'
                                                                                '            '
                                                                                '"explanation": '
                                                                                '(\n'
                                                                                '                '
                                                                                '"Output '
                                                                                'fields:\\n"\n'
                                                                                '                '
                                                                                '"- '
                                                                                'success: '
                                                                                'Boolean '
                                                                                'indicating '
                                                                                'if '
                                                                                'any '
                                                                                'PCR '
                                                                                'products '
                                                                                'were '
                                                                                'found\\n"\n'
                                                                                '                '
                                                                                '"- '
                                                                                'message: '
                                                                                'Error '
                                                                                'message '
                                                                                'if '
                                                                                'no '
                                                                                'products '
                                                                                'found\\n"\n'
                                                                                '                '
                                                                                '"- '
                                                                                'products: '
                                                                                'Empty '
                                                                                'list '
                                                                                'when '
                                                                                'no '
                                                                                'products '
                                                                                'found\\n"\n'
                                                                                '                '
                                                                                '"- '
                                                                                'forward_binding_sites: '
                                                                                'Number '
                                                                                'of '
                                                                                'forward '
                                                                                'primer '
                                                                                'binding '
                                                                                'locations\\n"\n'
                                                                                '                '
                                                                                '"- '
                                                                                'reverse_binding_sites: '
                                                                                'Number '
                                                                                'of '
                                                                                'reverse '
                                                                                'primer '
                                                                                'binding '
                                                                                'locations"\n'
                                                                                '            '
                                                                                '),\n'
                                                                                '            '
                                                                                '"success": '
                                                                                'False,\n'
                                                                                '            '
                                                                                '"message": '
                                                                                '"No '
                                                                                'valid '
                                                                                'PCR '
                                                                                'products '
                                                                                'found '
                                                                                'with '
                                                                                'these '
                                                                                'primers.",\n'
                                                                                '            '
                                                                                '"products": '
                                                                                '[],\n'
                                                                                '            '
                                                                                '"forward_binding_sites": '
                                                                                'len(fwd_positions),\n'
                                                                                '            '
                                                                                '"reverse_binding_sites": '
                                                                                'len(rev_positions),\n'
                                                                                '        '
                                                                                '}'}]},
                          'return_schema': {   'description': 'Results of PCR '
                                                              'simulation '
                                                              'including '
                                                              'products and '
                                                              'primer binding '
                                                              'details',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'simulation',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Simulates restriction enzyme digestion of a DNA sequence '
                   'and returns the resulting fragments with their properties.',
    'name': 'digest_sequence',
    'optional_parameters': [   {   'default': True,
                                   'description': 'Whether the DNA sequence is '
                                                  'circular (True) or linear '
                                                  '(False)',
                                   'name': 'is_circular',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Input DNA sequence to be '
                                                  'digested',
                                   'name': 'dna_sequence',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Names of restriction '
                                                  'enzymes to use for '
                                                  'digestion',
                                   'name': 'enzyme_names',
                                   'type': 'List[str]'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing the '
                                                              'digestion '
                                                              'fragments and '
                                                              'their '
                                                              'properties '
                                                              'including '
                                                              'positions',
                                               'type': 'Dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'simulation',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Identifies restriction enzyme sites in a given DNA '
                   'sequence for specified enzymes.',
    'name': 'find_restriction_sites',
    'optional_parameters': [   {   'default': True,
                                   'description': 'Whether the DNA sequence is '
                                                  'circular (True) or linear '
                                                  '(False)',
                                   'name': 'is_circular',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Complete input DNA sequence',
                                   'name': 'dna_sequence',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'List of restriction enzyme '
                                                  'names to check',
                                   'name': 'enzymes',
                                   'type': 'List[str]'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing all '
                                                              'identified '
                                                              'restriction '
                                                              'sites',
                                               'type': 'Dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Finds common restriction enzyme sites in a DNA sequence '
                   'and returns their cut positions.',
    'name': 'find_restriction_enzymes',
    'optional_parameters': [   {   'default': False,
                                   'description': 'Whether the sequence is '
                                                  'circular',
                                   'name': 'is_circular',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'DNA sequence to analyze',
                                   'name': 'sequence',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary of '
                                                              'enzymes and '
                                                              'their cut '
                                                              'positions',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Compare query sequence against reference sequence to '
                   'identify mutations.',
    'name': 'find_sequence_mutations',
    'optional_parameters': [   {   'default': 1,
                                   'description': 'The start position of the '
                                                  'query sequence',
                                   'name': 'query_start',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'The sequence being analyzed',
                                   'name': 'query_sequence',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'The reference sequence to '
                                                  'compare against',
                                   'name': 'reference_sequence',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {   'do_not': [],
                                                 'important': [   {   'condition': 'If '
                                                                                   'any '
                                                                                   'of '
                                                                                   'the '
                                                                                   'input '
                                                                                   'arguments '
                                                                                   '(query_sequence, '
                                                                                   'reference_sequence, '
                                                                                   'query_start) '
                                                                                   'are '
                                                                                   'falsy',
                                                                      'resolution': 'Ensure '
                                                                                    'all '
                                                                                    'input '
                                                                                    'arguments '
                                                                                    'are '
                                                                                    'valid.',
                                                                      'source': 'return '
                                                                                '{\n'
                                                                                '            '
                                                                                '"explanation": '
                                                                                '(\n'
                                                                                '                '
                                                                                '"Output '
                                                                                'fields:\\n"\n'
                                                                                '                '
                                                                                '"- '
                                                                                'mutations: '
                                                                                'List '
                                                                                'of '
                                                                                'mutations '
                                                                                'found, '
                                                                                'where '
                                                                                'each '
                                                                                'mutation '
                                                                                'is '
                                                                                'formatted '
                                                                                'as:\\n"\n'
                                                                                '                '
                                                                                '"  '
                                                                                '* '
                                                                                'RefAA_Position_QueryAA\\n"\n'
                                                                                '                '
                                                                                '"  '
                                                                                '* '
                                                                                'RefAA: '
                                                                                'Original '
                                                                                'amino '
                                                                                'acid/base '
                                                                                'in '
                                                                                'reference '
                                                                                'sequence\\n"\n'
                                                                                '                '
                                                                                '"  '
                                                                                '* '
                                                                                'Position: '
                                                                                'Position '
                                                                                'where '
                                                                                'mutation '
                                                                                'occurs '
                                                                                '(1-based)\\n"\n'
                                                                                '                '
                                                                                '"  '
                                                                                '* '
                                                                                'QueryAA: '
                                                                                'New '
                                                                                'amino '
                                                                                'acid/base '
                                                                                'in '
                                                                                'query '
                                                                                'sequence\\n"\n'
                                                                                '                '
                                                                                '"  '
                                                                                '* '
                                                                                'Example: '
                                                                                "'A123T' "
                                                                                'means '
                                                                                'position '
                                                                                '123 '
                                                                                'changed '
                                                                                'from '
                                                                                'A '
                                                                                'to '
                                                                                'T\\n"\n'
                                                                                '                '
                                                                                '"- '
                                                                                'success: '
                                                                                'Boolean '
                                                                                'indicating '
                                                                                'if '
                                                                                'comparison '
                                                                                'was '
                                                                                'successful"\n'
                                                                                '            '
                                                                                '),\n'
                                                                                '            '
                                                                                '"mutations": '
                                                                                '[],\n'
                                                                                '            '
                                                                                '"success": '
                                                                                'False,\n'
                                                                                '        '
                                                                                '}'}]},
                          'return_schema': {   'description': 'List of '
                                                              'mutations in '
                                                              'format '
                                                              'RefAA_Position_QueryAA',
                                               'type': 'list'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Design sgRNAs for CRISPR knockout by searching '
                   'pre-computed sgRNA libraries. Returns optimized guide RNAs '
                   'for targeting a specific gene.',
    'name': 'design_knockout_sgrna',
    'optional_parameters': [   {   'default': 'human',
                                   'description': 'Target organism species',
                                   'name': 'species',
                                   'type': 'str'},
                               {   'default': 1,
                                   'description': 'Number of guides to return',
                                   'name': 'num_guides',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Target gene symbol/name '
                                                  '(e.g., "EGFR", "TP53")',
                                   'name': 'gene_name',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Path to the data lake',
                                   'name': 'data_lake_path',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing:\n'
                                                              '        - '
                                                              'explanation: '
                                                              'Explanation of '
                                                              'the output '
                                                              'fields\n'
                                                              '        - '
                                                              'gene_name: '
                                                              'Target gene '
                                                              'name\n'
                                                              '        - '
                                                              'species: Target '
                                                              'species\n'
                                                              '        - '
                                                              'guides: List of '
                                                              'sgRNA sequences',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Return a standard protocol for annealing oligonucleotides '
                   'without phosphorylation.',
    'name': 'get_oligo_annealing_protocol',
    'optional_parameters': [],
    'required_parameters': [],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing '
                                                              'detailed '
                                                              'protocol steps '
                                                              'for oligo '
                                                              'annealing',
                                               'type': 'Dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'transformation',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Return a customized protocol for Golden Gate assembly '
                   'based on the number of inserts and specific DNA sequences.',
    'name': 'get_golden_gate_assembly_protocol',
    'optional_parameters': [   {   'default': 1,
                                   'description': 'Number of inserts to be '
                                                  'assembled',
                                   'name': 'num_inserts',
                                   'type': 'int'},
                               {   'default': 75.0,
                                   'description': 'Amount of vector to use in '
                                                  'ng',
                                   'name': 'vector_amount_ng',
                                   'type': 'float'},
                               {   'default': None,
                                   'description': 'List of insert lengths in '
                                                  'bp',
                                   'name': 'insert_lengths',
                                   'type': 'List[int]'},
                               {   'default': False,
                                   'description': 'Whether this is for library '
                                                  'preparation',
                                   'name': 'is_library_prep',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Type IIS restriction enzyme '
                                                  'to be used',
                                   'name': 'enzyme_name',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Length of the destination '
                                                  'vector in bp',
                                   'name': 'vector_length',
                                   'type': 'int'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing '
                                                              'detailed '
                                                              'protocol steps '
                                                              'for Golden Gate '
                                                              'assembly',
                                               'type': 'Dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'general',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Return a standard protocol for bacterial transformation.',
    'name': 'get_bacterial_transformation_protocol',
    'optional_parameters': [   {   'default': 'ampicillin',
                                   'description': 'Selection antibiotic',
                                   'name': 'antibiotic',
                                   'type': 'str'},
                               {   'default': False,
                                   'description': 'Whether the sequence '
                                                  'contains repetitive '
                                                  'elements',
                                   'name': 'is_repetitive',
                                   'type': 'bool'}],
    'required_parameters': [],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing '
                                                              'detailed '
                                                              'protocol steps '
                                                              'for bacterial '
                                                              'transformation',
                                               'type': 'Dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'transformation',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Design a single primer within the given sequence window.',
    'name': 'design_primer',
    'optional_parameters': [   {   'default': 20,
                                   'description': 'Length of the primer to '
                                                  'design',
                                   'name': 'primer_length',
                                   'type': 'int'},
                               {   'default': 0.4,
                                   'description': 'Minimum GC content',
                                   'name': 'min_gc',
                                   'type': 'float'},
                               {   'default': 0.6,
                                   'description': 'Maximum GC content',
                                   'name': 'max_gc',
                                   'type': 'float'},
                               {   'default': 55.0,
                                   'description': 'Minimum melting temperature '
                                                  'in °C',
                                   'name': 'min_tm',
                                   'type': 'float'},
                               {   'default': 65.0,
                                   'description': 'Maximum melting temperature '
                                                  'in °C',
                                   'name': 'max_tm',
                                   'type': 'float'},
                               {   'default': 100,
                                   'description': 'Size of window to search '
                                                  'for primers',
                                   'name': 'search_window',
                                   'type': 'int'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Target DNA sequence',
                                   'name': 'sequence',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Starting position for '
                                                  'primer search',
                                   'name': 'start_pos',
                                   'type': 'int'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary with '
                                                              'primer '
                                                              'information or '
                                                              'None if no '
                                                              'suitable primer '
                                                              'found',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'analysis',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Design Sanger sequencing primers to verify a specific '
                   'region in a plasmid. First tries to use primers from an '
                   'existing primer pool. If they cannot fully cover the '
                   'region, designs additional primers as needed.',
    'name': 'design_verification_primers',
    'optional_parameters': [   {   'default': None,
                                   'description': 'List of existing primers '
                                                  'with their sequences and '
                                                  'optional names',
                                   'name': 'existing_primers',
                                   'type': 'Optional[List[Dict[str, str]]]'},
                               {   'default': True,
                                   'description': 'Whether the plasmid is '
                                                  'circular',
                                   'name': 'is_circular',
                                   'type': 'bool'},
                               {   'default': 800,
                                   'description': 'Typical read length for '
                                                  'each primer in base pairs',
                                   'name': 'coverage_length',
                                   'type': 'int'},
                               {   'default': 20,
                                   'description': 'Length of newly designed '
                                                  'primers',
                                   'name': 'primer_length',
                                   'type': 'int'},
                               {   'default': 0.4,
                                   'description': 'Minimum GC content for new '
                                                  'primers',
                                   'name': 'min_gc',
                                   'type': 'float'},
                               {   'default': 0.6,
                                   'description': 'Maximum GC content for new '
                                                  'primers',
                                   'name': 'max_gc',
                                   'type': 'float'},
                               {   'default': 55.0,
                                   'description': 'Minimum melting temperature '
                                                  'in °C',
                                   'name': 'min_tm',
                                   'type': 'float'},
                               {   'default': 65.0,
                                   'description': 'Maximum melting temperature '
                                                  'in °C',
                                   'name': 'max_tm',
                                   'type': 'float'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'The complete plasmid '
                                                  'sequence',
                                   'name': 'plasmid_sequence',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Start and end positions to '
                                                  'verify (0-based indexing)',
                                   'name': 'target_region',
                                   'type': 'Tuple[int, int]'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing:\n'
                                                              '        - '
                                                              'target_region: '
                                                              'The region to '
                                                              'be verified\n'
                                                              '        - '
                                                              'recommended_primers: '
                                                              'List of primers '
                                                              'to use (from '
                                                              'existing and/or '
                                                              'newly '
                                                              'designed)\n'
                                                              '        - '
                                                              'coverage_map: '
                                                              'How the primers '
                                                              'cover the '
                                                              'target region',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'general',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Design complementary oligonucleotides with Type IIS '
                   'restriction enzyme overhangs for Golden Gate assembly '
                   'based on restriction site analysis of the backbone.',
    'name': 'design_golden_gate_oligos',
    'optional_parameters': [   {   'default': True,
                                   'description': 'Whether the backbone is '
                                                  'circular',
                                   'name': 'is_circular',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Complete backbone sequence',
                                   'name': 'backbone_sequence',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Sequence to be inserted '
                                                  '(e.g., sgRNA target '
                                                  'sequence)',
                                   'name': 'insert_sequence',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Type IIS restriction enzyme '
                                                  'to be used',
                                   'name': 'enzyme_name',
                                   'type': 'str'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing '
                                                              'overhang '
                                                              'information and '
                                                              'designed oligos',
                                               'type': 'Dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'transformation',
                                           'domain': 'molecular_biology'}}},
{   'description': 'Simulate Golden Gate assembly to predict final construct '
                   'sequences from backbone and fragment sequences.',
    'name': 'golden_gate_assembly',
    'optional_parameters': [   {   'default': True,
                                   'description': 'Whether the backbone is '
                                                  'circular',
                                   'name': 'is_circular',
                                   'type': 'bool'}],
    'required_parameters': [   {   'default': None,
                                   'description': 'Complete backbone sequence',
                                   'name': 'backbone_sequence',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'Type IIS restriction enzyme '
                                                  'to be used (e.g., "BsmBI", '
                                                  '"BsaI")',
                                   'name': 'enzyme_name',
                                   'type': 'str'},
                               {   'default': None,
                                   'description': 'List of fragments to '
                                                  'insert, containing one of: '
                                                  'name + fwd_oligo + '
                                                  'rev_oligo (oligo pair with '
                                                  'matching overhangs) or name '
                                                  '+ sequence (double-stranded '
                                                  'DNA fragment containing '
                                                  'restriction sites)',
                                   'name': 'fragments',
                                   'type': 'List[Dict[str, str]]'}],
    'spec_expansion': {   'failure_pattern': {'do_not': [], 'important': []},
                          'return_schema': {   'description': 'Dictionary '
                                                              'containing:\n'
                                                              '        - '
                                                              'success: '
                                                              'Boolean '
                                                              'indicating if '
                                                              'assembly was '
                                                              'successful\n'
                                                              '        - '
                                                              'assembled_sequence: '
                                                              'The final '
                                                              'assembled '
                                                              'sequence\n'
                                                              '        - '
                                                              'message: Error '
                                                              'message if '
                                                              'assembly failed',
                                               'type': 'dict'},
                          'test_example': None,
                          'tool_type': {   'category': 'simulation',
                                           'domain': 'molecular_biology'}}}
]
