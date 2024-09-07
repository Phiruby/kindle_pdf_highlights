#!/bin/bash

# Check if both arguments are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <internal_name> <subject_title>"
    exit 1
fi

internal_name=$1
subject_title=$2

# Create a new directory for the question set
mkdir -p "question_sets/$internal_name"

# Create a new config file for this set
cat << EOF > "question_sets/$internal_name/config.json"
{
    "internal_name": "$internal_name",
    "subject_title": "$subject_title",
    "qa_pairs_file": "generated_qa_pairs.json",
    "keys_are_question": "true"
}
EOF

# Create an empty generated_qa_pairs.json file
echo "{}" > "question_sets/$internal_name/generated_qa_pairs.json"

echo "Created new question set: $internal_name"