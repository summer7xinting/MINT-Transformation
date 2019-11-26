#!/usr/bin/env bash
set -e

source ./locations.sh

function run_transformation {
    area=$1
    bbox=$2
    layers="1 2 3 4 5 6 7"

    if [[ ! -d "/data/mint/topoflow/$area/isric_soil/$area" ]]; then
        mkdir -p "/data/mint/topoflow/$area/isric_soil/$area"
    fi

    for layer in $layers
    do
        echo "Run transformation on $area and layer $layer"
        python -m dtran.main exec_pipeline \
            --config ./topoflow_soil.yml \
            --tf_soil.output_dir=/data/mint/topoflow/$area/isric_soil/$area \
            --tf_soil.DEM_bounds="$bbox" \
            --tf_soil.layer=$layer > /data/mint/topoflow/$area/isric_soil/run.log
    done
}

for name in "${!AREAS[@]}"; do
    bbox=${AREAS[$name]}
    run_transformation $name "$bbox"
done