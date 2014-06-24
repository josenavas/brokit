#!/usr/bin/env python
"""
Unit tests for the SortMeRNA version 2.0 Application controller
===============================================================
"""


from unittest import TestCase, main
import re
from os import close
from os.path import abspath, exists, getsize
from tempfile import mkstemp, mkdtemp

from brokit.sortmerna_v2 import (IndexDB,
                                 build_database_sortmerna,
                                 Sortmerna,
                                 sortmerna_ref_cluster)
from skbio.util.misc import remove_files
from skbio.parse.sequences import parse_fasta

# ----------------------------------------------------------------------------
# Copyright (c) 2014--, brokit development team
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------


# Test class and cases
class SortmernaV2Tests(TestCase):
    """ Tests for SortMeRNA version 2.0 functionality """

    def setUp(self):
        self.output_dir = '/tmp/'
        self.reference_seq_fp = reference_seqs_fp
        self.read_seqs_fp = read_seqs_fp

        # create temporary file with reference sequences defined
        # in reference_seqs_fp
        f, self.file_reference_seq_fp = mkstemp(prefix='temp_references_',
                                                suffix='.fasta')
        close(f)

        # write _reference_ sequences to tmp file
        tmp = open(self.file_reference_seq_fp, 'w')
        tmp.write(self.reference_seq_fp)
        tmp.close()

        # create temporary file with read sequences defined in read_seqs_fp
        f, self.file_read_seqs_fp = mkstemp(prefix='temp_reads_',
                                            suffix='.fasta')
        close(f)

        # write _read_ sequences to tmp file
        tmp = open(self.file_read_seqs_fp, 'w')
        tmp.write(self.read_seqs_fp)
        tmp.close()

        # list of files to remove
        self.files_to_remove = [self.file_reference_seq_fp,
                                self.file_read_seqs_fp]

    def tearDown(self):
        remove_files(self.files_to_remove)

    def test_indexdb_default_param(self):
    	""" Test indexing a database using SortMeRNA
        """
        sortmerna_db, db_files_to_remove = build_database_sortmerna(
            abspath(self.file_reference_seq_fp),
            max_pos=250,
            output_dir=self.output_dir)

        expected_db_files = set([sortmerna_db + ext
                                for ext in ['.bursttrie_0.dat', '.kmer_0.dat',
                                            '.pos_0.dat', '.stats']])

        # Make sure all db_files exist
        for fp in expected_db_files:
            self.assertTrue(exists(fp))

        # Add files to be remove
        (self.files_to_remove).extend(db_files_to_remove)

    def test_sortmerna_default_param(self):
        """ SortMeRNA version 2.0 reference OTU picking works with default settings
        """
        # rebuild the index
        sortmerna_db, db_files_to_remove = build_database_sortmerna(
            abspath(self.file_reference_seq_fp),
            max_pos=250,
            output_dir=self.output_dir)

        # Files created by indexdb_rna to be deleted
        (self.files_to_remove).extend(db_files_to_remove)

        # Run SortMeRNA
        clusters, failures, smr_files_to_remove = sortmerna_ref_cluster(
            self.file_read_seqs_fp,
            sortmerna_db,
            self.file_reference_seq_fp,
            self.output_dir,
            max_e_value=1,
            similarity=0.97,
            coverage=0.97,
            threads=1,
            tabular=False,
            best=1,
            HALT_EXEC=False)

        # Check all sortmerna output files exist
        output_files = [self.output_dir + ext
                        for ext in ['sortmerna_otus_otus.txt',
                                    'sortmerna_otus.log',
                                    'sortmerna_otus_denovo.fasta',
                                    'sortmerna_otus.fasta']]

        # File size (in bytes) for picked_otus_otus.txt, picked_otus.log,
        # picked_otus_denovo.fasta, picked_otus.fasta
        output_files_size = [346, 935, 3748, 7574]

        # Check output files have the correct size
        i = 0
        for fp in output_files:
            self.assertTrue(exists(fp))
            size = getsize(fp)
            self.assertTrue(size, output_files_size[i])
            i = i+1

        # Random reads that should not appear in any output file
        random_reads = ['simulated_random_reads.fa.000000000',
                        'simulated_random_reads.fa.000000001',
                        'simulated_random_reads.fa.000000002',
                        'simulated_random_reads.fa.000000003',
                        'simulated_random_reads.fa.000000004',
                        'simulated_random_reads.fa.000000005',
                        'simulated_random_reads.fa.000000006',
                        'simulated_random_reads.fa.000000007',
                        'simulated_random_reads.fa.000000008',
                        'simulated_random_reads.fa.000000009']

        # Reads passing E-value threshold and with similarity/coverage >=97%
        otu_reads = ['HMPMockV1.2.Staggered2.673827_47',
                     'HMPMockV1.2.Staggered2.673827_115',
                     'HMPMockV1.2.Staggered2.673827_122',
                     'HMPMockV1.2.Staggered2.673827_161',
                     'HMPMockV1.2.Staggered2.673827_180',
                     'HMPMockV1.2.Staggered2.673827_203',
                     'HMPMockV1.2.Staggered2.673827_207',
                     'HMPMockV1.2.Staggered2.673827_215',
                     'HMPMockV1.2.Staggered2.673827_218',
                     'HMPMockV1.2.Staggered2.673827_220']

        # Reads passing E-value threshold and with similarity/coverage <97%
        denovo_reads = ['HMPMockV1.2.Staggered2.673827_0',
                        'HMPMockV1.2.Staggered2.673827_1',
                        'HMPMockV1.2.Staggered2.673827_2',
                        'HMPMockV1.2.Staggered2.673827_3',
                        'HMPMockV1.2.Staggered2.673827_4',
                        'HMPMockV1.2.Staggered2.673827_5',
                        'HMPMockV1.2.Staggered2.673827_6',
                        'HMPMockV1.2.Staggered2.673827_7',
                        'HMPMockV1.2.Staggered2.673827_8',
                        'HMPMockV1.2.Staggered2.673827_9']

        # Check correct number of OTU clusters in file
        otu_clusters = ['295053']

        f_aligned = open(output_files[3], "U")
        f_otumap = open(output_files[0], "U")
        f_denovo = open(output_files[2], "U")

        # Verify the aligned FASTA file
        for label, seq in parse_fasta(f_aligned):
            id = label.split()[0]
            # Read is not random
            self.assertNotIn(id, random_reads)
            # Read is either in otu_reads or denovo_reads
            self.assertIn(id, otu_reads+denovo_reads)

        # Verify the de novo reads FASTA file
        for label, seq in parse_fasta(f_denovo):
            id = label.split()[0]
            # Read is not random
            self.assertNotIn(id, random_reads)
            # Read is not an OTU read
            self.assertNotIn(id, otu_reads)
            # Read is a de novo read
            self.assertIn(id, denovo_reads)

        # Check the OTU map
        for line in f_otumap:
            otu_entry = line.split()
            # Cluster ID is correct
            self.assertIn(otu_entry[0], otu_clusters)
            # Each read in the cluster must exclusively be an OTU read
            for read in otu_entry[1:]:
                self.assertNotIn(read, random_reads)
                self.assertNotIn(read, denovo_reads)
                self.assertIn(read, otu_reads)

        # Check returned list of lists of clusters
        expected_cluster = ['HMPMockV1.2.Staggered2.673827_47',
                            'HMPMockV1.2.Staggered2.673827_115',
                            'HMPMockV1.2.Staggered2.673827_122',
                            'HMPMockV1.2.Staggered2.673827_161',
                            'HMPMockV1.2.Staggered2.673827_180',
                            'HMPMockV1.2.Staggered2.673827_203',
                            'HMPMockV1.2.Staggered2.673827_207',
                            'HMPMockV1.2.Staggered2.673827_215',
                            'HMPMockV1.2.Staggered2.673827_218',
                            'HMPMockV1.2.Staggered2.673827_220']

        # Should only have 1 cluster
        self.assertEqual(1, len(clusters))
        for actual_cluster in clusters:
            actual_cluster.sort()
            expected_cluster.sort()
            self.assertEqual(actual_cluster, expected_cluster)

        # Check log file number of clusters and failures corresponds to
        # the results in the output files
        f_log = open(output_files[1], "U")
        num_clusters = 0
        num_failures = 0
        for line in f_log:
            if "Total OTUs" in line:
                num_clusters = (re.split('Total OTUs = ', line)[1]).strip()
            elif "non-aligned reads" in line:
                num_failures = (re.split('non-aligned reads = | \(',
                                         line)[1]).strip()

        self.assertEqual(int(num_clusters), len(otu_clusters))
        self.assertEqual(int(num_failures), len(denovo_reads))

        # Files created sortmerna to be deleted (StdErr and StdOut were already
        # removed in sortmerna_ref_cluster)
        (self.files_to_remove).extend(output_files)

# Reference sequence database
reference_seqs_fp = """>426848
AGAGTTTGATCCTGGCTCAGGATGAACGCTAGCGGCAGGCTTAATACATGCAAGTCGAGGGGCAGCACTGGTAGCAATAC
CTGGTGGCGACCGGCGGACGGGTGCGTAACACGTATGCAACCTACCCTGTACAGGGGGATAGCCCGAGGAAATTCGGATT
AATACCCCATACGATAAGAATCGGCATCGATTTTTATTGAAAGCTCCGGCGGTACAGGATGGGCATGCGCCCCATTAGCT
AGTTGGTGAGGTAACGGCTCACCAAGGCTACGATGGGTAGGGGGCCTGAGAGGGTGATCCCCCACACTGGAACTGAGACA
CGGTCCAGACTCCTACGGGAGGCAGCAGTAAGGAATATTGGTCAATGGGCGCAAGCCTGAACCAGCCATGCCGCGTGCAG
GAAGACTGCCATTATGGTTGTAAACTGCTTTTATATGGGAAGAAACCTCCGGACGTGTCCGGAGCTGACGGTACCATGTG
AATAAGGATCGGCTAACTCCGTGCCAGCAGCCGCGGTAATACGGAGGATCCAAGCGTTATCCGGATTTATTGGGTTTAAA
GGGTGCGTAGGCGGCGTGTTAAGTCAGAGGTGAAATTCGGCAGCTCAACTGTCAAATTGCCTTTGATACTGGCACACTTG
AATGCGATTGAGGTAGGCGGAATGTGACATGTAGCGGTGAAATGCTTAGACATGTGACAGAACACCGATTGCGAAGGCAG
CTTACCAAGTCGTTATTGACGCTGAGGCACGAAAGCGTGGGGAGCAAACAGGATTAGATACCCTGGTAGTCCACGCCGTA
AACGATGATAACTCGACGTTAGCGATACACTGTTAGCGTCCAAGCGAAAGCGTTAAGTTATCCACCTGGGAAGTACGATC
GCAAGGTTGAAACTCAAAGGAATTGACGGGGGCCCGCACAAGCGGTGGAGCATGTGGTTTAATTCGATGATACGCGAGGA
ACCTTACCAGGGCTTAAATGGGGAACGACCTTCTGGGAAACCAGAATTTCTTTTAGACGGTCCTCAAGGTGCTGCATGGT
TGTCGTCAGCTCGTGCCGTGAGGTGTTGGGTTAAGTCCCGCAACGAGCGCAACCCCTACTGTTAGTTGCCAGCGGATAAT
GCCGGGGACTCTAGCGGAACTGCCTGTGCAAACAGAGAGGAAGGTGGGGATGACGTCAAATCATCACGGCCCTTACGTCC
TGGGCTACACACGTGCTACAATGGCCGGTACAGAGGGCAGCCACTTCGTGAGAAGGAGCGAATCCTTAAAGCCGGTCTCA
GTTCGGATTGTAGTCTGCAACTCGACTACATGAAGCTGGAATCGCTAGTAATCGCGTATCAGCCATGACGCGGTGAATAC
GTTCCCGGGCCTTGTACACACCGCCCGTCAAGCCATGGGAATTGGGAGTACCTAAAGTCGGTAACCGCAAGGAGCCGCCT
AAGGTAATACCAGTGACTGGGGCTAAGTCGTAACAAGGTAGCCGTA
>42684
AGAGTTTGATCCTGGCTCAGATTGAACGCTGGCGGCATGCTTTACACATGCAAGTCGGACGGCAGCACAGAGGAGCTTGC
TTCTTGGGTGGCGAGTGGCGAACGGGTGAGTGACGCATCGGAACGTACCGAGTAATGGGGGATAACTGTCCGAAAGGACA
GCTAATACCGCATACGCCCTGAGGGGGAAAGCGGGGGATCTTAGGACCTCGCGTTATTCGAGCGGCCGATGTCTGATTAG
CTGGTTGGCGGGGTAAAGGCCCACCAAGGCGACGATCAGTAGCGGGTCTGAGAGGATGATCCGCCACACTGGGACTGAGA
CACGGCCCAGACTCCTACGGGAGGCAGCAGTGGGGAATTTTGGACAATGGGCGCAAGCCTGATCCAGCCATGCCGCGTGT
CTGAAGAAGGCCTTCGGGTTGTAAAGGACTTTTGTCAGGGAAGAAAAGGAACGTGTTAATACCATGTTCTGATGACGGTA
CCTGAAGAATAAGCACCGGCTAACTACGTGCCAGCAGCCGCGGTAATACGTAGGGTGCGAGCGTTAATCGGAATTACTGG
GCGTAAAGCGGGCGCAGACGGTTACTTAAGCGGGATGTGAAATCCCCGGGCTCAACCCGGGAACTGCGTTCCGAACTGGG
TGGCTAGAGTGTGTCAGAGGGGGGTAGAATTCCACGTGTAGCAGTGAAATGCGTAGAGATGTGGAGGAATACCGATGGCG
AAGGCAGCCCCCTGGGATAACACTGACGTTCATGCCCGAAAGCGTGGGTAGCAAACAGGGTTAGATACCCTGGTAGTCCA
CGCCCTAAACGATGTCGATTAGCTGTTGGGGCACTTGATGCCTTAGTAGCGTAGCTAACGCGTGAAATCGACCGCCTGGG
GAGTACGGTCGCAAGATTAAAACTCAAAGGAATTGACGGGGACCCGCACAAGCGGTGGATGATGTGGATTAATTCGATGC
AACGCGAAGAACCTTACCTGGTCTTGACATGTACGGAATCTTCCAGAGACGGAAGGGTGCCTTCGGGAGCCGTAACACAG
GTGCTGCATGGCTGTCGTCAGCTCGTGTCGTGAGATGTTGGGTTAAGTCCCGCAACGAGCGCAACCCTTGTCATTAGTTG
CCATCACTTGGTTGGGCACTCTAATGAGACTGCCGGTGACAAACCGGAGGAAGGTGGGGATGACGTCAAGTCCTCATGGC
CCTTATGACCAGGGCTTCACACGTCATACAATGGTCGGTACAGAGGGTAGCCAAGCCGCGAGGCGGAGCCAATCCCAGAA
AACCGATCGTAGTCCGGATTGCACTCTGCAACTCGAGTGCATGAAGTCGGAATCGCTAGTAATCGCAGGTCAGCATACTG
CGGTGAATACGTTCCCGGGTCTTGTACACACCGCCCGTCACACCATGGGAGTGGGGGATACCAGAAGCAGGTAGGCTAAC
CGCAAGGAGGCCGCTTGCCACGGTATGCTTCATGACTGGGGTGAAGTCGTAACAAGGTAAC
>342684
AGAGTTTGATCCTGGCTCAGGATGAACGCTAGCGGCAGGCTTAACACATGCAAGTCGAGGGGCATCGCGGGTAGCAATAC
CTGGCGGCGACCGGCGGAAGGGTGCGTAACGCGTGAGCGACATACCCGTGACAGGGGGATAACAGATGGAAACGTCTCCT
AATACCCCATAAGATCATATATCGCATGGTATGTGATTGAAAGGTGAGAACCGGTCACGGATTGGCTCGCGTCCCATCAG
GTAGACGGCGGGGCAGCGGCCCGCCGTGCCGACGACGGGTAGGGGCTCTGAGAGGAGTGACCCCCACAATGGAACTGAGA
CACGGTCCATACTCCTACGGGAGGCAGCAGTGAGGAATATTGGTCAATGGGCGGAAGCCTGAACCAGCCATGCCGCGTGC
GGGAGGACGGCCCTATGGGTTGTAAACCGCTTTTGAGTGAGAGCAATAAGGTTCACGTGTGGACCGATGAGAGTATCATT
CGAATAAGCATCGGCTAACTCCGTGCCAGCAGCCGCGGTAATACGGAGGATGCGAGCGTTATCCGGATTCATTGGGTTTA
AAGGGTGCGTAGGCGGACATGTAAGTCCGAGGTGAAAGACCGGGGCCCAACCCCGGGGTTGCCTCGGATACTGTGTGTCT
GGAGTGGACGTGCCGCCGGGGGAATGAGTGGTGTAGCGGTGAAATGCATAGATGTCACTCAGAACACCGATTGCGAAGGC
ACCTGGCGAATGTCTTACTGACGCTGAGGCACGAAAGCGTGGGGATCGAACAGGATTAGATACCCTGGTAGTCCACGCAG
TAAACGATGATGGCTGTCCGTTCGCTCCGATAGGAGTGAGTAGACAAGCGAAAGCGCTAAGCCATCCACCTGGGGAGTAC
GGCCGCAAGGCTGAAACTCAAAGGAATTGACGGGGGCCCGCACAAGCGGAGGAACATGTGGTTTAATTCGATGATACGCG
AGGAACCTTACCCGGGCTCGAACGGCAGGTGAACGATGCAGAGATGCAAAGGCCCTTCGGGGCGTCTGTCGAGGTGCTGC
ATGGTTGTCGTCAGCTCGTGCCGTGAGGTGTCGGCTCAAGTGCCATAACGAGCGCAACCCTTGCCTGCAGTTGCCATCGG
GTAAAGCCGGGGACTCTGCAGGGACTGCCACCGCAAGGTGAGAGGAGGGGGGGGATGACGTCAAATCAGCACGGCCCTTA
CGTCCGGGGCGACACACGTGTTACAATGGCGGCCACAGCGGGAAGCCACCCAGTGATGGGGCGCGGATCCCAAAAAAGCC
GCCTCAGTTCGGATCGGAGTCTGCAACCCGACTCCGTGAAGCTGGATTCGCTAGTAATCGCGCATCAGCCATGGCGCGGT
GAATACGTTCCCGGGCCTTGTACACACCGCCCGTCAAGCCATGGGAGTCGTGGGCGCCTGAAGGCCGTGACCGCGAGGAG
CGGCCTAGGGCGAACGCGGTGACTGGGGCTAAGTCGTAACAAGGTA
>295053
AGAGTTTGATCCTGGCTCAGGACGAACGCTGGCGGCGTGCCTAACACATGCAAGTCGAACGGAGATGCTCCTTCGGGAGT
ATCTTAGTGGCGAACGGGTGAGTAACGCGTGAGCAACCTGACCTTCACAGGGGGATAACCGCTGGAAACAGCAGCTAATA
CCGCATAACGTCGCAAGACCAAAGAGGGGGACCTTCGGGCCTCTTGCCATCGGATGTGCCCAGATGGGATTAGCTTGTTG
GTGGGGTAACGGCTCACCAAGGCGACGATCCCTAGCTGGTCTGAGAGGATGACCAGCCACACTGGAACTGAGACACGGTC
CAGACTCCTACGGGAGGCAGCAGTGGGGAATATTGCACAATGGGCGCAAGCCTGATGCAGCCATGCCGCGTGTATGAAGA
AGGCCTTCGGGTTGTAAAGTACTTTCAGCGGGGAGGAAGGGAGTAAAGTTAATACCTTTGCTCATTGACGTTACCCGCAG
AAGAAGCACCGGCTAACTCCGTGCCAGCAGCCGCGGTAATACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAA
GCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCCCCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTG
AGTCTCGTAGAGGGGGGTAGAATTCCAGGTGTAGCGGTGAAATGCGTAGAGATCTGGAGGAATACCGGTGGCGAAGGCGG
CCCCCTGGACGAAGACTGACGCTCAGGTGCGAAAGCGTGGGGAGCAAACAGGATTAGATACCCTGGTAGTCCACGCCGTA
AACGATGTCGACTTGGAGGTTGTGCCCTTGAGGCGTGGCTTCCGGAGCTAACGCGTTAAGTCGACCGCCTGGGGAGTACG
GCCGCAAGGTTAAAACTCAAATGAATTGACGGGGGCCCGCACAAGCGGTGGAGCATGTGGTTTAATTCGATGCAACGCGA
AGAACCTTACCTGGTCTTGACATCCACAGAACTTTCCAGAGATGGATTGGTGCCTTCGGGAACTGTGAGACAGGTGCTGC
ATGGCTGTCGTCAGCTCGTGTTGTGAAATGTTGGGTTAAGTCCCGCAACGAGCGCAACCCTTGTCCTTTGTTGCCAGCGG
TCCGGCCGGGAACTCAAAGGAGACTGCCAGTGATAAACTGGAGGAAGGTGGGGATGACGTCAAGTCATCATGGCCCTTAC
GACCAGGGCTACACACGTGCTACAATGGCGCATACAAAGAGAAGCGACCTCGCGAGAGCAAGCGGACCTCATAAAGTGCG
TCGTAGTCCGGATTGGAGTCTGCAACTCGACTCCATGAAGTCGGAATCGCTAGTAATCGTGGATCAGAATGCCACGGTGA
ATACGTTCCCGGGCCTTGCACACACCGCC
>879972
GACGAACGCTGGCGGCGTGCCTAATACATGCAAGTCGAACGAGATTGACCGGTGCTTGCACTGGTCAATCTAGTGGCGAA
CGGGTGAGTAACACGTGGGTAACCTGCCCATCAGAGGGGGATAACATTCGGAAACGGATGCTAAAACCGCATAGGTCTTC
GAACCGCATGGTTTGAAGAGGAAAAGAGGCGCAAGCTTCTGCTGATGGATGGACCCGCGGTGTATTAGCTAGTTGGTGGG
GTAACGGCTCACCAAGGCGACGATACATAGCCGACCTGAGAGGGTGATCGGCCACACTGGGACTGAGACACGGCCCAGAC
TCCTACGGGAGGCAGCAGTAGGGAATCTTCGGCAATGGACGGAAGTCTGACCGAGCAACGCCGCGTGAGTGAAGAAGGTT
TTCGGATCGTAAAGCTCTGTTGTAAGAGAAGAACGAGTGTGAGAGTGGAAAGTTCACACTGTGACGGTATCTTACCAGAA
AGGGACGGCTAACTACGTGCCAGCAGCCGCGGTAATACGTAGGTCCCGAGCGTTGTCCGGATTTATTGGGCGTAAAGCGA
GCGCAGGCGGTTAGATAAGTCTGAAGTTAAAGGCTGTGGCTTAACCATAGTACGCTTTGGAAACTGTTTAACTTGAGTGC
AAGAGGGGAGAGTGGAATTCCATGTGTAGCGGTGAAATGCGTAGATATATGGAGGAACACCGGTGGCGAAAGCGGCTCTC
TGGCTTGTAACTGACGCTGAGGCTCGAAAGCGTGGGGAGCAAACAGGATTAGATACCCTGGTAGTCCACGCCGTAAACGA
TGAGTGCTAGGTGTTAGACCCTTTCCGGGGTTTAGTGCCGCAGCTAACGCATTAAGCACTCCGCCTGGGGAGTACGACCG
CAGGGTTGAAACTCAAAGGAATTGACGGGGGCCCGCACAAGCGGTGGAGCATGTGGTTTAATTCGAAGCAACGCGAAGAA
CCTTACCAGGTCTTGACATCCCTCTGACCGCTCTAGAGATAGAGCTTTCCTTCGGGACAGAGGTGACAGGTGGTGCATGG
TTGTCGTCAGCTCGTGTCGTGAGATGTTGGGTTAAGTCCCGCAACGAGCGCAACCCCTATTGTTAGTTGCCATCATTCAG
TTGGGCACTCTAGCGAGACTGCCGGTAATAAACCGGAGGAAGGTGGGGATGACGTCAAATCATCATGCCCCTTATGACCT
GGGCTACACACGTGCTACAATGGCTGGTACAACGAGTCGCAAGCCGGTGACGGCAAGCTAATCTCTTAAAGCCAGTCTCA
GTTCGGATTGTAGGCTGCAACTCGCCTACATGAAGTCGGAATCGCTAGTAATCGCGGATCAGCACGCCGCGGTGAATACG
TTCCCGGGCCT
"""

# Reads to search against the database
# - 10 rRNA reads:   amplicon reads were taken from Qiime study 1685
# - 10 random reads: simulated using mason with the following command:
#     mason illumina -N 10 -snN -o simulated_random_reads.fa -n
#     150 random.fasta
# - 10 rRNA reads with id < 97: amplicon reads were taken from
#   Qiime study 1685
read_seqs_fp = """>HMPMockV1.2.Staggered2.673827_47 M141:79:749142:1:1101:16169:1589
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCAAGCAGGCGGTTTGTTAAGTCAGATGTGAAATCCCCGGGCTCAACCTGGGAACTGCATTTGATACTGGCAAGCTTGAGTCTCGTAGAGGAGGGTAGAATTCCAGG
TGTAGCGGGGAAATGCGTAGAGATCTGGAGGAATACCGGTGGCGAAGGCGGCTCCATGGACGAAGACTGACGCT
>HMPMockV1.2.Staggered2.673827_115 M141:79:749142:1:1101:14141:1729
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCCCCCGGCTCAACCTTGGAACTGCATCTGATACGGGCAAGCTTGAGTCTCGTAGAGGGGGGTAGAATTCCAGG
TGTAGCGGTGAAATGCGTAGAGATCTGGAGGAATACCGGTGGCGAAGGCGGCCCTCTGGACGAAGACTGACGCTCAGGTGCGAAAGCGTGGGGAGCAAACA
>HMPMockV1.2.Staggered2.673827_122 M141:79:749142:1:1101:16032:1739
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCCCCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGTAGAATTCCAGG
TGTAGCGGTGAAATGCGTAGAGATCTGGAGGAATACCGGTGGCGAAGGCGGCCCCCTGGACGAAGACTGACGCTCAGGTGCGAAAGCGTGGTGATCAAACA
>HMPMockV1.2.Staggered2.673827_161 M141:79:749142:1:1101:17917:1787
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCCCCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGTAGAATTCCAGG
TGTAGCGGTGAAATGCGTAGAGATCTGGAGGAATACCGGTGGCGAAGGCGGCTCCCTGGACGAAGACTGACGCTCAGGTGCGAAAGCGTGGGGAGCAAACA
>HMPMockV1.2.Staggered2.673827_180 M141:79:749142:1:1101:16014:1819
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGTGGTTTGTTAAGTCAGATGTGAAATCCCCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGTAGAATTCCAGG
TGTAGCGGTGAAATGCGTAGAGATCTGGAGGAATACCGGTGGCGAAGGCGGCCCCCTGGACGAAGACTGACGCTCAGGTGCGAAAGCGTG
>HMPMockV1.2.Staggered2.673827_203 M141:79:749142:1:1101:17274:1859
TACGGAGGTTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCCCCCGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGTAGAATTCCAGG
TGTAGCGGTGAAATGCGTAGAGATCTGGAGGAATACCGGTGGCGAAGGCGGCCTCCTGGACGAAGACTGACGCTCAGGTGCGAAAGCGTGGGGATCAAACA
>HMPMockV1.2.Staggered2.673827_207 M141:79:749142:1:1101:17460:1866
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCCCCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGTAGAATTCCAGG
TGTAGCGGTGAAATGCGTAGAGATCTGGAGGAATACCGGTGGCGAAGGCGGCCCCCTGGACGAAGACTGACGCTCAGGTGCGAAAGCGTGGGGAGCAAACA
>HMPMockV1.2.Staggered2.673827_215 M141:79:749142:1:1101:18390:1876
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCCCCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGTAGAATTCCAGG
TGTAGCGGTGAAATGCGTAGAGATCTGGAGGAATACCGGTGGCGAAGGCGGCCCCCTGGACGAAGACTGACG
>HMPMockV1.2.Staggered2.673827_218 M141:79:749142:1:1101:18249:1879
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCCCCGGGCTCAACCTGGGAACTTCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGTAGAATTCCAGG
TGTAGCGGTGAAATGCGTAGAGATCTGGAGGAATACCGGTGGCGAAGGCGGCCCCCTGGACGAAGACTGACGCTCAGGTGCGAAAGCGTGGGGAGCACACA
>HMPMockV1.2.Staggered2.673827_220 M141:79:749142:1:1101:15057:1880
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCCCCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGTAGAATTCCAGG
TGTAGCGGTGAAATGCGTAGAGATCTGGAGGAATACCGGTGGCGAAGGCGGCCTCCTGGACGAAGACTGACGCTC
>simulated_random_reads.fa.000000000
AGCCGGGTGTCTACGGTCAGGTGTGTTCTGACTACGTAGTTTGACAGCACGTGTCCTTTCCCCTTCCCAAGGTAACGAATTGTCGTTATCAACGTTTCGATCCGTAATTTCACGGAACGACATAAAGGCATCAATACTATCGCCAACAGA
>simulated_random_reads.fa.000000001
GTGGACGTCGTGGCGGCGTACTAACTTCCTACAGGCATATCCGGAATAACATTCTGCCGCTTGTCGACATAAGCTGTTCCCTACATAGACGACGACGGTTGAAGGGTGTATGTATTCTTTGGGTACGGCTCCTCTGGGCGCATGGTAGCA
>simulated_random_reads.fa.000000002
CATTCTTTATAGGCCTACAACACTAATCATCGTTAAGCATAAGGGGAGGAGTGTGCGTGGCATCAAGTCCTGGTTCTTCGCCTAGTACCACACCGTCTCACACGCAGCCGCCGACGACCAGTGAGGGCGCGTGGGACACCCATTCGGTCC
>simulated_random_reads.fa.000000003
TCGCCTTGGTACAAACAGTCGCGGCACGCTGTATGGAGGACCATAGAGGCACAGGCTGAGGACAGGGGCATGGAAGGTTCAATCGCCCCCCACAGCTTTAGGTAGGAAGTACTGTTCTAGTGCCAATTTGATTTTAACGGCAGTTACTCG
>simulated_random_reads.fa.000000004
CATATTCTAATATCCTACTTCTGATACCCGATTATACACGACACCACCCCAGGACTGTCGTCACATCCTTATCTGGATAAACATCCGGTTCCGTTTGGCCGTGCTCCGCAAGTGATGCGTCTGTGGAATGTACGTGGAGCGTTGACAGTT
>simulated_random_reads.fa.000000005
CCGGATTAGGCATGTTTATAGTACAACGGATTCGCAAAAAGGTCAGGGTAACAATTTTGAAATGCTTTCATACTGCGGTCTAAATGGACCACCCTTTAGGTGCAGCCAACTATAGTTGGTCGATTCTCTGAACACGTACCGAAGGCAATT
>simulated_random_reads.fa.000000006
AACCCATCGGAATAATCTACTGCTTCGTATGGAACGGTCCTACATTTAAATAAACGTGTCCAGTGCCACCCGATACCTCTCGTCAATCAGGGGCTCTCCCTGAATCAGCAGTAAACAAACCCAGTACACTGTCGAACACTACTGAGACCG
>simulated_random_reads.fa.000000007
CCGAAGGCAAGTCTGTCGTAGAATGGTTTTTGTCGTTGTAACAACCCCGCTCTAGACCCTGAAAACCATAAAGTCAAGCCCAACTAATATTAGAGGCATTCTGGCTACTCCCGCTCACCGCAATCTTCACATACTGTGATACCCTCAGCC
>simulated_random_reads.fa.000000008
ATATCCGTTAAACCCCGGATTTGACAATTCATCATCAACGCTACTAACGGCTTTCTCAATTTGGGGCTGTGGCCTATCCGCATACGGCTACCTGCGCAAGAAGAGAGTACTGTTAGATGTCACGCTGCACTTGCGAAGACCGGTGGGCGT
>simulated_random_reads.fa.000000009
AGCGATGAGTACACAAGATGAGTGAAGGGATTAAACTTCAAACCTTGAAGTGTTACCCGATTTCCTACCATTGGGGATTCGTTAATGCTTCGAATGGATCTATATCCGGTGTTTAGCTGACTGTTAAAATACTCTCGTTGTACGAAAGTA
>HMPMockV1.2.Staggered2.673827_0 M141:79:749142:1:1101:17530:1438
TACGTAGGTGGCAAGCGTTATCCGGAATTATTGGGCGCAAAGCGCGCGTAGGCGGTTTTTTAAGTCTGATGTGAAAGCCCACGGCTCAACCGTGGAGGGTCATTGGAAACTGGAAAACTTGAGTGCAGAAGAGGAAAGTGGAATTCCATG
TGTAGCGGTGAAATGCGCAGAGATATGGAGGAACACCAGTGGCGAAGGCGACCTTCTGGTCTGTAACTGACGCTGATGTGCGAAAGCGTG
>HMPMockV1.2.Staggered2.673827_1 M141:79:749142:1:1101:17007:1451
TACGTAGGTGGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGCGCGTAGGCGGTTTTTTAAGTCTGATGTGAAAGCCCACGGCTCAACCGTGGAGGGTCATTGGAAACTGGAAAACTTGAGTGCAGAAGAGGAAAGTGGAATTCCATG
TGTAGCGGTGAAATGCGCAGAGATATGGAGGAACACCAGTGGCGAAGGCGACTTTCTGGTCTGTAACTTACGCTG
>HMPMockV1.2.Staggered2.673827_2 M141:79:749142:1:1101:16695:1471
TACGTAGGTGGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGCGCGTAGGCGGTTTTTTAAGTCTGATGTGAAAGCCCACGGCTCAACCGTGGAGGGTCATTGGAAACTGGAAAACTTGAGTGCAGAAGAGGAAAGTGGAATTCCATG
TGTAGCGGTGAAATGCGCAGAGATATGGAGGAACACCAGTGGCGAAGGCGACTTTCTGGTCTGTAACTGACGCTGATGTGCGAAAGCGTGGGGA
>HMPMockV1.2.Staggered2.673827_3 M141:79:749142:1:1101:17203:1479
TACGTAGGTGGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGCGCGTAGGCGGTTTTTTAAGTCTGATGTGAAAGCCCACGGCTCAACCGTGGAGGGTCATTGGAAACTGGAAAACTTGAGTGCAGAAGAGGAAAGTGGAATTCCATG
TGTAGCGGTGAAATGCGTAGAGATATGGAGGAACACCAGTGGCGAAGGCGACGTTCTGGTCTGTAACTGACGCTGATGTGCGAAAGCGTGG
>HMPMockV1.2.Staggered2.673827_4 M141:79:749142:1:1101:14557:1490
TACGTAGGTGGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGCGCGTAGGCGGTTTTTTAAGTCTGATGTGAAAGCCCACGGCTCAACCGTGGAGGGTCATTGGAAACTGGAAAACTTGAGTGCAGAAGAGGAAAGTGGAATTCCATG
TGTAGCGGTGAAATGCGCAGAGATATGGAGGAACACCAGTGGCGAAGGCGACTTTCTGGGCTGTAACTGACGCTGATGTGCGCAAGCGTGGTGATCAAACA
>HMPMockV1.2.Staggered2.673827_5 M141:79:749142:1:1101:16104:1491
TACGTAGGTGGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGCGCGTAGGCGGTTTTTTAAGTCTGATGTGAAAGCCCACGGCTCAACCGTGGAGGGTCATTGGAAACTGGAAAACTTGAGTGCAGAAGAGGAAAGTGGAATTCCATG
TGTAGCGGTGAAATGCGCAGAGATATGGAGGAACACCAGTGGCGAAGGCGACTTTCTGGTCTGTAACTGACGC
>HMPMockV1.2.Staggered2.673827_6 M141:79:749142:1:1101:16372:1491
TACGTAGGTGGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGCGCGTAGGCGGTTTTTTAAGTCTGATGTGAAAGCCCACGGCTCAACCGTGGAGGGTCATTGGAAACTGGAAAACTTGAGTGCAGAAGAGGAAAGTGGAATTCCATG
TGTAGCGGTGAAATGCGCAGAGATATGGAGGAACAACAGTGGCGAAGGCGACTTTCTGGTCTGTAACTGACGCTGATGTGCGTAAG
>HMPMockV1.2.Staggered2.673827_7 M141:79:749142:1:1101:17334:1499
TACGTAGGTGGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGCGCGTAGGCGGTTTTTTAAGTCTGATGTGAAAGCCCACGGCTCAACCGTGGAGGGTCATTGGAAACTGGAAAACTTGAGTGCAGAAGAGGAAAGTGGAATTCCATG
TGTAGCGGTGAAATGCGCAGAGATATGGAGGAACACCAGTGGCGAAGGCGACTTTCTGGTCTGTAACTGACGCTGATGT
>HMPMockV1.2.Staggered2.673827_8 M141:79:749142:1:1101:17273:1504
TACGTAGGTGGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGCGCGTAGGCGGTTTTTTAAGTCTGATGTGAAAGCCCACGGCTCAACCGTGGAGGGTCATTGGAAACTGGAAAACTTGAGTGCAGAAGAGGAAAGTGGAATTCCATG
TGTAGCGGTGAAATGCACAGAGATATGGAGGAACACCAGTGGCGAAGGCGACTTTCTGGTCTGTAACTGACGCTGA
>HMPMockV1.2.Staggered2.673827_9 M141:79:749142:1:1101:16835:1505
TACGTAGGTGGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGCGCGTAGGCGGTTTTTTAAGTCTGATGTGAAAGCCCACGGCTCAACCGTGGAGGGTCATTGGAAACTGGAAAACTTGAGTGCAGAAGAGGAAAGTGGAATTCCATG
TGTAGCGGTGACATGCGCAGAGATATGGAGGAACACCAGTGGCGAAGGCGACTTTCTGGTCTGTAACTGACGCTGATGTGCGAAAGCGTGGGGAT
"""


if __name__ == '__main__':
    main()
