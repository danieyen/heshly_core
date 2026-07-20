# Heshly Engineering Blueprint v1.0

## Goal
Build the MVP as fast as possible while maintaining production-quality architecture.

## Layers

1. DocTypes → Data
2. Models → Shared objects
3. Services → Business logic
4. API → Entry points
5. Tests → Verification

## AI Pipeline

Incoming Message
↓
Intent Classifier
↓
Entity Extractor
↓
Completeness Checker
↓
Business Rules
↓
Action Planner
↓
Response Generator
↓
WhatsApp

## Rules

- No business logic inside DocTypes.
- One responsibility per file.
- Every service gets a test.
- No hardcoded business data.
- ERPNext is the source of truth.

## MVP Success

✓ Receive WhatsApp message
✓ Understand intent
✓ Qualify customer
✓ Answer questions
✓ Book appointment
✓ Save conversation
✓ Remember customer
✓ Human handoff