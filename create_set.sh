#!/bin/bash

# Initialize variables
internal_name=""
subject_title=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --internal_name)
            internal_name="$2"
            shift 2
            ;;
        --subject_title)
            subject_title="$2"
            shift 2
            ;;
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
done

# Check if both arguments are provided
if [ -z "$internal_name" ] || [ -z "$subject_title" ]; then
    echo "Usage: $0 --internal_name <internal_name> --subject_title <subject_title>"
    exit 1
fi

# Create a new directory for the question set
mkdir -p "question_sets/$internal_name"
mkdir -p "question_sets/$internal_name/images"

# Create a new config file for this set
cat << EOF > "question_sets/$internal_name/config.json"
{
    "internal_name": "$internal_name",
    "subject_title": "$subject_title",
    "qa_pairs_file": "generated_qa_pairs.json",
    "keys_are_question": "true",
    "num_questions": 2
}
EOF

# Create an empty generated_qa_pairs.json file
echo "{}" > "question_sets/$internal_name/generated_qa_pairs.json"

echo "Created new question set: $internal_name"