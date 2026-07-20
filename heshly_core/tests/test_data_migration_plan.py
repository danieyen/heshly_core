from pathlib import Path


def test_data_migration_plan():

    print("\n================================")
    print("Data Migration Plan")
    print("================================\n")

    plan = Path("deployment/data_migration_plan.md")
    script = Path("deployment/scripts/migrate.sh")

    assert plan.exists()
    assert script.exists()

    plan_text = plan.read_text()
    script_text = script.read_text()

    assert "Migration Steps" in plan_text
    assert "Rollback Plan" in plan_text
    assert "Validation Checklist" in plan_text
    assert "Success Criteria" in plan_text

    assert "bench --site production migrate" in script_text

    print("✅ Migration plan documented")
    print("✅ Rollback procedure documented")
    print("✅ Validation checklist documented")
    print("✅ Migration script available")

    print("\n🎉 DATA MIGRATION PLAN PASSED\n")