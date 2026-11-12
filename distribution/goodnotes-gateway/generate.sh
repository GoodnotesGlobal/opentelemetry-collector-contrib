#!/bin/sh
# Generates the collector sources into ./build, then raises shared dependencies
# to versions with fixes for advisories reachable from the gateway. Collector
# components stay on 0.141.0; only libraries they import move. Raise a version
# here when the gateway workflow's govulncheck step reports a new advisory.
set -eu
go run go.opentelemetry.io/collector/cmd/builder@v0.141.0 --config builder.yaml --skip-compilation
cd build
go get \
  github.com/andybalholm/brotli@v1.2.7 \
  github.com/antchfx/xpath@v1.3.6 \
  github.com/expr-lang/expr@v1.17.7 \
  github.com/klauspost/compress@v1.20.3 \
  go.opentelemetry.io/contrib/bridges/otelzap@v0.21.0 \
  go.opentelemetry.io/contrib/otelconf@v0.27.0 \
  go.opentelemetry.io/otel@v1.47.0 \
  go.opentelemetry.io/otel/sdk@v1.47.0 \
  golang.org/x/net@v0.60.0 \
  google.golang.org/grpc@v1.84.0
go mod tidy
