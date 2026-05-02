# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- BERT fine-tuning option as an alternative classification backend
- PostgreSQL migration guide
- Webhook support for post-classification events
- REST API rate-limit headers (`X-RateLimit-*`)

---

## [1.0.0] — 2026-04-27

### Added
- TF-IDF + Logistic Regression document classification pipeline with per-class confidence scores
- Smart folder routing using cosine similarity against existing folder names
- Three-tier confidence decision logic (auto-suggest / offer alternatives / manual selection)
- OCR support for scanned PDFs and images via Tesseract and EasyOCR
- AES-256 file encryption at rest using Python `cryptography` (Fernet)
- SHA-256 duplicate detection before storage
- Full-text keyword search with category, date range, and tag filters
- Immutable audit log for all upload, download, and modification events
- Role-based access control (Admin / User); users are scoped to their own files
- JWT authentication with access and refresh token support
- Per-IP rate limiting via Flask-Limiter
- Drag-and-drop upload UI with real-time progress feedback
- Dashboard with file count, storage usage, and category breakdown charts
- Multi-label document tagging
- Automated backup and restore scripts (`scripts/backup.py`, `scripts/restore_backup.py`)
- Self-signed certificate generator for local HTTPS (`scripts/generate_self_signed_cert.py`)
- Folder watcher for drop-folder auto-classification (`scripts/watch_folder.py`)
- Docker Compose deployment with Nginx reverse proxy
- Sentry integration for production error tracking
- GitHub Actions CI pipeline (lint, test, security scan)
