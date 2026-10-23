# Goodnotes gateway

This distribution uses Collector 0.141.0 and its stable 1.47.0 modules. It
includes the components used by the fleet gateway, not the node agent or
CloudWatch collector. The `github` receiver takes GitHub `workflow_run` and
`workflow_job` webhooks and makes CI traces; `github-webhook.test.yaml` is a
webhook-only config that the workflow validates against the built image. The ClickHouse exporter is extracted from immutable
upstream commit `daab18f8a3c556b54492971bcca926910d2adc28` and patched to preserve
observed timestamps in map and JSON log tables. The upstream EventName column
detection and insertion are retained in both formats. All components use the
0.141.0 release and OCB 0.141.0. Existing tables must have
`ObservedTimestamp DateTime64(9)` before adoption; see the exporter README.

From a full clone of this fork:

```sh
python3 distribution/goodnotes-gateway/prepare.py /tmp/gateway
(cd /tmp/gateway/exporter/clickhouseexporter && go mod tidy && go test ./... && \
  go test -tags integration -run '^TestIntegration$/^(25.8|25.3)$/^TestLogs' -count=1)
docker build -t gateway:test /tmp/gateway
docker run --rm gateway:test components
python3 distribution/goodnotes-gateway/test_roundtrip.py gateway:test
```

The upstream integration harness tests ClickHouse 25.8-alpine and 25.3-alpine.
The regression covers independent nanoseconds, missing event-time fallback,
and missing observed-time zero, with native/HTTP connections and map/JSON
tables. The image roundtrip sends
real OTLP HTTP requests into the built collector and checks those same timestamp
cases together with `EventName = browser.web_vital` across both ClickHouse
versions, both table formats, and both database protocols. An absent observed
time remains zero; it is never substituted with the event time.

The Goodnotes gateway workflow tests before publishing. Only a manual run on
this fork's `main` with `publish=true` can write packages. It publishes
`ghcr.io/goodnotesglobal/otel-gateway:0.141.0-observed.2-<source-sha>` for
linux/amd64 and linux/arm64 and records the immutable manifest digest in the
run summary. Adopt the digest, not a mutable tag. Base images and source are
pinned by digest/commit; Go modules are versioned and verified by Go checksums.

New GHCR packages default to private. The workflow rejects an existing package
with any other visibility and verifies private visibility immediately after
publication. It never changes visibility. The source repository is public;
package access must remain private independently of repository visibility.

Fleet rewrites this path to
`<account>.dkr.ecr.<region>.amazonaws.com/github/goodnotesglobal/otel-gateway`.
The package owner must grant read access to the service user/team owning
`platform/ecr-pullthrough/github-container-registry`, through package settings
or inherited repository access. A successful workflow push proves publisher
access only. Actual ECR pull-through access and gateway config validation must
be verified before deployment. This distribution does not deploy anything.
