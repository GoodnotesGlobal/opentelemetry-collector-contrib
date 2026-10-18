import contextlib
import http.client
import json
import pathlib
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True).strip()


def wait(check):
    deadline = time.monotonic() + 60
    while True:
        try:
            return check()
        except (OSError, http.client.HTTPException, AssertionError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.25)


@contextlib.contextmanager
def container(*args):
    identifier = docker("run", "-d", *args)
    try:
        yield identifier
    except BaseException:
        subprocess.run(["docker", "logs", identifier], check=False)
        raise
    finally:
        docker("rm", "-f", identifier)


def mapped_port(identifier, port):
    return docker("port", identifier, f"{port}/tcp").rsplit(":", 1)[1]


def verify(image, network, version):
    with container(
        "--network", network, "--network-alias", "clickhouse", "--memory=1g",
        "-p", "127.0.0.1::8123", "-e", "CLICKHOUSE_USER=fixture",
        "-e", "CLICKHOUSE_PASSWORD=fixture",
        "-e", "CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1",
        f"clickhouse/clickhouse-server:{version}",
    ) as clickhouse:
        def query(sql):
            request = urllib.request.Request(
                "http://127.0.0.1:" + mapped_port(clickhouse, 8123), sql.encode(),
                headers={"X-ClickHouse-User": "fixture", "X-ClickHouse-Key": "fixture"},
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.read().decode()

        wait(lambda: query("SELECT 1"))
        for schema in ["map", "json"]:
            for protocol, port in [("tcp", 9000), ("http", 8123)]:
                database = f"fixture_{schema}_{protocol}"
                config = {
                    "receivers": {"otlp": {"protocols": {"http": {"endpoint": "0.0.0.0:4318"}}}},
                    "exporters": {"clickhouse": {
                        "endpoint": f"{protocol}://clickhouse:{port}",
                        "username": "fixture", "password": "fixture", "database": database,
                        "create_schema": True, "ttl": "0s",
                        "connection_params": {"enable_json_type": "1", "output_format_native_write_json_as_string": "1"},
                    }},
                    "service": {"pipelines": {"logs": {"receivers": ["otlp"], "exporters": ["clickhouse"]}}},
                }
                with tempfile.TemporaryDirectory() as directory:
                    path = pathlib.Path(directory) / "config.json"
                    path.write_text(json.dumps(config))
                    path.chmod(0o644)
                    with container(
                        "--network", network, "-p", "127.0.0.1::4318",
                        "-v", f"{path}:/config.json:ro", image, "--config=/config.json",
                        f"--feature-gates={'+' if schema == 'json' else '-'}clickhouse.json",
                    ) as collector:
                        endpoint = "http://127.0.0.1:" + mapped_port(collector, 4318) + "/v1/logs"

                        def send(body):
                            request = urllib.request.Request(endpoint, json.dumps(body).encode(), headers={"Content-Type": "application/json"})
                            with urllib.request.urlopen(request, timeout=5) as response:
                                result = json.load(response)
                            assert not result.get("partialSuccess"), result
                            return result

                        wait(lambda: send({"resourceLogs": []}))
                        fixtures = [
                            (1750000000123456789, 1750000000987654321),
                            (0, 1750000000987654321),
                            (1750000000123456789, 0),
                        ]
                        records = []
                        for index, (event, observed) in enumerate(fixtures):
                            record = {"eventName": "browser.web_vital", "body": {"stringValue": str(index)}}
                            if event:
                                record["timeUnixNano"] = str(event)
                            if observed:
                                record["observedTimeUnixNano"] = str(observed)
                            records.append(record)
                        send({"resourceLogs": [{"scopeLogs": [{"logRecords": records}]}]})

                        def read():
                            rows = json.loads(query(
                                "SELECT toString(toUnixTimestamp64Nano(Timestamp)) AS event, "
                                "toString(toUnixTimestamp64Nano(ObservedTimestamp)) AS observed, EventName "
                                f"FROM {database}.otel_logs ORDER BY Body FORMAT JSON"
                            ))["data"]
                            assert len(rows) == len(fixtures), rows
                            return rows

                        rows = wait(read)
                        assert [(int(row["event"]), int(row["observed"]), row["EventName"]) for row in rows] == [
                            (event or observed, observed, "browser.web_vital") for event, observed in fixtures
                        ], rows
                        print(json.dumps({"clickhouse": version, "schema": schema, "protocol": protocol, "rows": rows}), flush=True)


network = "gateway-roundtrip-" + uuid.uuid4().hex
docker("network", "create", network)
try:
    for version in ["25.8-alpine", "25.3-alpine"]:
        verify(sys.argv[1], network, version)
finally:
    docker("network", "rm", network)
