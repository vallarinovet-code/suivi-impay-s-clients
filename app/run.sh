#!/usr/bin/env bash
# Lance l'application locale de suivi des impayés (boucle locale uniquement).
cd "$(dirname "$0")"
exec python3 server.py "$@"
