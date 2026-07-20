# Heshly Disaster Recovery Plan

## Objectives

- Restore application after catastrophic failure.
- Minimize downtime.
- Recover latest available backup.

## Recovery Procedure

1. Stop running containers.
2. Locate latest backup.
3. Restore application files.
4. Restore database.
5. Restore Redis (if applicable).
6. Restart Docker services.
7. Verify health checks.
8. Verify application availability.

## Recovery Target

- RTO: < 30 minutes
- RPO: < 24 hours