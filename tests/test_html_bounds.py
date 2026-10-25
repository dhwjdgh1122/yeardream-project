import httpx
import pytest

from backend.app import crawler

CLIENT = httpx.Client


def client_with(monkeypatch, respond):
    transport = httpx.MockTransport(respond)
    monkeypatch.setattr(crawler.httpx, 'Client', lambda **kw: CLIENT(transport=transport, **kw))


def test_non_html_is_rejected_before_reading_body(monkeypatch):
    class Unreadable(httpx.SyncByteStream):
        def __iter__(self):
            pytest.fail('Non-HTML body must not be consumed')
            yield b''
    client_with(monkeypatch, lambda r: httpx.Response(200, stream=Unreadable(), headers={'content-type': 'application/pdf'}))
    with pytest.raises(ValueError, match='HTML'):
        crawler.fetch_html('https://example.com/file')


def test_content_length_and_streamed_size_are_bounded(monkeypatch):
    monkeypatch.setattr(crawler, 'MAX_HTML_BYTES', 10)
    client_with(monkeypatch, lambda r: httpx.Response(200, content=b'x' * 11, headers={'content-type': 'text/html'}))
    with pytest.raises(ValueError, match='한도'):
        crawler.fetch_html('https://example.com/')
    class Chunked(httpx.SyncByteStream):
        def __iter__(self):
            yield b'12345'
            yield b'678901'
    client_with(monkeypatch, lambda r: httpx.Response(200, stream=Chunked(), headers={'content-type': 'text/html'}))
    with pytest.raises(ValueError, match='한도'):
        crawler.fetch_html('https://example.com/')


def test_binary_signature_without_media_type_is_rejected(monkeypatch):
    client_with(monkeypatch, lambda r: httpx.Response(200, content=b'%PDF-1.7 example'))
    with pytest.raises(ValueError, match='파일'):
        crawler.fetch_html('https://example.com/file')


def test_html_attachment_is_not_treated_as_a_page(monkeypatch):
    client_with(monkeypatch, lambda r: httpx.Response(200, content=b'<p>Attachment</p>',
        headers={'content-type': 'text/html', 'content-disposition': 'attachment; filename=a.html'}))
    with pytest.raises(ValueError, match='첨부파일'):
        crawler.fetch_html('https://example.com/file')
