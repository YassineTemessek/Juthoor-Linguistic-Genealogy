#!/usr/bin/env bash
#
# Setup raw data symlinks for Juthoor Linguistic Genealogy
# Cross-platform equivalent of setup_raw_links.ps1
#
# This script creates symbolic links from the Resources directory
# to the expected locations in Juthoor-DataCore-LV0/data/raw/
#
# Usage:
#   ./scripts/setup_raw_links.sh           # Run normally
#   ./scripts/setup_raw_links.sh --dry-run # Preview without changes
#

set -euo pipefail

DRY_RUN=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
RESOURCES_ROOT="$REPO_ROOT/Resources"
LV0_RAW_ROOT="$REPO_ROOT/Juthoor-DataCore-LV0/data/raw"

# Colors for output (if terminal supports it)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--dry-run|-n]"
            echo ""
            echo "Setup symlinks from Resources/ to Juthoor-DataCore-LV0/data/raw/"
            echo ""
            echo "Options:"
            echo "  --dry-run, -n   Show what would be done without making changes"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

log() {
    echo -e "[setup_raw_links] $1"
}

log_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
}

log_create() {
    echo -e "${BLUE}[CREATE]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

ensure_dir() {
    local path="$1"
    if [[ ! -d "$path" ]]; then
        if $DRY_RUN; then
            log_create "Would create directory: $path"
        else
            mkdir -p "$path"
            log_create "Created directory: $path"
        fi
    fi
}

# Create a symbolic link (for directories)
ensure_symlink() {
    local link_path="$1"
    local target_path="$2"
    local description="${3:-}"

    ensure_dir "$(dirname "$link_path")"

    # Check if link already exists and points to correct target
    if [[ -L "$link_path" ]]; then
        local current_target
        current_target="$(readlink "$link_path")"
        if [[ "$current_target" == "$target_path" ]]; then
            log_ok "Symlink OK: $link_path -> $target_path"
            return
        fi
        log_skip "Symlink exists with different target: $link_path"
        return
    fi

    # Check if something else exists at this path
    if [[ -e "$link_path" ]]; then
        log_skip "Path exists (not symlink): $link_path"
        return
    fi

    # Check if target exists
    if [[ ! -e "$target_path" ]]; then
        log_skip "Target missing: $target_path"
        return
    fi

    # Create the symlink
    if $DRY_RUN; then
        log_create "Would symlink: $link_path -> $target_path"
    else
        ln -s "$target_path" "$link_path"
        log_create "Symlinked: $link_path -> $target_path"
    fi
}

# Create a hard link (for files)
ensure_hardlink() {
    local link_path="$1"
    local target_path="$2"

    ensure_dir "$(dirname "$link_path")"

    # Check if file already exists
    if [[ -e "$link_path" ]]; then
        # Check if it's the same file (hardlink)
        if [[ -e "$target_path" ]]; then
            local link_inode target_inode
            # Use stat in a portable way
            if [[ "$(uname)" == "Darwin" ]]; then
                link_inode="$(stat -f %i "$link_path" 2>/dev/null || echo "")"
                target_inode="$(stat -f %i "$target_path" 2>/dev/null || echo "")"
            else
                link_inode="$(stat -c %i "$link_path" 2>/dev/null || echo "")"
                target_inode="$(stat -c %i "$target_path" 2>/dev/null || echo "")"
            fi
            if [[ -n "$link_inode" && -n "$target_inode" && "$link_inode" == "$target_inode" ]]; then
                log_ok "Hardlink OK: $link_path"
                return
            fi
        fi
        log_skip "File exists (not hardlink to target): $link_path"
        return
    fi

    # Check if target exists
    if [[ ! -e "$target_path" ]]; then
        log_skip "Target missing: $target_path"
        return
    fi

    # Create the hard link
    if $DRY_RUN; then
        log_create "Would hardlink: $link_path -> $target_path"
    else
        ln "$target_path" "$link_path"
        log_create "Hardlinked: $link_path -> $target_path"
    fi
}

echo ""
log "Juthoor Linguistic Genealogy - Raw Data Link Setup"
echo ""
log "Repo root:  $REPO_ROOT"
log "Resources:  $RESOURCES_ROOT"
log "LV0 raw:    $LV0_RAW_ROOT"
if $DRY_RUN; then
    log "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
fi
echo ""

# =============================================================================
# Arabic Sources
# =============================================================================
log "Setting up Arabic sources..."

# Quran morphology data
ensure_symlink \
    "$LV0_RAW_ROOT/arabic/quran-morphology" \
    "$RESOURCES_ROOT/qac_morphology" \
    "Quranic Arabic Corpus morphology"

# Word-root mapping CSV
ensure_hardlink \
    "$LV0_RAW_ROOT/arabic/word_root_map.csv" \
    "$RESOURCES_ROOT/word_root_map.csv"

# HuggingFace Arabic roots dataset
ensure_symlink \
    "$LV0_RAW_ROOT/arabic/arabic_roots_hf" \
    "$RESOURCES_ROOT/arabic_roots_hf" \
    "HuggingFace Arabic roots"

# Taj al-Arus roots
ensure_symlink \
    "$LV0_RAW_ROOT/arabic/arabic_roots_taj" \
    "$RESOURCES_ROOT/arabic_roots_taj" \
    "Taj al-Arus Arabic roots"

# =============================================================================
# English Sources
# =============================================================================
log "Setting up English sources..."

# CMUDict pronunciation dictionary
ensure_symlink \
    "$LV0_RAW_ROOT/english/cmudict" \
    "$RESOURCES_ROOT/english_modern" \
    "CMUDict pronunciation data"

# =============================================================================
# Classical Languages
# =============================================================================
log "Setting up classical language sources..."

# Ancient Greek
ensure_symlink \
    "$LV0_RAW_ROOT/ancient_greek" \
    "$RESOURCES_ROOT/ancient_greek" \
    "Ancient Greek data"

# Latin
ensure_symlink \
    "$LV0_RAW_ROOT/latin" \
    "$RESOURCES_ROOT/latin" \
    "Latin data"

# =============================================================================
# Quranic Datasets
# =============================================================================
log "Setting up Quranic datasets..."

ensure_symlink \
    "$LV0_RAW_ROOT/quran_dataset" \
    "$RESOURCES_ROOT/quran_dataset including CSV" \
    "Quran dataset with CSV"

echo ""
log "${GREEN}Setup complete!${NC}"
echo ""

if $DRY_RUN; then
    log "This was a dry run. Run without --dry-run to apply changes."
fi
