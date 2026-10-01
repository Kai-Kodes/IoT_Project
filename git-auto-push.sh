#!/bin/bash

cd "$(dirname "$0")" || exit 1

while true; do
    if [[ -n $(git status --porcelain) ]]; then
        git add .
        git commit -m "Auto-update $(date '+%Y-%m-%d %H:%M:%S')"
        git push origin main
    fi

    sleep 300
done
