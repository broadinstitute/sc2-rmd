#!/usr/bin/env python3

import os
import sys
import subprocess

#import epiweeks
import pandas as pd
import numpy as np


min_unambig = 24000


# -------------------------- LOAD DATA ---------------------------- #

assemblies_tsv = sys.argv[1]
collab_tsv = sys.argv[2]

df_assemblies = pd.read_csv(assemblies_tsv, sep='\t')
if collab_tsv and os.path.isfile(collab_tsv) and os.path.getsize(collab_tsv):
    collab_ids = pd.read_csv(collab_tsv, sep='\t')[list(['external_id', 'collaborator_id'])]
    collab_ids.columns = ['sample', 'collaborator_id']
else:
    collab_ids = pd.DataFrame(columns = ['sample', 'collaborator_id']) 


# -------------------------- TRANSFORM DATA ---------------------------- #

# format dates properly
df_assemblies = df_assemblies.astype({'collection_date':np.datetime64,'run_date':np.datetime64})

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


# get lists
states_all = list(x for x in df_assemblies['geo_state'].unique() if x)
collaborators_all = list(x for x in df_assemblies['collected_by'].unique() if x)
purposes_all = list(x for x in df_assemblies['purpose_of_sequencing'].unique() if x)



# -------------------------- RUN R Markdown reports ---------------------------- #


for state in states_all:
    state_sanitized = state.replace(' ', '_')
    subprocess.check_call([
        'R', '--vanilla', '--no-save', '-e',
        "rmarkdown::render('covid_seq_report-by_state.Rmd', output_file='report-{}.pdf', params = list(state = '{}', assemblies_tsv = '{}', collab_ids_tsv = '{}'))".format(state_sanitized, state, assemblies_tsv, collab_tsv),
        ])

    df = df_assemblies.query('geo_state == "{}"'.format(state))
    df.to_excel('report-{}-per_sample.xlsx'.format(state_sanitized), columns=[
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
