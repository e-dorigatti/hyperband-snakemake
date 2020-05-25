echo "Called with base directory $1 and budget $2"

if [ -z ${HBTEST+x} ]; then
    python hyperband_snakemake/example/train.py "$1/config" --budget $2
    if [ ! -f "$1/result" ]; then
        echo "ERROR: training script did not generate result file!"
        exit -1
    else
        exit 0
    fi
else
    rnd=$[RANDOM % 10000]
    echo "*** THIS IS A TEST RUN ***"
    echo "Random number is $rnd"
    echo $rnd > "$1/result"
fi
