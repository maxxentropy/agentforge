#!/bin/bash
# AgentForge Setup Script
# Installs the YAML-only output style for Claude Code

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_STYLES_DIR="$HOME/.claude/output-styles"

echo "========================================"
echo "AgentForge Setup"
echo "========================================"
echo

# Check if Claude Code is installed
if ! command -v claude &> /dev/null; then
    echo "⚠️  Claude Code CLI not found"
    echo "   Install with: npm install -g @anthropic-ai/claude-code"
    echo "   (Requires Claude Pro/Max subscription)"
    echo
fi

# Create output styles directory
if [ ! -d "$CLAUDE_STYLES_DIR" ]; then
    echo "Creating $CLAUDE_STYLES_DIR..."
    mkdir -p "$CLAUDE_STYLES_DIR"
fi

# Copy YAML-only style
echo "Installing yaml-only output style..."
cp "$SCRIPT_DIR/yaml-only.md" "$CLAUDE_STYLES_DIR/yaml-only.md"

echo
echo "✅ Setup complete!"
echo
echo "To use the YAML-only style in Claude Code interactive mode:"
echo "  /output-style yaml-only"
echo
echo "For programmatic execution (AgentForge), the style is"
echo "automatically enforced via --append-system-prompt."
echo
echo "========================================"
echo "Quick Start"
echo "========================================"
echo
echo "  python execute.py intake --request \"Add discount codes\""
echo "  python execute.py clarify"
echo "  python execute.py analyze"
echo "  python execute.py draft"
echo "  python execute.py validate"
echo
