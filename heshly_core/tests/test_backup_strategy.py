from pathlib import Path


def test_backup_strategy():

    print("\n================================")
    print("Backup Strategy")
    print("================================\n")

    backup = Path("deployment/scripts/backup.sh")
    restore = Path("deployment/scripts/restore.sh")

    assert backup.exists()
    assert restore.exists()

    backup_text = backup.read_text()
    restore_text = restore.read_text()

    assert "tar -czf" in backup_text
    assert "mkdir -p" in backup_text

    assert "tar -xzf" in restore_text

    print("✅ Backup script found")
    print("✅ Restore script found")
    print("✅ Archive backup configured")
    print("✅ Archive restore configured")

    print("\n🎉 BACKUP STRATEGY PASSED\n")