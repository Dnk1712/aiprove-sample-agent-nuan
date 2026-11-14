#!/bin/sh
# Build (if needed) and run the prime counter.
# Usage: echo 5000000 | ./run.sh
set -e
cd "$(dirname "$0")"
make -s primes
exec ./primes
