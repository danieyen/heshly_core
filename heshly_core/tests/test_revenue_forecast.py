from heshly_core.models.crm import Opportunity

from heshly_core.services.crm.revenue_forecast_manager import (
    RevenueForecastManager,
    RevenueForecastError,
)


def run():

    manager = RevenueForecastManager()


    opportunity = Opportunity(
        opportunity_id="OPP-001",
        lead_id="LEAD-001",
        title="Dental Implant Package",
        expected_value=200000,
        probability=0.75,
    )


    result = manager.calculate(
        opportunity
    )


    print(result)


    assert result.forecast_value == 150000


    # Invalid value test

    bad_opportunity = Opportunity(
        opportunity_id="OPP-002",
        lead_id="LEAD-002",
        title="Invalid Deal",
        expected_value=-5000,
        probability=0.50,
    )


    try:

        manager.calculate(
            bad_opportunity
        )


    except RevenueForecastError as error:

        print("\nExpected Error:")
        print(error)


    else:

        raise Exception(
            "Invalid forecast should fail"
        )


    print(
        "\n✅ Revenue Forecast Functional Test Passed"
    )


if __name__ == "__main__":
    run()