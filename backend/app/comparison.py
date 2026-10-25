"""URL equivalence for contest scoring (PDF p.12), never for HTTP fetching."""
from urllib.parse import parse_qsl, urlsplit


def evaluation_url_key(url):
    parts = urlsplit(url)
    if parts.scheme.lower() not in {'http', 'https'} or not parts.hostname:
        raise ValueError('Evaluation requires an absolute HTTP(S) URL')
    return (parts.netloc.lower(), parts.path.removesuffix('/'),
            tuple(sorted(parse_qsl(parts.query, keep_blank_values=True))))
