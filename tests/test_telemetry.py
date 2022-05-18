import json

import pytest
from unittest import mock

from aos.telemetry import AosTelemetryManager
from tests.util import read_fixture

mock_rest = mock.Mock()
mgr = AosTelemetryManager(mock_rest)


@pytest.fixture(params=["4.0.0"])
def aos_api_version(request):
    return request.param


def test_add_endpoint():
    mgr.add_endpoint("fakehost", "fakeport", "faketype")
    mock_rest.json_resp_post.assert_called_with(
        uri="/api/streaming-config",
        data={
            "hostname": "fakehost",
            "port": "fakeport",
            "streaming_type": "faketype",
            "sequencing_mode": "sequenced",
            "protocol": "protoBufOverTcp",
        },
    )


def test_get_endpoints(aos_api_version):
    fixture_path = f"aos/{aos_api_version}/telemetry/endpoints.json"
    mock_rest.json_resp_get.return_value = json.loads(read_fixture(fixture_path))
    r = mgr.get_endpoints()
    assert len(r) == 3
    mock_rest.json_resp_get.assert_called()


def test_delete_endpoints():
    mgr.delete_all_endpoints()
    mock_rest.delete.assert_called()
