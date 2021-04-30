#!/usr/bin/env python3

__author__ = "dpark@broadinstitute.org"

import os
import os.path
import sys
import subprocess
import argparse
import datetime

import epiweeks
import pandas as pd
import numpy as np


def load_data(assemblies_tsv, collab_tsv, min_unambig, min_date, max_date):

    df_assemblies = pd.read_csv(assemblies_tsv, sep='\t').dropna(how='all')
    if collab_tsv and os.path.isfile(collab_tsv) and os.path.getsize(collab_tsv):
        collab_ids = pd.read_csv(collab_tsv, sep='\t').dropna(how='all')[list(['external_id', 'collaborator_id'])]
        collab_ids.columns = ['sample', 'collaborator_id']
    else:
        collab_ids = None

    # format dates properly
    df_assemblies = df_assemblies.loc[
        ~df_assemblies['run_date'].isna() &
        ~df_assemblies['collection_date'].isna() &
        (df_assemblies['run_date'] != 'missing') &
        (df_assemblies['collection_date'] != 'missing')]
    df_assemblies = df_assemblies.astype({'collection_date':'datetime64[D]','run_date':'datetime64[D]'})

    # fix vadr_num_alerts
    df_assemblies = df_assemblies.astype({'vadr_num_alerts':'Int64'})

    # remove columns with File URIs
    cols_unwanted = [
        'assembly_fasta','coverage_plot','aligned_bam','replicate_discordant_vcf',
        'variants_from_ref_vcf','nextclade_tsv','nextclade_json',
        'pangolin_csv','vadr_tgz','vadr_alerts',
    ]
    cols_unwanted = list(c for c in cols_unwanted if c in df_assemblies.columns)
    df_assemblies.drop(columns=cols_unwanted, inplace=True)

    # subset by date range
    if min_date:
        df_assemblies = df_assemblies.loc[~df_assemblies['run_date'].isna() & (np.datetime64(min_date) <= df_assemblies['run_date'])]
    if max_date:
        df_assemblies = df_assemblies.loc[~df_assemblies['run_date'].isna() & (df_assemblies['run_date'] <= np.datetime64(max_date))]

    # fix missing data in purpose_of_sequencing
    df_assemblies.loc[:,'purpose_of_sequencing'] = df_assemblies.loc[:,'purpose_of_sequencing'].fillna('Missing').replace('', 'Missing')

    # derived column: genome_status
    if 'genome_status' not in df_assemblies.columns:
        df_assemblies.loc[:,'genome_status'] = list(
            'failed_sequencing' if df_assemblies.loc[id, 'assembly_length_unambiguous'] < min_unambig
            else 'failed_annotation' if df_assemblies.loc[id, 'vadr_num_alerts'] > 0
            else 'submittable'
            for id in df_assemblies.index)

    # derived columns: geo_country, geo_state, geo_locality
    if 'geo_country' not in df_assemblies.columns:
        df_assemblies.loc[:,'geo_country'] = list(g.split(': ')[0] if not pd.isna(g) else '' for g in df_assemblies.loc[:,'geo_loc_name'])
    if 'geo_state' not in df_assemblies.columns:
        df_assemblies.loc[:,'geo_state'] = list(g.split(': ')[1].split(', ')[0] if not pd.isna(g) else '' for g in df_assemblies.loc[:,'geo_loc_name'])
    if 'geo_locality' not in df_assemblies.columns:
        df_assemblies.loc[:,'geo_locality'] = list(g.split(': ')[1].split(', ')[1] if not pd.isna(g) and ', ' in g else '' for g in df_assemblies.loc[:,'geo_loc_name'])

    # derived columns: collection_epiweek, run_epiweek
    if 'collection_epiweek' not in df_assemblies.columns:
        df_assemblies.loc[:,'collection_epiweek'] = list(epiweeks.Week.fromdate(x) if not pd.isna(x) else x for x in df_assemblies.loc[:,'collection_date'])
    if 'run_epiweek' not in df_assemblies.columns:
        df_assemblies.loc[:,'run_epiweek'] = list(epiweeks.Week.fromdate(x) if not pd.isna(x) else x for x in df_assemblies.loc[:,'run_date'])
    if 'collection_epiweek_end' not in df_assemblies.columns:
        df_assemblies.loc[:,'collection_epiweek_end'] = list(x.enddate().strftime('%Y-%m-%d') if not pd.isna(x) else '' for x in df_assemblies.loc[:,'collection_epiweek'])
    if 'run_epiweek_end' not in df_assemblies.columns:
        df_assemblies.loc[:,'run_epiweek_end'] = list(x.enddate().strftime('%Y-%m-%d') if not pd.isna(x) else '' for x in df_assemblies.loc[:,'run_epiweek'])

    # derived column: sample_age_at_runtime
    if 'sample_age_at_runtime' not in df_assemblies.columns:
        df_assemblies.loc[:,'sample_age_at_runtime'] = list(x.days for x in df_assemblies.loc[:,'run_date'] - df_assemblies.loc[:,'collection_date'])

    # join column: collaborator_id
    if collab_ids is not None:
        df_assemblies = df_assemblies.merge(collab_ids, on='sample', how='left', validate='one_to_one')

    return df_assemblies


def main(args):

    df_assemblies = load_data(args.assemblies_tsv, args.collab_tsv, args.min_unambig, args.min_date, args.max_date)

    states_all = list(str(x) for x in df_assemblies['geo_state'].unique() if x and not pd.isna(x))
    collaborators_all = list(str(x) for x in df_assemblies['collected_by'].unique() if x and not pd.isna(x))
    purposes_all = list(str(x) for x in df_assemblies['purpose_of_sequencing'].unique() if x and not pd.isna(x))

    sequencing_lab_sanitized = args.sequencing_lab.replace(' ', '_')
    date_string = datetime.date.today().strftime("%Y_%m_%d")

    # prep output columns
    reordered_cols = [
        'sample',
        'collaborator_id',
        'hl7_message_id',
        'internal_id',
        'biosample_accession',
        'pango_lineage',
        'nextclade_clade',
        'geo_loc_name',
        'collection_date',
        'run_date',
        'assembly_length_unambiguous',
        'vadr_num_alerts',
        'nextclade_aa_subs',
        'nextclade_aa_dels',
        'collected_by',
        'purpose_of_sequencing',
        'amplicon_set',
        'bioproject_accession',
        'genome_status',
    ]
    reordered_cols = list(c for c in reordered_cols if c in df_assemblies.columns)
    reordered_cols.extend([c for c in df_assemblies.columns if c not in reordered_cols])

    # the everything reports
    out_basename = 'report-{}-everything-{}'.format(sequencing_lab_sanitized, date_string)
    df_assemblies.to_excel('{}.xlsx'.format(out_basename),
        index=False, freeze_panes=(1,1), columns=reordered_cols)
    df_assemblies.to_csv("{}.tsv".format(out_basename), sep='\t', index=False, columns=reordered_cols)
    subprocess.check_call([
        'R', '--vanilla', '--no-save', '-e',
        """rmarkdown::render('/docker/covid_seq_report-everything.Rmd',
            output_file='{}.pdf',
            output_dir='./',
            params = list(
                assemblies_tsv = '{}.tsv',
                sequencing_lab = '{}',
                intro_blurb = '{}',
                voc_list = '{}',
                voi_list = '{}',
                min_unambig = {:d}))
        """.format(out_basename, os.path.join(os.getcwd(), out_basename),
            args.sequencing_lab, args.intro_blurb,
            args.voc_list, args.voi_list, args.min_unambig),
        ])


    # per-state PDFs and XLSXs
    for state in states_all:
        print("making reports for state '{}'".format(state))
        state_sanitized = state.replace(' ', '_')
        out_basename = "report-{}-by_state-{}-{}".format(
            sequencing_lab_sanitized, state_sanitized, date_string)
        df = df_assemblies.query('geo_state == "{}"'.format(state))
        df.to_excel('{}-per_sample.xlsx'.format(out_basename),
            index=False, freeze_panes=(1,1), columns=reordered_cols)
        df.to_csv("{}-per_sample.tsv".format(out_basename), sep='\t', index=False, columns=reordered_cols)
        subprocess.check_call([
            'R', '--vanilla', '--no-save', '-e',
            """rmarkdown::render('/docker/covid_seq_report-by_state.Rmd',
                output_file='{}.pdf',
                output_dir='./',
                params = list(
                    state = '{}',
                    assemblies_tsv = '{}-per_sample.tsv',
                    sequencing_lab = '{}',
                    intro_blurb = '{}',
                    voc_list = '{}',
                    voi_list = '{}',
                    min_unambig = {:d}))
            """.format(out_basename,
                state, os.path.join(os.getcwd(), out_basename),
                args.sequencing_lab, args.intro_blurb,
                args.voc_list, args.voi_list, args.min_unambig),
            ])
        
    # per-collab PDFs and XLSXs
    for collab in collaborators_all:
        print("making reports for collaborator '{}'".format(collab))
        collab_sanitized = collab.replace(' ', '_')
        out_basename = "report-{}-by_lab-{}-{}".format(
            sequencing_lab_sanitized, collab_sanitized, date_string)
        df = df_assemblies.query('collected_by == "{}"'.format(collab))
        df.to_excel('{}-per_sample.xlsx'.format(out_basename),
            index=False, freeze_panes=(1,1), columns=reordered_cols)
        df.to_csv("{}-per_sample.tsv".format(out_basename), sep='\t', index=False, columns=reordered_cols)
        subprocess.check_call([
            'R', '--vanilla', '--no-save', '-e',
            """rmarkdown::render('/docker/covid_seq_report-by_collaborator.Rmd',
                output_file='{}.pdf',
                output_dir='./',
                params = list(
                    collab = '{}',
                    assemblies_tsv = '{}-per_sample.tsv',
                    sequencing_lab = '{}',
                    intro_blurb = '{}',
                    voc_list = '{}',
                    voi_list = '{}',
                    min_unambig = {:d}))
            """.format(out_basename,
                collab, os.path.join(os.getcwd(), out_basename),
                args.sequencing_lab, args.intro_blurb,
                args.voc_list, args.voi_list, args.min_unambig),
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

    parser.add_argument('--voc_list',
                        default="B.1.1.7,B.1.351,B.1.351.1,B.1.351.2,P.1,P.1.1,B.1.427,B.1.429,B.1.429.1",
                        help='Comma separated list of Pangolin lineages that are official Variants of Concern. (default: %(default)s)')
    parser.add_argument('--voi_list',
                        default="B.1.525,B.1.526,B.1.526.1,B.1.526.2,B.1.526.3,P.2",
                        help='Comma separated list of Pangolin lineages that are official Variants of Interest. (default: %(default)s)')

    args = parser.parse_args()
    main(args)
