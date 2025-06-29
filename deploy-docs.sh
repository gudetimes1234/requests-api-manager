#!/bin/bash
# GitHub Pages Deployment Script for requests-connection-manager

echo "Building and deploying documentation to GitHub Pages..."

# Build the documentation
echo "Building documentation..."
mkdocs build

# Deploy to GitHub Pages with force flag
echo "Deploying to GitHub Pages..."
mkdocs gh-deploy --force --message "Deploy documentation for requests-connection-manager v1.0.0"

echo "Documentation deployed successfully!"
echo "Visit: https://charlesgude.github.io/requests-connection-manager/"