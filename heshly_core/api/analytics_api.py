from __future__ import annotations

from heshly_core.services.analytics.analytics_integration import (
    AnalyticsIntegration,
)


class AnalyticsAPI:
    """
    Analytics API

    Public interface for the Analytics module.

    Other Heshly modules should communicate with
    analytics through this API rather than directly
    accessing service implementations.
    """

    def __init__(self):

        self.integration = AnalyticsIntegration()

    # =====================================================
    # Analytics
    # =====================================================

    def analytics(self):

        return self.integration.analytics

    # =====================================================
    # Dashboards
    # =====================================================

    def dashboards(self):

        return self.integration.dashboard

    # =====================================================
    # Appointment Analytics
    # =====================================================

    def appointments(self):

        return self.integration.appointments

    # =====================================================
    # Customer Analytics
    # =====================================================

    def customers(self):

        return self.integration.customers

    # =====================================================
    # Sales Analytics
    # =====================================================

    def sales(self):

        return self.integration.sales

    # =====================================================
    # AI Analytics
    # =====================================================

    def ai(self):

        return self.integration.ai

    # =====================================================
    # Marketing Analytics
    # =====================================================

    def marketing(self):

        return self.integration.marketing

    # =====================================================
    # Reporting
    # =====================================================

    def reporting(self):

        return self.integration.reporting

    # =====================================================
    # Business Intelligence
    # =====================================================

    def business_intelligence(self):

        return self.integration.business_intelligence

    # =====================================================
    # Managers
    # =====================================================

    def managers(self):

        return self.integration.managers()

    # =====================================================
    # Summary
    # =====================================================

    def summary(self):

        return self.integration.summary()

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return self.integration.health()