#!/bin/bash
set -e
set -u
set -o pipefail

readonly ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR_F1="${ROOT_DIR}/Fase_1"
readonly SCRIPT_DIR_F2="${ROOT_DIR}/Fase_2"
readonly SCRIPT_DIR_F3="${ROOT_DIR}/Fase_3"
readonly LOG_FILE="${ROOT_DIR}/logs_pipeline/pipeline_completa_$(date +%Y%m%d_%H%M%S).log"
readonly DATA_FILE="dati/taxi_february.txt"
readonly SHARED_DATASET_DIR="${ROOT_DIR}/dataset_processato_condiviso"
readonly GIORNO="2014-02-01"
readonly SEED=42

readonly F1_RADS=(1500 2500 4000)
readonly F1_OUTS=("${SCRIPT_DIR_F1}/experiments_radius_1500" "${SCRIPT_DIR_F1}/experiments_radius_2500" "${SCRIPT_DIR_F1}/experiments_radius_4000")
readonly F2_CONFIGS=("high" "mixed" "low")
readonly F2_OUTS=("${SCRIPT_DIR_F2}/esperimenti_fase2_high" "${SCRIPT_DIR_F2}/esperimenti_fase2_mixed" "${SCRIPT_DIR_F2}/esperimenti_fase2_low")
readonly F3_CONFIGS=("high" "mixed" "low")
readonly F3_OUTS=("${SCRIPT_DIR_F3}/esperimenti_fase3_high" "${SCRIPT_DIR_F3}/esperimenti_fase3_mixed" "${SCRIPT_DIR_F3}/esperimenti_fase3_low")

init_logging() { mkdir -p "$(dirname "$LOG_FILE")"; exec > >(tee -a "$LOG_FILE"); exec 2>&1; log "info" "Log attivo su: $LOG_FILE"; }
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$1] ${*:2}"; }

cleanup() { [ $? -ne 0 ] && log "errore" "Interruzione imprevista (codice $?)." || log "info" "Sessione conclusa."; }
trap cleanup EXIT
trap 'log "attenzione" "Interruzione manuale"; exit 130' INT TERM

handle_failure() {
    log "errore" "Problema in: $1. Controlla i messaggi sopra."
    log "info" "Ritorno al menu tra 10 secondi..."; for i in {10..1}; do echo -ne "Attendi $i... \r"; sleep 1; done; echo ""
    return 1
}

run_cmd() {
    log "info" "Avvio: $2"; log "debug" "Comando: $1"; local s=$(date +%s)
    eval "$1" && log "info" "Completato in $(( $(date +%s) - s ))s: $2" || { log "errore" "Fallito (codice $?): $2"; return 1; }
}

link_dataset() { mkdir -p "$1"; ln -sf "$SHARED_DATASET_DIR" "$1/dataset_processato"; log "info" "Link dati creato in $1"; }

check_prerequisites() {
    log "info" "Verifica prerequisiti..."
    ! command -v python >/dev/null 2>&1 && { log "errore" "Python non trovato."; return 1; }
    [ ! -f "${ROOT_DIR}/${DATA_FILE}" ] && { log "errore" "Dati mancanti: ${DATA_FILE}"; return 1; }
    local missing=0
    local f1_files=("fase_1.py" "classes.py" "imcu.py" "data_manager.py" "plot.py" "statistic_analysis.py" "radius_analysis.py" "advanced_analysis.py" "generate_radius_comparison_figures.py")
    local f2_files=("fase_2.py" "classes_bounded.py" "imcu_bounded.py" "data_manager_bounded.py" "plot_bounded.py")
    local f3_files=("fase_3.py" "classes_adaptive.py" "imcu_adaptive.py" "data_manager_adaptive.py")
    check_files() { local d=$1; shift; for f in "$@"; do [ ! -f "$d/$f" ] && { log "errore" "Manca $f in $d"; missing=$((missing+1)); }; done; }
    check_files "$SCRIPT_DIR_F1" "${f1_files[@]}"
    check_files "$SCRIPT_DIR_F2" "${f2_files[@]}"
    check_files "$SCRIPT_DIR_F3" "${f3_files[@]}"
    [ $missing -gt 0 ] && { log "errore" "Mancano $missing file essenziali."; return 1; }
    log "info" "Tutti i file presenti."; return 0
}

setup_dataset() {
    log "info" "Controllo dataset condiviso..."
    if [ -d "$SHARED_DATASET_DIR" ] && [ "$(find "$SHARED_DATASET_DIR" -name "*.csv" 2>/dev/null | wc -l)" -gt 0 ]; then
        log "info" "Dataset trovato. Salto generazione."; SKIP_ETL=true
    else
        log "info" "Dataset da generare."; mkdir -p "$SHARED_DATASET_DIR"; SKIP_ETL=false
    fi
}

get_params() {
    echo "--raw ${ROOT_DIR}/${DATA_FILE} --day $GIORNO --start 8 --end 20 --cell 500 --max_users 316 --dpi 300 --seed $SEED --out $1"
}

run_sim() {
    link_dataset "$2"; local p=$(get_params "$2"); local extra="$3"
    [ "$4" == "F1" ] && p="$p --cost_min 0.45 --cost_max 0.70 --value_mode uniform --dataset_out $SHARED_DATASET_DIR"
    [ "$4" == "F2" ] && p="$p --radius 2500 --cost_min 0.45 --cost_max 0.70 --value_mode demand_log --value_min 1.8 --value_max 15.0 --no_verify"
    [ "$4" == "F3" ] && p="$p --radius 2500 --cost_min 0.45 --cost_max 0.70 --value_mode demand_log --value_min 1.8 --value_max 15.0 --high_value_pct 0.80 --min_rel_crit 0.70 --max_rel_crit 0.85 --min_qual_crit 0.40 --max_qual_crit 0.60 --min_weight_crit 1.5 --max_weight_crit 2.5"
    run_cmd "python $1 $p $extra" "$5"
}

main_fase1() {
    log "info" "Avvio fase 1"
    [ "$SKIP_ETL" = false ] && log "info" "Dataset verrà generato al primo passo."
    for i in "${!F1_RADS[@]}"; do
        run_sim "${SCRIPT_DIR_F1}/fase_1.py" "${F1_OUTS[$i]}" "--radius ${F1_RADS[$i]}" "F1" "Simulazione fase 1 (raggio=${F1_RADS[$i]})" || return 1
    done

    log "info" "Analisi statistica e figure teoriche fase 1..."
    pushd "$SCRIPT_DIR_F1" >/dev/null
    for s in \
        statistic_analysis.py \
        radius_analysis.py \
        advanced_analysis.py \
        generate_radius_comparison_figures.py \
        generate_bounding_box_roma.py \
        generate_critical_payment.py \
        generate_fft_figure.py \
        generate_routing_figure.py \
        generate_submodularity.py \
        generate_theorical_lorenz_gini.py
    do
        [ -f "$s" ] && run_cmd "python $s" "Script $s" || log "attenzione" "Script $s mancante."
    done
    popd >/dev/null

    log "info" "Fase 1 completata"
    return 0
}

main_fase2() {
    log "info" "Avvio fase 2"
    [ ! "$(ls -A $SHARED_DATASET_DIR 2>/dev/null)" ] && { log "errore" "Dataset mancante. Esegui fase 1."; return 1; }
    for i in "${!F2_CONFIGS[@]}"; do
        run_sim "${SCRIPT_DIR_F2}/fase_2.py" "${F2_OUTS[$i]}" "--rationality ${F2_CONFIGS[$i]}" "F2" "Simulazione fase 2 (razionalità=${F2_CONFIGS[$i]})" || return 1
    done
    log "info" "Fase 2 completata"; return 0
}

main_fase3() {
    log "info" "Avvio fase 3"
    [ ! "$(ls -A $SHARED_DATASET_DIR 2>/dev/null)" ] && { log "errore" "Dataset mancante. Esegui fase 1."; return 1; }
    for i in "${!F3_CONFIGS[@]}"; do
        run_sim "${SCRIPT_DIR_F3}/fase_3.py" "${F3_OUTS[$i]}" "--rationality ${F3_CONFIGS[$i]}" "F3" "Simulazione fase 3 (razionalità=${F3_CONFIGS[$i]})" || return 1
    done
    log "info" "Fase 3 completata"; return 0
}

cd "$ROOT_DIR"
init_logging; check_prerequisites || handle_failure "controllo prerequisiti"; setup_dataset

while true; do
    printf '\033c'; echo "Menu simulazione MCS"; echo "1. Fase 1 (dati e analisi raggio)"; echo "2. Fase 2 (stress test razionalità)"; echo "3. Fase 3 (meccanismo GAP)"; echo "Q. Esci"; echo "---"
    read -r -p "Scelta: " c
    case "$c" in
        1) main_fase1 || handle_failure "fase 1"; read -p "Premi invio..." ;;
        2) main_fase2 || handle_failure "fase 2"; read -p "Premi invio..." ;;
        3) main_fase3 || handle_failure "fase 3"; read -p "Premi invio..." ;;
        [Qq]) log "info" "Uscita."; break ;;
        *) echo "Riprova."; sleep 1 ;;
    esac
done
exit 0
