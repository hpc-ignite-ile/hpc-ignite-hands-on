#!/bin/bash
# Compatibility wrapper for PyTorch GPU training on LANTA.
# Prefer pytorch-shared.sh for new lessons.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/pytorch-shared.sh"
