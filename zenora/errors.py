# Copyright (c) 2021 DevGuyAhnaf

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from zenora.exceptions import (
    APIError,
    AuthenticationError,
    CloudflareException,
    RateLimitException,
)
from zenora.routes import BASE_URL

import json
import typing
import requests


def raise_error_or_return(r: requests.Response) -> typing.Optional[dict]:
    try:
        json_data = r.json()
    except json.decoder.JSONDecodeError:
        raise CloudflareException("Cloudflare blocking API request to Discord")
    if not r.ok:
        if "X-RateLimit-Bucket" in r.headers:  # Rate limited
            throw_rate_limit_error(r)
        elif r.status_code == 401:  # Unauthorized
            raise AuthenticationError(json_data["message"])
        else:
            if "error" in json_data:
                raise APIError(f"{json_data['error_description']}")
            for x in json_data["errors"]:
                if "_errors" in json_data["errors"][x]:
                    msg = json_data["errors"][x]["_errors"][0]["message"]
                else:
                    msg = json_data["errors"][x][0]["message"]
                raise APIError(f"Code {json_data['code']}. Message: {msg}")
    else:
        return json_data


def throw_rate_limit_error(r: requests.Response):
    data = r.json()

    if data.get("global"):
        raise RateLimitException(
            f"Being rate limited globally, will reset after {data['retry_after']}s.",
            r.headers,
        )

    raise RateLimitException(
        f"Being rate limited on {r.url.replace(BASE_URL, '')}, will reset after {data['retry_after']}s. Bucket: {r.headers['X-RateLimit-Bucket']}",
        r.headers,
    )
