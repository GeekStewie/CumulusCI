from unittest import mock

import pytest

from cumulusci.core.config import (
    BaseProjectConfig,
    OrgConfig,
    ServiceConfig,
    UniversalConfig,
)
from cumulusci.core.config.scratch_org_config import ScratchOrgConfig


@pytest.fixture()
def project_config():
    universal_config = UniversalConfig()
    project_config = BaseProjectConfig(universal_config, config={"no_yaml": True})
    project_config.config["services"] = {
        "connected_app": {"attributes": {"test": {"required": True}}},
        "github": {"attributes": {"name4tests": {"required": True}, "pw4tests": {}}},
        "github_enterprise": {
            "attributes": {"name4tests": {"required": True}, "pw4tests": {}}
        },
        "not_configured": {"attributes": {"foo": {"required": True}}},
        "devhub": {"attributes": {"foo": {"required": True}}},
        "marketing_cloud": {
            "class_path": "cumulusci.core.config.marketing_cloud_service_config.MarketingCloudServiceConfig",
            "attributes": {"foo": {"required": True}},
        },
    }
    project_config.project__name = "TestProject"
    return project_config


@pytest.fixture(autouse=True)
def clear_environment():
    with mock.patch("os.environ", {}):
        yield


@pytest.fixture
def org_config():
    return OrgConfig({"foo": "bar"}, "test")


@pytest.fixture
def scratch_org_config():
    return ScratchOrgConfig({"foo": "bar"}, "test")


@pytest.fixture
def key():
    return "0123456789123456"


@pytest.fixture
def service_config():
    return ServiceConfig({"name4tests": "bar@baz.biz", "password": "test123"})
