#!/bin/bash

# Package script for Athena Insights Automation
# Creates @athena_insights_auto.zip with the complete project structure

echo "Creating @athena_insights_auto.zip package..."

# Remove existing zip if it exists
rm -f @athena_insights_auto.zip

# Create the zip package excluding .git directory
zip -r @athena_insights_auto.zip . -x ".git/*" "*.zip" "package.sh"

echo "Package created successfully: @athena_insights_auto.zip"

# Show package contents
echo -e "\nPackage contents:"
unzip -l @athena_insights_auto.zip

# Show package size
echo -e "\nPackage size:"
ls -lh @athena_insights_auto.zip