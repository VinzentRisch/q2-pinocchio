# ----------------------------------------------------------------------------
# Copyright (c) 2024, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import importlib

from q2_types.feature_data import FeatureData, Sequence  # , Taxonomy

# from q2_types.per_sample_sequences import SequencesWithQuality
# from q2_types.sample_data import SampleData
from qiime2.plugin import (  # Bool,; Choices,; Float,; Int,; Range,; Str,; Threads,
    Citations,
    Plugin,
)

import q2_long_reads_qc
from q2_long_reads_qc import __version__
from q2_long_reads_qc._action_params import (
    filter_reads_param_descriptions,
    filter_reads_params,
    minimap2_build_param_descriptions,
    minimap2_build_params,
    minimap2_search_param_descriptions,
    minimap2_search_params,
)
from q2_long_reads_qc.types._format import (
    Minimap2IndexDBDirFmt,
    Minimap2IndexDBFmt,
    PairwiseAlignmentMN2DirectoryFormat,
    PairwiseAlignmentMN2Format,
)
from q2_long_reads_qc.types._type import Minimap2IndexDB, PairwiseAlignmentMN2

citations = Citations.load("citations.bib", package="q2_long_reads_qc")

plugin = Plugin(
    name="long-reads-qc",
    version=__version__,
    website="https://github.com/bokulich-lab/q2-plugin-name",
    package="q2_long_reads_qc",
    description="QIIME 2 Plugin for quality control of long read sequences.",
    short_description="",
)

plugin.register_formats(
    Minimap2IndexDBDirFmt,
    Minimap2IndexDBFmt,
    PairwiseAlignmentMN2Format,
    PairwiseAlignmentMN2DirectoryFormat,
)
plugin.register_semantic_types(Minimap2IndexDB, PairwiseAlignmentMN2)
plugin.register_semantic_type_to_format(
    Minimap2IndexDB, artifact_format=Minimap2IndexDBDirFmt
)

plugin.register_semantic_type_to_format(
    FeatureData[PairwiseAlignmentMN2], PairwiseAlignmentMN2DirectoryFormat
)

plugin.methods.register_function(
    function=q2_long_reads_qc.filtering.filter_reads,
    inputs={
        "query_reads": FeatureData[Sequence],
        "minimap2_index": Minimap2IndexDB,
        "reference_reads": FeatureData[Sequence],
    },
    parameters=filter_reads_params,
    outputs=[("filtered_query_reads", FeatureData[Sequence])],
    input_descriptions={
        "query_reads": "The sequences to be filtered.",
        "minimap2_index": "Minimap2 index file. Incompatible with reference_reads.",
        "reference_reads": "Reference sequences. Incompatible with minimap2_index.",
    },
    parameter_descriptions=filter_reads_param_descriptions,
    output_descriptions={
        "filtered_query_reads": "The resulting filtered sequences.",
    },
    name="Filter long sequences using Minimap2.",
    description=(
        "Filter demultiplexed single- or paired-end sequences based "
        "on alignment to a reference database using Minimap2 and samtools. "
        "This versatile command allows for the exclusion of long sequences "
        "or, when exclude_mapped is set to False, selectively retains only "
        "those sequences aligning to the reference."
    ),
    citations=[citations["Minimap2"]],
)


plugin.methods.register_function(
    function=q2_long_reads_qc.minimap2.minimap2_build,
    inputs={"sequences": FeatureData[Sequence]},
    parameters=minimap2_build_params,
    outputs=[("database", Minimap2IndexDB)],
    input_descriptions={
        "sequences": "Reference sequences used to build Minimap2 index."
    },
    parameter_descriptions=minimap2_build_param_descriptions,
    output_descriptions={"database": "Minimap2 index."},
    name="Build Minimap2 index from reference sequences.",
    description="Build Minimap2 index from reference sequences.",
    citations=[citations["Minimap2"]],
)


plugin.methods.register_function(
    function=q2_long_reads_qc.minimap2.minimap2_search,
    inputs={
        "query_reads": FeatureData[Sequence],
        "minimap2_index": Minimap2IndexDB,
        "reference_reads": FeatureData[Sequence],
    },
    parameters=minimap2_search_params,
    outputs=[("search_results", FeatureData[PairwiseAlignmentMN2])],
    input_descriptions={
        "query_reads": "Query sequences.",
        "minimap2_index": "Minimap2 index file. Incompatible with reference_reads.",
        "reference_reads": "Reference sequences. Incompatible with minimap2_index.",
    },
    parameter_descriptions=minimap2_search_param_descriptions,
    output_descriptions={
        "search_results": "Top hits for each query.",
    },
    name="Minimap2 alignment search.",
    description=(
        "Search for top hits in a reference database using alignment between the "
        "query sequences and reference database sequences using Minimap2. Returns a "
        "report of the top M hits for each query (where M=maxaccepts)."
    ),
    citations=[citations["Minimap2"], citations["li2009sequence"]],
)


"""
plugin.pipelines.register_function(
    function=q2_long_reads_qc.classification.classify_consensus_minimap2,
    inputs={'query': FeatureData[Sequence],
            'minimap2_index': Minimap2IndexDB,
            'reference_reads': FeatureData[Sequence],
            'reference_taxonomy': FeatureData[Taxonomy]},
    parameters={'evalue': Float,
                'maxaccepts': Int % Range(1, None),
                'perc_identity': Float % Range(0.0, 1.0, inclusive_end=True),
                'query_cov': Float % Range(0.0, 1.0, inclusive_end=True),
                'strand': Str % Choices(['both', 'plus', 'minus']),
                'output_no_hits': Bool,
                'num_threads': Threads,
                'min_consensus':
                Float % Range(0.5, 1.0, inclusive_end=True, inclusive_start=False),
                'unassignable_label': Str},
    outputs=[ ('search_results', FeatureData[PairwiseAlignmentMN2])],
    input_descriptions={'query': 'Query sequences.',
                        'minimap2_index': 'Minimap2 indexed database. '
                        'Incompatible with reference_reads.',
                        'reference_reads': 'Reference sequences. Incompatible '
                        'with blastdb.',
                        'reference_taxonomy': 'reference taxonomy labels.'},
    parameter_descriptions={
        'evalue': 'BLAST expectation value (E) threshold for saving hits.',
        'strand': ('Align against reference sequences in forward ("plus"), '
        'reverse ("minus"), or both directions ("both").'),
        'maxaccepts': ('Maximum number of hits to keep for each query. BLAST will '
        'choose the first N hits in the reference database that '
        'exceed perc_identity similarity to query. NOTE: the '
        'database is not sorted by similarity to query, so these '
        'are the first N hits that pass the threshold, not '
        'necessarily the top N hits.'),
        'perc_identity': ('Reject match if percent identity to query is lower.'),
        'query_cov': 'Reject match if query alignment coverage per high-'
        'scoring pair is lower. Note: this uses blastn\'s '
        'qcov_hsp_perc parameter, and may not behave identically '
        'to the query_cov parameter used by classify-consensus-'
        'vsearch.',
        'output_no_hits': 'Report both matching and non-matching queries. '
        'WARNING: always use the default setting for this '
        'option unless if you know what you are doing! If '
        'you set this option to False, your sequences and '
        'feature table will need to be filtered to exclude '
        'unclassified sequences, otherwise you may run into '
        'errors downstream from missing feature IDs. Set to '
        'FALSE to mirror default BLAST search.',
        'num_threads': 'Number of threads (CPUs) to use in the BLAST search. '
        'Pass 0 to use all available CPUs.',
        'min_consensus': 'Minimum fraction of assignments must match top '
        'hit to be accepted as consensus assignment.',
        'unassignable_label': 'Annotation given to sequences without any hits.'
    },
    output_descriptions={'search_results': 'Top hits for each query.'},
    name='Minimap2 consensus taxonomy classifier',
    description=('Assign taxonomy to query sequences using Minimap2. Performs '
                 'alignment between query and reference_reads, then '
                 'assigns consensus taxonomy to each query sequence from '
                 'among maxaccepts hits, min_consensus of which share '
                 'that taxonomic assignment. Note that maxaccepts selects the '
                 'first N hits with > perc_identity similarity to query, '
                 'not the top N matches. For top N hits, use '
                 'classify-consensus-vsearch.'),
    #citations=[citations['camacho2009blast+']]
)

plugin.methods.register_function(
    function=q2_long_reads_qc.classification.find_consensus_annotation,
    inputs={'search_results': FeatureData[PairwiseAlignmentMN2],
            'reference_taxonomy': FeatureData[Taxonomy]},
    parameters={
        'min_consensus':
        Float % Range(0.5, 1.0, inclusive_end=True, inclusive_start=False),
        'unassignable_label': Str},
    outputs=[('consensus_taxonomy', FeatureData[Taxonomy])],
    input_descriptions={
        'search_results': 'Search results in BLAST6 output format',
        'reference_taxonomy': 'reference taxonomy labels.'},
    parameter_descriptions={
        'min_consensus': 'Minimum fraction of assignments must match top '
        'hit to be accepted as consensus assignment.',
        'unassignable_label': 'Annotation given when no consensus is found.'
    },
    output_descriptions={
        'consensus_taxonomy': 'Consensus taxonomy and scores.'},
    name='Find consensus among multiple annotations.',
    description=('Find consensus annotation for each query searched against '
                 'a reference database, by finding the least common ancestor '
                 'among one or more semicolon-delimited hierarchical '
                 'annotations. Note that the annotation hierarchy is assumed '
                 'to have an even number of ranks.'),
)

"""

importlib.import_module("q2_long_reads_qc.types._transformer")
