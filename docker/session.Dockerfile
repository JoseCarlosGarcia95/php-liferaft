ARG SDK_IMAGE=scratch
FROM ${SDK_IMAGE} AS session-builder
ARG SOURCE_ARCHIVE
ARG SOURCE_SHA256
ARG SDK_IMAGE_ID
COPY ${SOURCE_ARCHIVE} /tmp/php.tar.xz
COPY docker/build-session.sh /usr/local/bin/build-session
RUN printf '%s  /tmp/php.tar.xz\n' "$SOURCE_SHA256" | sha256sum -c - \
    && SDK_IMAGE_ID="$SDK_IMAGE_ID" sh /usr/local/bin/build-session /tmp/php.tar.xz

FROM scratch AS session-module
COPY --from=session-builder /module/ /
