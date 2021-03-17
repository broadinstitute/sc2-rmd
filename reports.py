#!/usr/bin/env python3

__author__ = "dpark@broadinstitute.org"

import os
import sys
import subprocess
import argparse
import datetime

#import epiweeks
import pandas as pd
import numpy as np


def load_data(assemblies_tsv, collab_tsv, min_unambig, min_date, max_date):

    df_assemblies = pd.read_csv(assemblies_tsv, sep='\t')
    if collab_tsv and os.path.isfile(collab_tsv) and os.path.getsize(collab_tsv):
        collab_ids = pd.read_csv(collab_tsv, sep='\t')[list(['external_id', 'collaborator_id'])]
        collab_ids.columns = ['sample', 'collaborator_id']
    else:
        collab_ids = pd.DataFrame(columns = ['sample', 'collaborator_id']) 


    # format dates properly
    df_assemblies = df_assemblies.astype({'collection_date':np.datetime64,'run_date':np.datetime64})

    # subset by date range
    if min_date:
        df_assemblies = df_assemblies.loc[~df_assemblies['run_date'].isna() & (np.datetime64(min_date) <= df_assemblies['run_date'])]
    if max_date:
        df_assemblies = df_assemblies.loc[~df_assemblies['run_date'].isna() & (df_assemblies['run_date'] <= np.datetime64(max_date))]

    # fix missing data in purpose_of_sequencing
    df_assemblies.loc[:,'purpose_of_sequencing'] = df_assemblies.loc[:,'purpose_of_sequencing'].fillna('Missing').replace('', 'Missing')

    # derived column: genome_status
    df_assemblies.loc[:,'genome_status'] = list(
            'failed_sequencing' if df_assemblies.loc[id, 'assembly_length_unambiguous'] < min_unambig
            else 'failed_annotation' if df_assemblies.loc[id, 'vadr_num_alerts'] > 0
            else 'submittable'
            for id in df_assemblies.index)

    # derived columns: geo_country, geo_state, geo_locality
    df_assemblies.loc[:,'geo_country'] = list(g.split(': ')[0] if not pd.isna(g) else '' for g in df_assemblies.loc[:,'geo_loc_name'])
    df_assemblies.loc[:,'geo_state'] = list(g.split(': ')[1].split(', ')[0] if not pd.isna(g) else '' for g in df_assemblies.loc[:,'geo_loc_name'])
    df_assemblies.loc[:,'geo_locality'] = list(g.split(': ')[1].split(', ')[1] if not pd.isna(g) and ', ' in g else '' for g in df_assemblies.loc[:,'geo_loc_name'])

    # join column: collaborator_id
    df_assemblies = df_assemblies.merge(collab_ids, on='sample', how='left', validate='one_to_one')

    return df_assemblies


def main(args):

    df_assemblies = load_data(args.assemblies_tsv, args.collab_tsv, args.min_unambig, args.min_date, args.max_date)

    states_all = list(str(x) for x in df_assemblies['geo_state'].unique() if x and not pd.isna(x))
    collaborators_all = list(str(x) for x in df_assemblies['collected_by'].unique() if x and not pd.isna(x))
    purposes_all = list(str(x) for x in df_assemblies['purpose_of_sequencing'].unique() if x and not pd.isna(x))

    sequencing_lab_sanitized = args.sequencing_lab.replace(' ', '_')
    date_string = datetime.date.today().strftime("%Y_%m_%d")

    # the everything reports
    df_assemblies.to_excel('report-{}-everything-{}.xlsx'.format(
        sequencing_lab_sanitized, date_string),
        index=False, freeze_panes=(1,1),
        columns=[
        'sample',
        'collaborator_id',
        'biosample_accession',
        'pango_lineage',
        'nextclade_clade',
        'geo_loc_name',
        'run_date',
        'assembly_length_unambiguous',
        'amplicon_set',
        'vadr_num_alerts',
        'nextclade_aa_subs',
        'nextclade_aa_dels',
        'collected_by',
        'purpose_of_sequencing',
        'bioproject_accession',
        'genome_status',
        ])
    subprocess.check_call([
        'R', '--vanilla', '--no-save', '-e',
        """rmarkdown::render('/docker/covid_seq_report-everything.Rmd',
            output_file='report-{}-everything-{}.pdf',
            output_dir='./',
            params = list(
                assemblies_tsv = '{}',
                collab_ids_tsv = '{}',
                sequencing_lab = '{}',
                intro_blurb = '{}',
                {}
                min_date = '{}',
                min_unambig = {:d}))
        """.format(sequencing_lab_sanitized, date_string,
            args.assemblies_tsv, args.collab_tsv, args.sequencing_lab, args.intro_blurb,
            ("max_date = '{}', ".format(args.max_date) if args.max_date else ""), args.min_date, args.min_unambig),
        ])


    # per-state PDFs and XLSXs
    for state in states_all:
        print("making reports for state '{}'".format(state))
        state_sanitized = state.replace(' ', '_')
        subprocess.check_call([
            'R', '--vanilla', '--no-save', '-e',
            """rmarkdown::render('/docker/covid_seq_report-by_state.Rmd',
                output_file='report-{}-by_state-{}-{}.pdf',
                output_dir='./',
                params = list(
                    state = '{}',
                    assemblies_tsv = '{}',
                    collab_ids_tsv = '{}',
                    sequencing_lab = '{}',
                    intro_blurb = '{}',
                    {}
                    min_date = '{}',
                    min_unambig = {:d}))
            """.format(sequencing_lab_sanitized, state_sanitized, date_string,
                state, args.assemblies_tsv, args.collab_tsv, args.sequencing_lab, args.intro_blurb,
                ("max_date = '{}', ".format(args.max_date) if args.max_date else ""), args.min_date, args.min_unambig),
            ])

        df = df_assemblies.query('geo_state == "{}"'.format(state))
        df.to_excel('report-{}-by_state-{}-{}-per_sample.xlsx'.format(
            sequencing_lab_sanitized, state_sanitized, date_string),
            index=False, freeze_panes=(1,1),
            columns=[
            'sample',
            'collaborator_id',
            'biosample_accession',
            'pango_lineage',
            'nextclade_clade',
            'geo_loc_name',
            'run_date',
            'assembly_length_unambiguous',
            'amplicon_set',
            'vadr_num_alerts',
            'nextclade_aa_subs',
            'nextclade_aa_dels',
            'collected_by',
            'purpose_of_sequencing',
            'bioproject_accession',
            'genome_status',
            ])

    # per-collab PDFs and XLSXs
    for collab in collaborators_all:
        print("making reports for collaborator '{}'".format(collab))
        collab_sanitized = collab.replace(' ', '_')
        subprocess.check_call([
            'R', '--vanilla', '--no-save', '-e',
            """rmarkdown::render('/docker/covid_seq_report-by_collaborator.Rmd',
                output_file='report-{}-by_lab-{}-{}.pdf',
                output_dir='./',
                params = list(
                    collab = '{}',
                    assemblies_tsv = '{}',
                    collab_ids_tsv = '{}',
                    sequencing_lab = '{}',
                    intro_blurb = '{}',
                    {}
                    min_date = '{}',
                    min_unambig = {:d}))
            """.format(sequencing_lab_sanitized, collab_sanitized, date_string,
                collab, args.assemblies_tsv, args.collab_tsv, args.sequencing_lab, args.intro_blurb,
                ("max_date = '{}', ".format(args.max_date) if args.max_date else ""), args.min_date, args.min_unambig),
            ])

        df = df_assemblies.query('collected_by == "{}"'.format(collab))
        df.to_excel('report-{}-by_lab-{}-{}-per_sample.xlsx'.format(
            sequencing_lab_sanitized, collab_sanitized, date_string),
            index=False, freeze_panes=(1,1),
            columns=[
            'sample',
            'collaborator_id',
            'biosample_accession',
            'pango_lineage',
            'nextclade_clade',
            'geo_loc_name',
            'run_date',
            'assembly_length_unambiguous',
            'amplicon_set',
            'vadr_num_alerts',
            'nextclade_aa_subs',
            'nextclade_aa_dels',
            'collected_by',
            'purpose_of_sequencing',
            'bioproject_accession',
            'genome_status',
            ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate sequencing progress reports for collaborators and public health partners.')
    parser.add_argument('assemblies_tsv', help='Sample and assembly metadata tsv input')
    parser.add_argument('--collab_tsv', help='Collaborator ID tsv input')

    parser.add_argument('--sequencing_lab',
                        default='Sequencing Lab',
                        help='The name of the sequencing lab to be used in reports. (default: %(default)s)')
    parser.add_argument('--intro_blurb',
                        default='The Sequencing Lab is sequencing SARS-CoV-2 from patients.',
                        help='An introductory paragraph for the first page of the PDF reports. (default: %(default)s)')
    parser.add_argument('--min_date',
                        default='2020-01-01',
                        help='Report only on sequencing activity on or after this date. (default: %(default)s)')
    parser.add_argument('--max_date',
                        default=None,
                        help='Report only on sequencing activity on or before this date. (default: today)')
    parser.add_argument('--min_unambig',
                        type=int,
                        default=24000,
                        help='Threshold for considering a genome successful. (default: %(default)s)')

    args = parser.parse_args()
    main(args)
