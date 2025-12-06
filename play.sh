#!/bin/bash
# Quick start script for Mamitrax

echo "🛒 Welcome to Mamitrax! 🛒"
echo ""
echo "Starting the game..."
echo "Note: Running with fallback graphics (simple shapes)"
echo ""
echo "Want better graphics? Run: python generate_images.py"
echo "(Requires OPENAI_API_KEY environment variable)"
echo ""

# Run the game
.venv/bin/python main.py
