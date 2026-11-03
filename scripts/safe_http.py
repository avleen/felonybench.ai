"""Limits on what fetching a URL can read into memory."""
import urllib.request


class NoDrainRedirects(urllib.request.HTTPRedirectHandler):
    """urllib reads a redirect's whole body, with no limit, before following it. Nobody needs that body."""

    def http_error_302(self, req, fp, code, msg, headers):
        fp.close()
        return super().http_error_302(req, fp, code, msg, headers)

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302
