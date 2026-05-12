# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Ubiquity Press
#
# Invenio-Bulk-Importer is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
#

"""Importer task and record links."""

from invenio_records_resources.services.base.links import EndpointLink


class ImporterEndpointLink(EndpointLink):
    """Endpoint link for importer tasks and records.

    Maps the route's ``pid_value`` to ``record.id`` and skips emission for
    drafts that don't yet have a persistent ID assigned.
    """

    @staticmethod
    def vars(record, vars):
        """Variables for the URI template."""
        # Some records don't have record.pid.pid_value yet (e.g. drafts)
        pid_value = getattr(record, "pid", None)
        if pid_value:
            vars.update({"pid_value": record.id})
