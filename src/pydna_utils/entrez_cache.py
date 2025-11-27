#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""""Monkeypatching urlopen"""

import requests
import requests_cache
import urllib.request
import Bio.Entrez
from pathlib import Path
import email.message
from pydna_utils.settings import load_settings

cache_name="ncbi_cache"
backend = "sqlite"
cfg = load_settings()
cache_path = Path(cfg.pydna_ncbi_cache_dir)/cache_name
expire_after = int(cfg.pydna_ncbi_expiration)


def enable_entrez_cache(
    cache_path=cache_path,
    expire_after=expire_after,
):
    """Transparent caching for Bio.Entrez using requests_cache."""

    # Install requests_cache
    requests_cache.install_cache(
        str(cache_path),
        backend=backend,
        expire_after=expire_after
    )

    # Monkeypatched urlopen
    def cached_urlopen(request, *args, **kwargs):
        url = getattr(request, "full_url", request)
        headers = getattr(request, "headers", {})

        resp = requests.get(url, headers=headers, stream=True)
        resp.raw.decode_content = True

        # Build a fake urllib-style response wrapper
        class FakeHTTPResponse:
            def __init__(self, resp):
                self.resp = resp
                self.url = resp.url
                self.fp = resp.raw

                # Convert requests headers → email.message.Message
                msg = email.message.Message()
                for k, v in resp.headers.items():
                    msg[k] = v
                self.headers = msg

            # --- REQUIRED FOR TextIOWrapper ---
            def readable(self):
                return True

            def writable(self):
                return False

            def seekable(self):
                return False

            # --- OPTIONAL BUT SAFE ---
            def close(self):
                return self.fp.close()

            def flush(self):
                return None

            def fileno(self):
                # TextIOWrapper may call this
                try:
                    return self.fp.fileno()
                except Exception:
                    raise OSError("fileno not supported")

            # --- CORE DATA METHODS ---
            def read(self, *a, **kw):
                return self.fp.read(*a, **kw)

            def readline(self, *a, **kw):
                return self.fp.readline(*a, **kw)

            def readinto(self, b):
                return self.fp.readinto(b)

            # --- Required by urllib-like interface ---
            def info(self):
                return self.headers

            def geturl(self):
                return self.url

            @property
            def closed(self):
                return self.fp.closed

        return FakeHTTPResponse(resp)

    # Patch both urlopen references
    urllib.request.urlopen = cached_urlopen
    Bio.Entrez.__dict__["urlopen"] = cached_urlopen

    return cache_path.with_suffix(".sqlite")
