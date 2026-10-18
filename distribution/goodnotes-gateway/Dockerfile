FROM --platform=$BUILDPLATFORM golang:1.26.1-bookworm@sha256:ab3d6955bbc813a0f3fdf220c1d817dd89c0b3f283777db8ece4a32fe7858edd AS build
ARG TARGETOS
ARG TARGETARCH
WORKDIR /src
COPY . .
RUN go run go.opentelemetry.io/collector/cmd/builder@v0.141.0 --config builder.yaml --skip-compilation
RUN cd build && CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -trimpath -ldflags='-s -w -buildid=' -o /otelcol-contrib .

FROM gcr.io/distroless/static-debian12:nonroot@sha256:afa5c872c891853ca7fcf1f12c3edb23f7eeef36189728842dd51042ff57f7ab
COPY --from=build /otelcol-contrib /otelcol-contrib
ENTRYPOINT ["/otelcol-contrib"]
