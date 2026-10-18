# Goodnotes gateway

This distribution retains Collector 0.136.0 and its stable 1.42.0 modules. It
includes the components used by the fleet gateway, not the node agent or
CloudWatch collector. The ClickHouse exporter is extracted from immutable
upstream commit `7bf85220afc6a650e6a298790d244f3f83f581e6` and patched to preserve
observed timestamps in map and JSON log tables. No other exporter behavior or
component version is changed. Existing tables must have
`ObservedTimestamp DateTime64(9)` before adoption; see the exporter README.

From a full clone of this fork:

```sh
python3 distribution/goodnotes-gateway/prepare.py /tmp/gateway
cd /tmp/gateway/exporter/clickhouseexporter
go mod tidy
go test ./...
go test -tags integration -run '^TestIntegration$/^(25.8|25.3)$/^TestLogs' -count=1
cd /tmp/gateway
docker build -t gateway:test .
docker run --rm gateway:test components
```

The upstream integration harness labels its 25.6-alpine image test `25.8`;
this distribution preserves that existing harness and also tests 25.3.
The regression covers independent nanoseconds, missing event-time fallback,
and missing observed-time zero, with native/HTTP connections and map/JSON tables.

The Goodnotes gateway workflow tests before publishing. Only a manual run on
this fork's `main` with `publish=true` can write packages. It publishes
`ghcr.io/goodnotesglobal/otel-gateway:0.136.0-observed.1-<source-sha>` for
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
