#!/usr/bin/env python3
"""
Clean up emojis in the signature server for better compatibility
"""

import re

# Read the signature server file
with open('simple_signature_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace common emojis with text equivalents
emoji_replacements = {
    '🖊️': '[Sign]',
    '📄': '[Document]',
    '📝': '[Note]',
    '🏢': '[Building]',
    '⛽': '[Fuel]',
    '💰': '[Money]',
    '📋': '[Clipboard]',
    '🤝': '[Handshake]',
    '⏰': '[Clock]',
    '✅': '[Checkmark]',
    '🔒': '[Lock]',
    '🗑️': '[Trash]',
    '⏳': '[Hourglass]',
    '🔐': '[Key]',
    '❌': '[X]',
    '🌐': '[Globe]',
    '📧': '[Email]',
    '🔗': '[Link]',
    '🎉': '[Celebrate]',
    '💾': '[Save]',
    '✔️': '[Check]',
    '📊': '[Chart]',
    '🚀': '[Rocket]',
    '⚠️': '[Warning]'
}

# Replace emojis
for emoji, replacement in emoji_replacements.items():
    content = content.replace(emoji, replacement)

# Write the cleaned version
with open('simple_signature_server_clean.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Created clean version: simple_signature_server_clean.py")
print("This version uses text labels instead of emojis for better compatibility.")