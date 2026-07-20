import sys

from pathlib import Path


MOCK_PATH = Path(__file__).parent / "mocks"


sys.path.insert(
    0,
    str(MOCK_PATH)
)

import pytest

from heshly_core.tests.fixtures.environment import (
    get_test_environment,
)

from heshly_core.tests.fixtures.entities import (
    tenant_fixture,
    user_fixture,
    customer_fixture,
    appointment_fixture,
    lead_fixture,
)

from heshly_core.tests.fixtures.security import (
    session_fixture,
    token_fixture,
    security_context_fixture,
)

from heshly_core.tests.fixtures.ai import (
    conversation_fixture,
    ai_session_fixture,
    intent_fixture,
)


@pytest.fixture(scope="session")
def test_environment():

    return get_test_environment()



@pytest.fixture
def tenant():

    return tenant_fixture()



@pytest.fixture
def user():

    return user_fixture()



@pytest.fixture
def customer():

    return customer_fixture()



@pytest.fixture
def appointment():

    return appointment_fixture()



@pytest.fixture
def lead():

    return lead_fixture()



@pytest.fixture
def session():

    return session_fixture()



@pytest.fixture
def token():

    return token_fixture()



@pytest.fixture
def security_context():

    return security_context_fixture()



@pytest.fixture
def conversation():

    return conversation_fixture()



@pytest.fixture
def ai_session():

    return ai_session_fixture()



@pytest.fixture
def intent():

    return intent_fixture()


from heshly_core.tests.mocks import (
    MockWhatsAppService,
    MockCalendarService,
    MockPaymentService,
    MockAIService,
    MockNotificationService,
)


@pytest.fixture
def whatsapp_service():

    return MockWhatsAppService()



@pytest.fixture
def calendar_service():

    return MockCalendarService()



@pytest.fixture
def payment_service():

    return MockPaymentService()



@pytest.fixture
def ai_service():

    return MockAIService()



@pytest.fixture
def notification_service():

    return MockNotificationService()


from heshly_core.tests.environment import (
    TestEnvironment,
)

from heshly_core.tests.database import (
    TestDatabase,
)

from heshly_core.tests.cleanup import (
    TestCleanup,
)


@pytest.fixture(scope="session")
def test_env():

    env = TestEnvironment()

    env.validate()

    return env



@pytest.fixture
def test_database():

    db = TestDatabase()

    db.connect()

    yield db

    db.disconnect()



@pytest.fixture
def cleanup():

    manager = TestCleanup()

    yield manager

    manager.cleanup()
