# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 Ubiquity Press.
#
# Invenio-Bulk-Importer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""In-process fakes for the remote file origins supported by the importer.

``FileMixin`` in :mod:`invenio_bulk_importer.record_types.base` reads files
from HTTP(S) URLs, S3 and Google Cloud Storage. Tests must never reach the
real services for those, so this module provides the fixture payloads, the
fake locations that replace the live ones, and a stand-in GCS client.

HTTP is served by ``responses`` and S3 by ``moto``; only GCS needs a
hand-written double, as there is no in-process emulator for it.
"""

from io import BytesIO
from urllib.parse import urlparse

S3_BUCKET = "bulk-importer-test"
"""Bucket created in the ``moto`` backend."""

GS_BUCKET = "bulk-importer-test"
"""Bucket served by :class:`FakeGCSClient`."""

URL_CONTENT = b'{"slideshow": {"author": "Yours Truly", "title": "Sample"}}'
"""Body returned for :data:`URL_FILE`."""

S3_CONTENT = b'{"key": "help", "value": "S3 fixture content"}'
"""Body stored at :data:`S3_FILE`."""

GS_CONTENT = b"<html><body>GCS fixture</body></html>"
"""Body stored at :data:`GS_FILE`."""

LOCAL_FILE = "fixture.txt"
"""Key of the ``local`` origin file, held in the importer task bucket."""

LOCAL_CONTENT = b"Local fixture content for the importer task bucket.\n"
"""Body stored at :data:`LOCAL_FILE`."""

URL_FILE = "https://files.test/article.json"
"""Reachable HTTP file, replaces the former public echo-service dependency."""

URL_FILE_MISSING = "https://files.test/missing.json"
"""HTTP file that responds ``404``."""

S3_FILE = f"s3://{S3_BUCKET}/fixtures/key_help.json"
"""Reachable S3 file."""

S3_FILE_MISSING = f"s3://{S3_BUCKET}/fixtures/missing.json"
"""S3 key that does not exist."""

GS_FILE = f"gs://{GS_BUCKET}/storage/static-hosting/index.html"
"""Reachable GCS file."""

GS_FILE_MISSING = f"gs://{GS_BUCKET}/missing.pdf"
"""GCS blob that does not exist."""

GS_BLOBS = {urlparse(GS_FILE).path.lstrip("/"): GS_CONTENT}
"""Blob name to content mapping served by :class:`FakeGCSClient`."""

URL_FILE_KEY = URL_FILE.rsplit("/", 1)[-1]
"""File key the importer derives from :data:`URL_FILE`."""

S3_FILE_KEY = S3_FILE.rsplit("/", 1)[-1]
"""File key the importer derives from :data:`S3_FILE`."""

GS_FILE_KEY = GS_FILE.rsplit("/", 1)[-1]
"""File key the importer derives from :data:`GS_FILE`."""


class FakeGCSBlob:
    """Stand-in for :class:`google.cloud.storage.blob.Blob`.

    Only implements the surface ``FileMixin`` touches: existence checks,
    metadata reload, ``size`` and opening a binary stream.
    """

    def __init__(self, name, content=None):
        """Initialize the blob.

        :param name: Blob name within the bucket.
        :param content: Blob content, or ``None`` when the blob is absent.
        """
        self.name = name
        self._content = content

    def exists(self):
        """Check whether the blob exists.

        :return: ``True`` when the blob has content.
        """
        return self._content is not None

    def reload(self):
        """Refresh the blob metadata.

        Metadata is always current on the fake, so this is a no-op.
        """

    @property
    def size(self):
        """Size of the blob in bytes.

        :return: Byte count, or ``None`` when the blob is absent.
        """
        return None if self._content is None else len(self._content)

    def open(self, mode="rb"):
        """Open a stream on the blob content.

        :param mode: Only binary reads are supported.
        :return: A file-like object over the blob content.
        """
        if mode != "rb":
            raise ValueError(f"Unsupported mode: {mode}")
        if self._content is None:
            raise FileNotFoundError(self.name)
        return BytesIO(self._content)


class FakeGCSBucket:
    """Stand-in for :class:`google.cloud.storage.bucket.Bucket`."""

    def __init__(self, name, blobs):
        """Initialize the bucket.

        :param name: Bucket name.
        :param blobs: Mapping of blob name to content.
        """
        self.name = name
        self._blobs = blobs

    def blob(self, blob_name):
        """Get a blob from the bucket.

        :param blob_name: Name of the blob.
        :return: A :class:`FakeGCSBlob`, empty when the name is unknown.
        """
        return FakeGCSBlob(blob_name, self._blobs.get(blob_name))


class FakeGCSClient:
    """Stand-in for :class:`google.cloud.storage.Client`."""

    def __init__(self, blobs=None):
        """Initialize the client.

        :param blobs: Mapping of blob name to content, defaults to
            :data:`GS_BLOBS`.
        """
        self._blobs = GS_BLOBS if blobs is None else blobs

    def bucket(self, bucket_name):
        """Get a bucket by name.

        :param bucket_name: Name of the bucket.
        :return: A :class:`FakeGCSBucket`. Unknown buckets are served empty,
            mirroring the lazy behaviour of the real client.
        """
        blobs = self._blobs if bucket_name == GS_BUCKET else {}
        return FakeGCSBucket(bucket_name, blobs)
