import frappe
from unittest import TestCase

from heshly_core.models.business_account import BusinessAccount
from heshly_core.repositories.frappe_business_repository import (
    FrappeBusinessRepository,
)


class TestFrappeBusinessRepository(TestCase):

    def setUp(self):
        self.repo = FrappeBusinessRepository()
        self.repo.clear()
        self.repo.context.set("heshly")

    def tearDown(self):
        self.repo.clear()

    def test_get_existing_business(self):
        business = self.repo.get("HESHLY")

        self.assertIsNotNone(business)
        self.assertEqual(business.business_id, "HESHLY")
        self.assertEqual(business.name, "Heshly")
        self.assertEqual(business.tenant_id, "heshly")

    def test_exists_existing_business(self):
        self.assertTrue(self.repo.exists("HESHLY"))

    def test_get_missing_business(self):
        self.assertIsNone(self.repo.get("DOES_NOT_EXIST"))

    def test_exists_missing_business(self):
        self.assertFalse(self.repo.exists("DOES_NOT_EXIST"))

    def test_all_returns_current_tenant_only(self):
        businesses = self.repo.all()

        self.assertGreaterEqual(len(businesses), 1)

        for business in businesses:
            self.assertEqual(
                business.tenant_id,
                "heshly",
            )

    def test_tenant_isolation(self):
        self.repo.context.set("other_tenant")

        self.assertIsNone(
            self.repo.get("HESHLY")
        )

        self.assertFalse(
            self.repo.exists("HESHLY")
        )

        self.assertEqual(
            self.repo.all(),
            [],
        )

    def test_cross_tenant_save_is_rejected(self):
        business = BusinessAccount(
            business_id="SECURITY_TEST_AUTO",
            tenant_id="other_tenant",
            name="Should Never Save",
            domain="should-not-save.example.com",
        )

        with self.assertRaises(PermissionError):
            self.repo.save(business)

        self.assertFalse(
            frappe.db.exists(
                "Business Account",
                {
                    "business_id": "SECURITY_TEST_AUTO",
                },
            )
        )

    def test_no_tenant_context_is_rejected(self):
        self.repo.clear()

        with self.assertRaises(RuntimeError):
            self.repo.get("HESHLY")

        with self.assertRaises(RuntimeError):
            self.repo.exists("HESHLY")

        with self.assertRaises(RuntimeError):
            self.repo.all()

    def test_clear_removes_context(self):
        self.assertTrue(
            self.repo.has_tenant()
        )

        self.repo.clear()

        self.assertFalse(
            self.repo.has_tenant()
        )

    def test_domain_normalization_on_save(self):
        """Domain is server-controlled and normalized from business_id."""
        business = BusinessAccount(
            business_id="TEST_DOMAIN_NORM",
            tenant_id="heshly",
            name="Test Domain Norm",
            domain="clients.heshly.com",
        )
        saved = self.repo.save(business)
        self.assertEqual(saved.domain, "test-domain-norm.heshly.com")
        # Reload from DB
        reloaded = self.repo.get("TEST_DOMAIN_NORM")
        self.assertEqual(reloaded.domain, "test-domain-norm.heshly.com")
        # Cleanup
        frappe.delete_doc("Business Account", "TEST_DOMAIN_NORM", force=True)
        frappe.db.commit()

    def test_domain_rejects_shared_portal_on_direct_insert(self):
        """Direct Document insert with clients.heshly.com is corrected by validate."""
        from heshly_core.heshly_core.doctype.business_account.business_account import _normalized_heshly_domain
        expected = _normalized_heshly_domain("MY_CUSTOM_BIZ")
        # Simulate doc lifecycle
        doc = frappe.new_doc("Business Account")
        doc.business_id = "MY_CUSTOM_BIZ"
        doc.business_name = "My Custom Biz"
        doc.domain = "clients.heshly.com"
        # validate should correct domain before insert; need tenant context
        doc.insert(ignore_permissions=True)
        # After insert domain must be normalized, not shared portal
        stored = frappe.db.get_value("Business Account", "MY_CUSTOM_BIZ", "domain")
        self.assertEqual(stored, expected)
        self.assertNotEqual(stored, "clients.heshly.com")
        frappe.delete_doc("Business Account", "MY_CUSTOM_BIZ", force=True)
        frappe.db.commit()
