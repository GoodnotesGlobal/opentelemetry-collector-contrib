FROM --platform=$BUILDPLATFORM golang:1.26.11-bookworm@sha256:dc40a13b61304647ed7e5d581d246b86413dfc29d63c6d018310feb93cd98fc0 AS build
ARG TARGETOS
ARG TARGETARCH
WORKDIR /src
COPY . .
RUN sh generate.sh
RUN cd build && CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -trimpath -ldflags='-s -w -buildid=' -o /otelcol-contrib .

FROM gcr.io/distroless/static-debian12:nonroot@sha256:afa5c872c891853ca7fcf1f12c3edb23f7eeef36189728842dd51042ff57f7ab
COPY --from=build /otelcol-contrib /otelcol-contrib
ENTRYPOINT ["/otelcol-contrib"]
