from heshly_core.utils import constants
from heshly_core.utils import datetime as datetime_utils
from heshly_core.utils import formatter
from heshly_core.utils import validators


def test_utilities():

    print("\n================================")
    print("Utility Tests")
    print("================================\n")

    # =====================================================
    # Constants
    # =====================================================

    assert constants is not None

    print("✅ Constants")

    # =====================================================
    # Datetime Utilities
    # =====================================================

    assert datetime_utils is not None

    print("✅ Datetime Utilities")

    # =====================================================
    # Formatter Utilities
    # =====================================================

    assert formatter is not None

    print("✅ Formatter Utilities")

    # =====================================================
    # Validators
    # =====================================================

    assert validators is not None

    print("✅ Validators")

    print("\n🎉 UTILITY TESTS PASSED\n")