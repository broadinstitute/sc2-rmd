version 1.0

task sequencing_report {
    meta {
        description: "Produce sequencing progress report."
    }
    input {
        File           assembly_stats_tsv
        File?          collab_ids_tsv

        String?        sequencing_lab
        String?        intro_blurb
        String?        max_date
        String?        min_date
        Int?           min_unambig

        String  docker = "quay.io/broadinstitute/sc2-rmd:latest"
    }
    command {
        set -e
        /docker/reports.py \
            "~{assembly_stats_tsv}" \
            ~{'--collab_tsv="' + collab_ids_tsv + '"'} \
            ~{'--sequencing_lab="' + sequencing_lab + '"'} \
            ~{'--intro_blurb="' + intro_blurb + '"'} \
            ~{'--max_date=' + max_date} \
            ~{'--min_date=' + min_date} \
            ~{'--min_unambig=' + min_unambig}
        zip all_reports.zip *.pdf *.xlsx
    }
    runtime {
        docker: docker
        memory: "2 GB"
        cpu:    2
        disks: "local-disk 50 HDD"
        dx_instance_type: "mem1_ssd1_v2_x2"
    }
    output {
        Array[File] reports = glob("*.pdf")
        Array[File] sheets = glob("*.xlsx")
        File        all_zip = "all_reports.zip"
    }
}


workflow sarscov2_sequencing_reports {
    meta {
        description: "Produce per-state and per-collaborator weekly reports of SARS-CoV-2 surveillance data."
    }

    call sequencing_report 

    output {
    File         sequencing_reports_zip   = sequencing_report.all_zip
    }
}
