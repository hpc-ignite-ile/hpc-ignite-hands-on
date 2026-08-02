#!/bin/bash
# Compatibility wrapper for MPI module loads on LANTA.
# Prefer cpe-mpi.sh for new lessons.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/cpe-mpi.sh"
