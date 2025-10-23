#!/usr/bin/env bash
# set-commit-template.sh
set -euo pipefail

TEMPLATE_PATH=".gitlab/.gitmessage.txt"

clear
printf "\n==============================================\n"
printf "        Setting Up Git Commit Template\n"
printf "==============================================\n\n"

# 1) Git 리포지토리 안인지 확인
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf "[ERROR] This is not a Git repository.\n"
  exit 1
fi

# 2) 템플릿 파일 존재 확인
if [[ ! -f "$TEMPLATE_PATH" ]]; then
  printf "[ERROR] Template file not found: %s\n" "$TEMPLATE_PATH"
  exit 1
fi

printf "[1/1] Setting up project commit template...\n"

# 3) 현재 리포지토리(local) 설정
git config commit.template "$TEMPLATE_PATH"

printf "[SUCCESS] Commit template has been set to '%s'.\n\n" "$TEMPLATE_PATH"
printf "==============================================\n"
printf "        Configuration is complete.\n"
printf "==============================================\n\n"

