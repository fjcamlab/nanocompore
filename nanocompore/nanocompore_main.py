#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#~~~~~~~~~~~~~~IMPORTS~~~~~~~~~~~~~~#

# Standard library imports
import argparse
from collections import *
import textwrap

# Local imports
from nanocompore import __version__ as package_version
from nanocompore import __name__ as package_name
from nanocompore.SampComp import SampComp
from nanocompore.SimReads import SimReads
from nanocompore.common import *

#~~~~~~~~~~~~~~MAIN PARSER ENTRY POINT~~~~~~~~~~~~~~#

def main(args=None):
    # General parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', '-v', action='version', version='v'+package_version)
    subparsers = parser.add_subparsers(help='Nanocompore implements the following subcommands', dest='sub-command')
    subparsers.required = True

    # Sampcomp subparser
    parser_sc = subparsers.add_parser('sampcomp', formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent("""
        Compare 2 samples and find significant signal\n
        * Minimal example with file_list arguments
            nanocompore sampcomp -1 f1.tsv,f2.tsv -2 f3.tsv,f4.tsv -f ref.fa -o results
        * Minimal example with sample YAML file
            nanocompore sampcomp -y samples.yaml -f ref -o results"""))
    parser_sc.set_defaults(func=sampcomp_main)
    parser_sc_sample_yaml = parser_sc.add_argument_group('YAML sample files', description="Option allowing to describe sample files in a YAML file")
    parser_sc_sample_yaml.add_argument("--sample_yaml", "-y", default=None, type=str, metavar="sample_yaml",
        help="YAML file containing the sample file labels. See formatting in documentation. (required if --file_list1 and --file_list2 not given)")
    parser_sc_sample_args = parser_sc.add_argument_group('Arguments sample files', description="Option allowing to describe sample files directly as command line arguments")
    parser_sc_sample_args.add_argument("--file_list1", "-1", default=None, type=str, metavar="/path/to/Condition1_rep1,/path/to/Codition1_rep2",
        help="Comma separated list of NanopolishComp files for label 1. (required if --sample_yaml not given)")
    parser_sc_sample_args.add_argument("--file_list2", "-2", default=None, type=str, metavar="/path/to/Condition2_rep1,/path/to/Codition2_rep2",
        help="Comma separated list of NanopolishComp files for label 2. (required if --sample_yaml not given)")
    parser_sc_sample_args.add_argument("--label1", type=str, metavar="Condition1", default="Condition1",
        help="Label for files in --file_list1 (default: %(default)s)")
    parser_sc_sample_args.add_argument("--label2", type=str, metavar="Condition2", default="Condition2",
        help="Label for files in --file_list2 (default: %(default)s)")
    parser_sc_io = parser_sc.add_argument_group('Input/Output options')
    parser_sc_io.add_argument("--fasta", "-f", type=str, required=True,
        help="Fasta file used for mapping (required)")
    parser_sc_io.add_argument("--bed", type=str, default=None,
        help="BED file with annotation of transcriptome used for mapping (optional)")
    parser_sc_io.add_argument("--outpath", "-o", type=str, default="results",
        help="Path to the output folder (default: %(default)s)")
    parser_sc_io.add_argument("--outprefix", "-p", type=str, default="out_",
        help="text outprefix for all the files generated by the function (default: %(default)s)")
    parser_sc_io.add_argument("--overwrite", action='store_true', default=False,
        help="Use --outpath even if it exists already (default: %(default)s)")
    parser_sc_filtering = parser_sc.add_argument_group('Transcript filtering options')
    parser_sc_filtering.add_argument("--max_invalid_kmers_freq", type=float, default=0.1,
        help="Max fequency of invalid kmers (default: %(default)s)")
    parser_sc_filtering.add_argument("--min_coverage", type=int, default=30,
        help="Minimum coverage required in each condition to do the comparison (default: %(default)s)")
    parser_sc_filtering.add_argument("--downsample_high_coverage", type=int, default=0,
        help="Used for debug: transcripts with high covergage will be downsampled (default: %(default)s)")
    parser_sc_filtering.add_argument("--min_ref_length", type=int, default=100,
        help="Minimum length of a reference transcript to include it in the analysis (default: %(default)s)")
    parser_sc_testing = parser_sc.add_argument_group('Statistical testing options')
    parser_sc_testing.add_argument("--comparison_methods", type=str, default="GMM,KS",
        help="Comma separated list of comparison methods. Valid methods are: GMM,KS,TT,MW. (default: %(default)s)")
    parser_sc_testing.add_argument("--sequence_context", type=int, default=0, choices=range(0,5),
        help="Sequence context for combining p-values (default: %(default)s)")
    parser_sc_testing.add_argument("--sequence_context_weights", type=str, default="uniform", choices=["uniform", "harmonic"],
        help="Type of weights to use for combining p-values")
    parser_sc_testing.add_argument("--pvalue_thr", type=float, default=0.05,
        help="Adjusted p-value threshold for reporting significant sites (default: %(default)s)")
    parser_sc_testing.add_argument("--logit", action='store_true',
        help="Use logistic regression testing also when all conditions have replicates (default: %(default)s)")
    parser_sc_testing.add_argument("--allow_warnings", action='store_true', default=False,
        help="If True runtime warnings during the ANOVA tests don't raise an error (default: %(default)s)")
    parser_sc_common = parser_sc.add_argument_group('Other options')
    parser_sc_common.add_argument("--nthreads", "-t", type=int, default=3,
        help="Number of threads (default: %(default)s)")
    parser_sc_common.add_argument("--log_level", type=str, default="info", choices=["warning", "info", "debug"],
        help="log level (default: %(default)s)")

    # simreads subparser
    parser_sr = subparsers.add_parser('simreads', formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent("""
        Simulate reads in a NanopolishComp like file from a fasta file and an inbuild model\n
        * Minimal example without model alteration
            nanocompore simreads -f ref.fa -o results -n 50
        * Minimal example with alteration of model intensity loc parameter for 50% of the reads
            nanocompore simreads -f ref.fa -o results -n 50 --intensity_mod_loc 10 --mod_reads_freq 0.5 --mod_bases_freq 0.2"""))
    parser_sr.set_defaults(func=simreads_main)
    parser_sr_io = parser_sr.add_argument_group('Input/Output options')
    parser_sr_io.add_argument("--fasta", "-f", type=str, required=True,
        help="Fasta file containing references to use to generate artificial reads (required)")
    parser_sr_io.add_argument("--run_type", type=str, default="RNA", choices=["RNA", "DNA"],
        help="Define the run type model to import (RNA or DNA) (default: %(default)s)")
    parser_sr_io.add_argument("--outpath", "-o", type=str, default="./",
        help="Path to the output folder (default: %(default)s)")
    parser_sr_io.add_argument("--outprefix", "-p", type=str, default="out",
        help="text outprefix for all the files generated by the function (default: %(default)s)")
    parser_sr_io.add_argument("--overwrite", action='store_true', default=False,
        help="Use --outpath even if it exists already (default: %(default)s)")
    parser_sr_io.add_argument("--nreads_per_ref", "-n", type=int, default=100,
        help="Number of reads to generate per references (default: %(default)s)")
    parser_sr_modify = parser_sr.add_argument_group('Signal modification options')
    parser_sr_modify.add_argument("--intensity_mod_loc", type=float, default=0,
        help="value by which to modify the intensity distribution loc value (mode) (default: %(default)s)")
    parser_sr_modify.add_argument("--intensity_mod_scale", type=float, default=0 ,
        help="value by which to modify the intensity distribution scale value (dispersion) (default: %(default)s)")
    parser_sr_modify.add_argument("--dwell_mod_loc", type=float, default=0,
        help="value by which to modify the dwell time distribution loc value (mode) (default: %(default)s)")
    parser_sr_modify.add_argument("--dwell_mod_scale", type=float, default=0,
        help="value by which to modify the dwell time distribution scale value (mode) (default: %(default)s)")
    parser_sr_modify.add_argument("--mod_reads_freq", type=float, default=0,
        help="Frequency of reads to modify (default: %(default)s)")
    parser_sr_modify.add_argument("--mod_bases_freq", type=float, default=0.25,
        help="Frequency of bases to modify in each read (if possible) (default: %(default)s)")
    parser_sr_modify.add_argument("--mod_bases_type", type=str, default="A", choices=["A","T","C","G"],
        help="Base for which to modify the signal (default: %(default)s)")
    parser_sr_modify.add_argument("--mod_extend_context", type=int, default=2,
        help="number of adjacent base affected by the signal modification following an harmonic serries (default: %(default)s)")
    parser_sr_modify.add_argument("--min_mod_dist", type=int, default=6,
        help="Minimal distance between to bases to modify (default: %(default)s)")
    parser_sr_common = parser_sr.add_argument_group('Other options')
    parser_sr_common.add_argument("--pos_rand_seed", type=int, default=42 ,
        help="Define a seed for randon position picking to get a deterministic behaviour (default: %(default)s)")
    parser_sr_common.add_argument("--not_bound", action='store_true', default=False,
        help="If given, the values generated by the distributions will be released from the min and max observed values bounds from the model file (default: %(default)s)")
    parser_sr_common.add_argument("--log_level", type=str, default="info", choices=["warning", "info", "debug"],
        help="log level (default: %(default)s)")

    # Downstream plot subparser
    parser_plot = subparsers.add_parser('plot', help="Run downstream analysis and plot results")
    parser_plot.set_defaults(func=plot)

    # Parse agrs and call subfunction
    args = parser.parse_args()
    args.func(args)

#~~~~~~~~~~~~~~SUBCOMMAND FUNCTIONS~~~~~~~~~~~~~~#

def sampcomp_main(args):

    # Load eventalign_fn_dict from a YAML file or assemble eventalign_fn_dict for the command line option
    if args.sample_yaml:
        eventalign_fn_dict = args.sample_yaml
    elif args.file_list1 and args.file_list2:
        eventalign_fn_dict = build_eventalign_fn_dict(args.file_list1, args.file_list2, args.label1, args.label2)
    else:
        raise NanocomporeError("Samples eventalign files have to be provided with either `--sample_yaml` or `--file_list1` and `--file_list2`")

    # Init SampComp
    s = SampComp(
        eventalign_fn_dict = eventalign_fn_dict,
        max_invalid_kmers_freq = args.max_invalid_kmers_freq,
        outpath = args.outpath,
        outprefix = args.outprefix,
        overwrite = args.overwrite,
        fasta_fn = args.fasta,
        bed_fn = args.bed,
        nthreads = args.nthreads,
        min_coverage = args.min_coverage,
        min_ref_length = args.min_ref_length,
        downsample_high_coverage = args.downsample_high_coverage,
        comparison_methods = args.comparison_methods,
        logit = args.logit,
        allow_warnings = args.allow_warnings,
        sequence_context = args.sequence_context,
        sequence_context_weights = args.sequence_context_weights,
        log_level = args.log_level)

    # Run SampComp
    db = s()
    # Save all reports
    db.save_all(pvalue_thr=args.pvalue_thr)

def simreads_main(args):

    # Run SimReads
    SimReads(
        fasta_fn = args.fasta,
        outpath = args.outpath,
        outprefix = args.outprefix,
        overwrite = args.overwrite,
        run_type = args.run_type,
        nreads_per_ref = args.nreads_per_ref,
        intensity_mod_loc = args.intensity_mod_loc,
        intensity_mod_scale = args.intensity_mod_scale,
        dwell_mod_loc = args.dwell_mod_loc,
        dwell_mod_scale = args.dwell_mod_scale,
        mod_reads_freq = args.mod_reads_freq,
        mod_bases_freq = args.mod_bases_freq,
        mod_bases_type = args.mod_bases_type,
        mod_extend_context = args.mod_extend_context,
        min_mod_dist = args.min_mod_dist,
        pos_rand_seed = args.pos_rand_seed,
        not_bound = args.not_bound,
        log_level = args.log_level)

def plot(args):
    """"""
    raise NanocomporeError("The plotting CLI methods haven't been implemented yet. Please load the the SampCompDB in jupyter for downstream analysis.")

#~~~~~~~~~~~~~~PRIVATE FUNCTIONS~~~~~~~~~~~~~~#

def build_eventalign_fn_dict(file_list1, file_list2, label1, label2):
    """
    Build the eventalign_fn_dict from file lists and labels
    """
    d = OrderedDict()
    d[label1] = {"{}_{}".format(label1, i): v for i, v in enumerate(file_list1.split(","),1)}
    d[label2] = {"{}_{}".format(label2, i): v for i, v in enumerate(file_list2.split(","),1)}
    return d

if __name__ == "__main__":
    # execute only if run as a script
    main()
