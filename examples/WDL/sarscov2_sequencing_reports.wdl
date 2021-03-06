version 1.0

task sequencing_report {
    meta {
        description: "Produce sequencing progress report."
    }
    input {
        File           assembly_stats_tsv
        File           collab_ids_tsv

        String  docker = "quay.io/broadinstitute/sc2-rmd:latest"
    }
    command {
        set -e
        /docker/reports.py "~{assembly_stats_tsv}" "~{collab_ids_tsv}"
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
    }
}


workflow sarscov2_sequencing_reports {
    meta {
        description: "Produce per-state and per-collaborator weekly reports of SARS-CoV-2 surveillance data."
    }

    call sequencing_report 

    output {
        Array[File]  reports = sequencing_report.reports
        Array[File]  sheets  = sequencing_report.sheets
    }
}
