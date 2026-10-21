#!/bin/bash
# Serialises builds and asset generators while several agents work in the same tree.
#
#   tools/locked.sh mod <tag>            build the mod to $SCRATCH/build-<tag>/Mods/backroomsss/
#   tools/locked.sh mapgen <tag>         build the layout harness to $SCRATCH/mapgen-<tag>/ (run $SCRATCH/mapgen-<tag>/mapgen.exe)
#   tools/locked.sh run <command...>     run any command (e.g. python tools/gen_fun.py) under the asset lock
#
# Builds share obj/, so they take one lock; asset generators (which rewrite lang/en.json and other shared
# files) take another. A lock is touched every minute while its command runs, so one untouched for 15 minutes is a dead job's and is broken.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SCRATCH="${BACKROOMS_SCRATCH:-${TEMP:-/tmp}/backrooms-build}"
DOTNET="${LOCALAPPDATA:-$HOME/AppData/Local}/Microsoft/dotnet/dotnet.exe"
mkdir -p "$SCRATCH"

take() {
    local lock="$SCRATCH/$1.lock" waited=0
    until mkdir "$lock" 2>/dev/null; do
        if [ -n "$(find "$lock" -maxdepth 0 -mmin +15 2>/dev/null)" ]; then rmdir "$lock" 2>/dev/null; continue; fi
        sleep 2; waited=$((waited + 2))
        [ $((waited % 60)) -eq 0 ] && echo "[locked.sh] still waiting for $1 lock (${waited}s)..." >&2
    done
    # Heartbeat: a slow job (a chain of generators, a long build) keeps its lock fresh, so "old" means "dead"
    ( while :; do sleep 60; touch "$lock" 2>/dev/null || exit; done ) &
    local beat=$!
    trap "kill $beat 2>/dev/null; rmdir '$lock' 2>/dev/null" EXIT
}

mode="${1:-}"; shift || true
case "$mode" in
    mod)
        tag="${1:?tag}"; take build
        cd "$REPO" && "$DOTNET" build Backrooms.csproj -nologo -clp:NoSummary -p:OutputPath="$SCRATCH/build-$tag/Mods/backroomsss/" ;;
    mapgen)
        tag="${1:?tag}"; take build
        cd "$REPO" && "$DOTNET" build tools/mapgen -c Release -nologo -clp:NoSummary -o "$SCRATCH/mapgen-$tag" ;;
    run)
        take assets
        cd "$REPO" && "$@" ;;
    *) echo "usage: tools/locked.sh mod|mapgen <tag> | run <command...>" >&2; exit 2 ;;
esac
