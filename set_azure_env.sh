#!/bin/bash
# Azure OpenAI Configuration
# Run this script with: source set_azure_env.sh

echo "Setting Azure OpenAI environment variables..."

# Azure OpenAI credentials
export AZURE_API_KEY="your-azure-openai-api-key-here"
export AZURE_API_BASE="https://airops.openai.azure.com"
export AZURE_API_VERSION="2025-01-01-preview"

# Also set the AZURE_OPENAI variants for compatibility
export AZURE_OPENAI_API_KEY="your-azure-openai-api-key-here"
export AZURE_OPENAI_ENDPOINT="https://airops.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT="gpt-4.1"
export AZURE_OPENAI_API_VERSION="2025-01-01-preview"

echo "✅ Azure OpenAI environment variables set successfully!"
echo ""
echo "Verification:"
echo "AZURE_API_KEY: ${AZURE_API_KEY:0:20}..."
echo "AZURE_API_BASE: $AZURE_API_BASE"
echo "AZURE_API_VERSION: $AZURE_API_VERSION"
echo "AZURE_OPENAI_DEPLOYMENT: $AZURE_OPENAI_DEPLOYMENT"