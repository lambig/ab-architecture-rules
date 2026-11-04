#!/bin/sh
# 同じ導入例をGradleとMavenからPOM/JARだけで検証する。
set -eu
module=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mode=${1:-candidate}
case "$mode" in candidate|public) ;; *) echo 'Usage: verify-example.sh [candidate|public]' >&2; exit 2 ;; esac
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
if [ "$mode" = public ]; then export GRADLE_USER_HOME="$scratch/gradle-cache"; fi
if [ "$mode" = candidate ]; then
    sh "$module/gradlew" -p "$module" --no-daemon --console=plain clean test publishMavenJavaPublicationToCandidateRepository
fi
logs="$module/build/consumer-results/$mode"
mkdir -p "$logs"
cp -R "$module/example/." "$scratch/"
run_gradle() {
    set -- "-Pscenario=$1"
    if [ "$mode" = candidate ]; then set -- "$@" "-ParchitectureRulesRepository=file:$module/build/repository"; fi
    if [ -n "${BOUNDARY_JAVA_HOME:-}" ]; then set -- "$@" "-PboundaryJavaHome=$BOUNDARY_JAVA_HOME"; fi
    if [ -n "${RULES_VERSION:-}" ]; then set -- "$@" "-PrulesVersion=$RULES_VERSION"; fi
    sh "$scratch/gradlew" -p "$scratch" --no-daemon --console=plain --refresh-dependencies "$@" clean check
}
run_maven() {
    set -- "-Dscenario=$1"
    if [ "$mode" = candidate ]; then set -- "$@" "-DarchitectureRulesRepository=file:$module/build/repository"; fi
    if [ -n "${BOUNDARY_JAVA_HOME:-}" ]; then set -- "$@" "-Dboundary.java=$BOUNDARY_JAVA_HOME/bin/java"; fi
    if [ -n "${RULES_VERSION:-}" ]; then set -- "$@" "-DrulesVersion=$RULES_VERSION"; fi
    mvn -B -ntp -f "$scratch/pom.xml" "-Dmaven.repo.local=$scratch/maven-cache" "$@" clean verify || return $?
    test ! -s "$scratch/target/runtime-classpath.txt"
}
for builder in gradle maven; do
    "run_$builder" allowed > "$logs/$builder-allowed.log" 2>&1 || { cat "$logs/$builder-allowed.log"; exit 1; }
    for scenario in direct reference; do
        if "run_$builder" "$scenario" > "$logs/$builder-$scenario.log" 2>&1; then
            echo "ERROR: $builder $scenario unexpectedly passed"; exit 1
        fi
        # ビルド失敗だけを検出成功とは扱わない。
        grep 'expected caller class' "$logs/$builder-$scenario.log"
        grep 'example.shipping.Client' "$logs/$builder-$scenario.log" >/dev/null
        grep 'Shipment.dispatch' "$logs/$builder-$scenario.log" >/dev/null
    done
    "run_$builder" fixed > "$logs/$builder-fixed.log" 2>&1 || { cat "$logs/$builder-fixed.log"; exit 1; }
    grep 'H1 boundary passed' "$logs/$builder-allowed.log"
    grep 'H1 boundary passed' "$logs/$builder-fixed.log"
    echo "$builder: allowed PASS; direct REJECTED; reference REJECTED; fixed PASS; runtime isolated"
done
