FROM ghcr.io/make87/rust:1-bookworm AS build-image

RUN apt-get update \
    && apt install --no-install-suggests --no-install-recommends -y \
        jq \
        build-essential \
        cmake \
        nasm \
        libavutil-dev \
        libavformat-dev \
        libavfilter-dev \
        libavdevice-dev \
        libclang-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY Cargo.toml .
COPY src ./src

# Install dependencies for examples
RUN cargo build --release

# Extract the binary name using cargo metadata and jq
# and copy the binary to /binary
RUN binary_name=$(cargo metadata --format-version=1 --no-deps | \
    jq -r '.packages[].targets[] | select(.kind[] == "bin") | .name') \
    && echo "Binary name: $binary_name" \
    && cp target/release/$binary_name /main

FROM ghcr.io/make87/ffmpeg:7.1.1

COPY --from=bluenviron/mediamtx:1.12.2 /mediamtx /mediamtx

WORKDIR /app

# Copy the workspace from the builders
COPY --from=build-image /main /app/main
COPY mediamtx.yml /app/mediamtx.yml

CMD ["/app/main"]