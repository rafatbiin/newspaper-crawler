import hashlib
from urllib.parse import urlparse


class URLProcessor:

    @classmethod
    def get_domain(cls, url):
        url_tokens = urlparse(url)
        domain = url_tokens.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain

    @classmethod
    def get_md5(cls, url):
        m = hashlib.md5()
        m.update(url.encode("utf-8"))
        return m.hexdigest()
