import json
from telnetlib import AO

import pytest
from unittest import mock
from unittest.mock import call

from aos.telemetry import AosTelemetryManager

mock_rest = mock.Mock()
mgr = AosTelemetryManager(mock_rest)

mock_rest.json_resp_get.return_value = {
  "items": [
    {
      "status": {
        "connectionLog": [
          {
            "date": "2022-05-09T15:54:34.909380+00:00",
            "message": "Eof encountered"
          },
          {
            "date": "2022-05-09T15:54:39.910426+00:00",
            "message": "Eof encountered"
          },
          {
            "date": "2022-05-09T15:54:44.911002+00:00",
            "message": "Eof encountered"
          }
        ],
        "connectionTime": None,
        "lastTransmittedTime": "2022-05-09T15:54:35.121503+00:00",
        "epoch": "2022-05-09T15:54:34.909126+00:00",
        "connectionResetCount": 3,
        "streamingEndpoint": {
          "hostname": "100.123.0.8",
          "protocol": "protoBufOverTcp",
          "port": 64429
        },
        "dnsLog": [],
        "connected": False,
        "disconnectionTime": "2022-05-09T15:54:44.910995+00:00"
      },
      "streaming_type": "alerts",
      "sequencing_mode": "sequenced",
      "protocol": "protoBufOverTcp",
      "hostname": "100.123.0.8",
      "port": 64429,
      "id": "9ebce4cc-8119-4e2d-b080-789cbbe57d32"
    },
    {
      "status": {
        "connectionLog": [
          {
            "date": "2022-05-09T15:54:35.121511+00:00",
            "message": "Eof encountered"
          },
          {
            "date": "2022-05-09T15:54:40.122113+00:00",
            "message": "Eof encountered"
          },
          {
            "date": "2022-05-09T15:54:45.122693+00:00",
            "message": "Eof encountered"
          }
        ],
        "connectionTime": None,
        "lastTransmittedTime": "2022-05-09T15:54:41.128922+00:00",
        "epoch": "2022-05-09T15:54:35.121228+00:00",
        "connectionResetCount": 3,
        "streamingEndpoint": {
          "hostname": "100.123.0.8",
          "protocol": "protoBufOverTcp",
          "port": 64427
        },
        "dnsLog": [],
        "connected": False,
        "disconnectionTime": "2022-05-09T15:54:45.122685+00:00"
      },
      "streaming_type": "perfmon",
      "sequencing_mode": "sequenced",
      "protocol": "protoBufOverTcp",
      "hostname": "100.123.0.8",
      "port": 64427,
      "id": "47c455f5-59ad-4582-9608-aa6c09398385"
    },
    {
      "status": {
        "connectionLog": [
          {
            "date": "2022-05-09T15:54:35.013046+00:00",
            "message": "Eof encountered"
          },
          {
            "date": "2022-05-09T15:54:40.013578+00:00",
            "message": "Eof encountered"
          },
          {
            "date": "2022-05-09T15:54:45.014154+00:00",
            "message": "Eof encountered"
          }
        ],
        "connectionTime": None,
        "lastTransmittedTime": "2022-05-09T15:54:45.122669+00:00",
        "epoch": "2022-05-09T15:54:35.012796+00:00",
        "connectionResetCount": 3,
        "streamingEndpoint": {
          "hostname": "100.123.0.8",
          "protocol": "protoBufOverTcp",
          "port": 64428
        },
        "dnsLog": [],
        "connected": False,
        "disconnectionTime": "2022-05-09T15:54:45.014146+00:00"
      },
      "streaming_type": "events",
      "sequencing_mode": "sequenced",
      "protocol": "protoBufOverTcp",
      "hostname": "100.123.0.8",
      "port": 64428,
      "id": "d8f5a012-232c-4aca-b5c9-637dbba8cb4b"
    }
  ]
}

def test_add_endpoint():
    mgr.add_endpoint("fakehost", "fakeport", "faketype")
    mock_rest.json_resp_post.assert_called_with(uri='/api/streaming-config', data={'hostname': 'fakehost', 'port': 'fakeport', 'streaming_type': 'faketype', 'sequencing_mode': 'sequenced', 'protocol': 'protoBufOverTcp'})

def test_delete_endpoints():
    mgr.delete_all_endpoints()
    mock_rest.delete.assert_called()

def test_get_endpoints():
    r = mgr.get_endpoints()
    assert len(r) == 3
    mock_rest.json_resp_get.assert_called()

