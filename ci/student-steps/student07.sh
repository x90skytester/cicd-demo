#!/usr/bin/env bash
set -euo pipefail

: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required}"
: "${AWS_SESSION_TOKEN:?AWS_SESSION_TOKEN is required}"
: "${AWS_REGION:?AWS_REGION is required}"

STS_CREDS_PATH="${STS_CREDS_PATH:-/tmp/sts-creds.sh}"
umask 077
mkdir -p "$(dirname "$STS_CREDS_PATH")"

{
  printf 'export AWS_ACCESS_KEY_ID=%s\n' "$AWS_ACCESS_KEY_ID"
  printf 'export AWS_SECRET_ACCESS_KEY=%s\n' "$AWS_SECRET_ACCESS_KEY"
  printf 'export AWS_SESSION_TOKEN=%s\n' "$AWS_SESSION_TOKEN"
  printf 'export AWS_REGION=%s\n' "$AWS_REGION"
} | tee "$STS_CREDS_PATH"
