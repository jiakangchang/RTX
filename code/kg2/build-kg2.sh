#!/bin/bash
set -euxo pipefail
# Usage: build-kg2.sh [all|test]
#
# * If no argument, then by default only the OWL-based KG2 is generated from scratch. It is then merged
#   with the pre-existing SemMedDB JSON file. 
# 
# * The 'all' argument means that the script will build the UMLS and SemMedDB files. Complete KG2 build.
#
# * The 'test' argument means that the OWL inventory is read from "owl-load-inventory-test.yaml"
#   and all KG JSON files generated will have the string "-test" appended before their JSON suffixes.

## load the master config file
CONFIG_DIR=`dirname "$0"`
source ${CONFIG_DIR}/master-config.shinc

## supply a default value for the BUILD_FLAG string
BUILD_FLAG=${1:-""}

## set the path to include ${BUILD_DIR}
export PATH=$PATH:${BUILD_DIR}

if [ ${BUILD_FLAG} == 'test' ]
then
    TEST_SUFFIX='-test'
else
    TEST_SUFFIX=''
fi

OUTPUT_FILE_BASE=kg2-owl${TEST_SUFFIX}.json
FINAL_OUTPUT_FILE_BASE=kg2${TEST_SUFFIX}.json
OUTPUT_NODES_FILE_BASE=kg2${TEST_SUFFIX}-nodes.json
REPORT_FILE_BASE=kg2-report${TEST_SUFFIX}.json
OUTPUT_FILE_FULL=${BUILD_DIR}/${OUTPUT_FILE_BASE}
OUTPUT_NODES_FILE_FULL=${BUILD_DIR}/${OUTPUT_NODES_FILE_BASE}
REPORT_FILE_FULL=${BUILD_DIR}/${REPORT_FILE_BASE}
STDERR_LOG_FILE=build-kg2-from-owl-stderr${TEST_SUFFIX}.log
OWL_LOAD_INVENTORY_FILE=${CODE_DIR}/owl-load-inventory${TEST_SUFFIX}.yaml
FINAL_OUTPUT_FILE_FULL=${BUILD_DIR}/${FINAL_OUTPUT_FILE_BASE}

cd ${BUILD_DIR}

MEM_GB=`${CODE_DIR}/get-system-memory-gb.sh`

export OWLTOOLS_MEMORY=${MEM_GB}G
export DEBUG=1  ## for owltools

if [ ${BUILD_FLAG} == 'all' ]
then
## Build UMLS TTL files
   ${CODE_DIR}/build-umls.sh
fi

## run the build_kg2_from_owl.py script
${VENV_DIR}/bin/python3 -u ${CODE_DIR}/multi_owl_to_json_kg.py \
           ${CODE_DIR}/curies-to-categories.yaml \
           ${CODE_DIR}/curies-to-urls-lookaside-list.yaml \
           ${OWL_LOAD_INVENTORY_FILE} \
           ${OUTPUT_FILE_FULL} \
           2>${BUILD_DIR}/${STDERR_LOG_FILE}

if [ ${BUILD_FLAG} == 'all' ]
then
## Build kg2-semmeddb.json.gz
    ${CODE_DIR}/build-semmeddb.sh
fi

${VENV_DIR}/bin/python3 ${CODE_DIR}/merge_json_kgs.py ${OUTPUT_FILE_FULL} \
           ${BUILD_DIR}/kg2-semmeddb.json ${FINAL_OUTPUT_FILE_FULL}

${VENV_DIR}/bin/python3 ${CODE_DIR}/get_nodes_json_from_kg_json.py \
           ${FINAL_OUTPUT_FILE_FULL} ${OUTPUT_NODES_FILE_FULL}

${VENV_DIR}/bin/python3 ${CODE_DIR}/report_stats_on_kg.py \
           ${FINAL_OUTPUT_FILE_FULL} ${REPORT_FILE_FULL}

gzip ${FINAL_OUTPUT_FILE_FULL}
gzip ${FINAL_OUTPUT_NODES_FILE_FULL}

## copy the KG to the public S3 bucket
aws s3 cp --no-progress --region ${S3_REGION} ${FINAL_OUTPUT_FILE_FULL}.gz s3://${S3_BUCKET_PUBLIC}/
aws s3 cp --no-progress --region ${S3_REGION} ${OUTPUT_NODES_FILE_FULL}.gz s3://${S3_BUCKET_PUBLIC}/
aws s3 cp --no-progress --region ${S3_REGION} ${REPORT_FILE_FULL} s3://${S3_BUCKET_PUBLIC}/

## copy the log files to the public S3 bucket
aws s3 cp --no-progress --region ${S3_REGION} ${BUILD_DIR}/build-kg2-stderr.log s3://${S3_BUCKET_PUBLIC}/
aws s3 cp --no-progress --region ${S3_REGION} ${BUILD_DIR}/${STDOUT_LOG_FILE} s3://${S3_BUCKET_PUBLIC}/

## copy the config files to the public S3 bucket
aws s3 cp --no-progress --region ${S3_REGION} ${OWL_LOAD_INVENTORY_FILE} s3://${S3_BUCKET_PUBLIC}/

# copy the index.html file to the public S3 bucket
aws s3 cp --no-progress --region ${S3_REGION} ${CODE_DIR}/s3/index.html s3://${S3_BUCKET_PUBLIC}/

echo "================= script finished ================="
