#!/usr/bin/env bash
set -e

source ./locations.sh

function exec {
    name=$1
    year=$2
    resolution=$3
    bbox="${AREAS[$name]}"

    output_dir=/data/mint/topoflow/$name/fldas/$year\_$resolution
    echo "Going to run and output to $output_dir"

    if [[ ! -d "$output_dir" ]]; then
        mkdir -p "$output_dir"
    fi

    if [[ ! -d "$output_dir/cropped_region" ]]; then
        mkdir -p "$output_dir/cropped_region"
    fi

    python -m dtran.main exec_pipeline \
        --config ./topoflow_climate.yml \
        --tf_climate.input_dir=/data/mint/fldas/$year \
        --tf_climate.crop_region_dir=$output_dir/cropped_region \
        --tf_climate.output_file=$output_dir/climate.rts \
        --tf_climate.DEM_bounds="$bbox" \
        --tf_climate.var_name=Rainf_f_tavg \
        --tf_climate.DEM_xres_arcsecs=$resolution \
        --tf_climate.DEM_yres_arcsecs=$resolution > $output_dir/run.log

    python -m dtran.main exec_pipeline \
        --config ./topoflow_climate_per_month.yml \
        --tf_climate_month.grid_dir=$output_dir/cropped_region \
        --tf_climate_month.output_file=$output_dir/climate.rts > $output_dir/run_climate.log

    # unit conversion
    python flux2rate.py ${output_dir}/climate_flux.rts ${output_dir}/climate.rts
    python flux2rate.py ${output_dir}/climate_flux.01.rts ${output_dir}/climate.01.rts
    python flux2rate.py ${output_dir}/climate_flux.02.rts ${output_dir}/climate.02.rts
    python flux2rate.py ${output_dir}/climate_flux.03.rts ${output_dir}/climate.03.rts
    python flux2rate.py ${output_dir}/climate_flux.04.rts ${output_dir}/climate.04.rts
    python flux2rate.py ${output_dir}/climate_flux.05.rts ${output_dir}/climate.05.rts
    python flux2rate.py ${output_dir}/climate_flux.06.rts ${output_dir}/climate.06.rts
    python flux2rate.py ${output_dir}/climate_flux.07.rts ${output_dir}/climate.07.rts
    python flux2rate.py ${output_dir}/climate_flux.08.rts ${output_dir}/climate.08.rts
    python flux2rate.py ${output_dir}/climate_flux.09.rts ${output_dir}/climate.09.rts
    python flux2rate.py ${output_dir}/climate_flux.10.rts ${output_dir}/climate.10.rts
    python flux2rate.py ${output_dir}/climate_flux.11.rts ${output_dir}/climate.11.rts
    python flux2rate.py ${output_dir}/climate_flux.12.rts ${output_dir}/climate.12.rts

    pushd $output_dir
    mv ./climate_flux.rti ./climate.rti
    # compress the file so we can delete the original file, which is much bigger
    tar -czf data.tar.gz run.log run_climate.log climate.rts climate.rti climate.*.rts cropped_region
    # remove the uncompressed files
    rm climate.*
    popd
}

#years="2008"
years=($1)

for year in $years; do
    bash ./download_fldas.sh $year /data/mint/fldas

    for name in "${!AREAS[@]}"; do
        exec $name $year 30
        exec $name $year 60
    done

    # remove the data
    rm -r /data/mint/fldas/$year

    # upload the data
    bash ./upload_climate.sh $year fldas
done