"""
(c) 2017 DigitalOcean

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This file has been modified by NetworktoCode, LLC.
"""

from packaging import version
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from pynautobot.core.query import Request
from pynautobot.core.app import App, PluginsApp
from pynautobot.core.graphql import GraphQLQuery


class Api(object):
    """The API object is the point of entry to pynautobot.

    After instantiating the Api() with the appropriate named arguments
    you can specify which app and endpoint you wish to interact with.

    Valid attributes currently are:
        * dcim
        * ipam
        * circuits
        * tenancy
        * extras
        * virtualization
        * users

    Calling any of these attributes will return
    :py:class:`.App` which exposes endpoints as attributes.

    **Additional Attributes**:
        *  **http_session(requests.Session)**:
                Override the default session with your own. This is used to control
                a number of HTTP behaviors such as SSL verification, custom headers,
                retires, and timeouts.
                See `custom sessions <advanced.html#custom-sessions>`__ for more info.

    :param str url: The base URL to the instance of Nautobot you
        wish to connect to.
    :param str token: Your Nautobot token.
    :param bool,optional threading: Set to True to use threading in ``.all()``
        and ``.filter()`` requests.
    :param int,optional max_workers: Set the maximum workers for threading in ``.all()``
        and ``.filter()`` requests.
    :param str,optional api_version: Set to override the default Nautobot REST API Version
        for all requests.
    :param int,optional retries: Number of retries, for HTTP codes 429, 500, 502, 503, 504,
        this client will try before dropping.
    :param bool,optional verify: SSL cert verification.
    :raises AttributeError: If app doesn't exist.
    :Examples:

    >>> import pynautobot
    >>> nb = pynautobot.api(
    ...     'http://localhost:8000',
    ...     token='d6f4e314a5b5fefd164995169f28ae32d987704f'
    ... )
    >>> nb.dcim.devices.all()
    """

    def __init__(
        self,
        url,
        token=None,
        threading=False,
        max_workers=4,
        api_version=None,
        retries=0,
        verify=True,
    ):
        base_url = "{}/api".format(url if url[-1] != "/" else url[:-1])
        self.token = token
        self.headers = {"Authorization": f"Token {self.token}"}
        self.base_url = base_url
        self.http_session = requests.Session()
        self.http_session.verify = verify
        if retries:
            _adapter = HTTPAdapter(
                max_retries=Retry(
                    total=retries,
                    backoff_factor=1,
                    allowed_methods=None,
                    status_forcelist=[429, 500, 502, 503, 504],
                )
            )
            self.http_session.mount("http://", _adapter)
            self.http_session.mount("https://", _adapter)
        self.threading = threading
        self.max_workers = max_workers
        self.api_version = api_version

        self.dcim = App(self, "dcim")
        self.ipam = App(self, "ipam")
        self.circuits = App(self, "circuits")
        self.tenancy = App(self, "tenancy")
        self.extras = App(self, "extras")
        self.virtualization = App(self, "virtualization")
        self.users = App(self, "users")
        self.plugins = PluginsApp(self)
        self.graphql = GraphQLQuery(self)
        self._validate_version()

    def _validate_version(self):
        """Validate API version if eq or ge than 2.0 raise an error."""
        api_version = self.version
        if api_version.replace(".", "").isnumeric() and version.parse(api_version) < version.parse("2.0"):
            raise ValueError("Nautobot version 1 detected, please downgrade pynautobot to version 1.x")

    @property
    def version(self):
        """Gets the API version of Nautobot.

        Can be used to check the Nautobot API version if there are
        version-dependent features or syntaxes in the API.

        :Returns: Version number as a string.
        :Example:

        >>> import pynautobot
        >>> nb = pynautobot.api(
        ...     'http://localhost:8000',
        ...     token='d6f4e314a5b5fefd164995169f28ae32d987704f'
        ... )
        >>> nb.version
        '1.0'
        >>>
        """
        return Request(
            base=self.base_url,
            http_session=self.http_session,
            api_version=self.api_version,
            token=self.token,
        ).get_version()

    def openapi(self):
        """Returns the OpenAPI spec.

        Quick helper function to pull down the entire OpenAPI spec.

        :Returns: dict
        :Example:

        >>> import pynautobot
        >>> nb = pynautobot.api(
        ...     'http://localhost:8000',
        ...     token='d6f4e314a5b5fefd164995169f28ae32d987704f'
        ... )
        >>> nb.openapi()
        {...}
        >>>
        """
        return Request(
            base=self.base_url,
            http_session=self.http_session,
            api_version=self.api_version,
            token=self.token,
        ).get_openapi()

    def status(self):
        """Gets the status information from Nautobot.

        Available in Nautobot 2.10.0 or newer.

        :Returns: Dictionary as returned by Nautobot.
        :Raises: :py:class:`.RequestError` if the request is not successful.
        :Example:

        >>> pprint.pprint(nb.status())
        {'django-version': '3.1.3',
         'installed-apps': {'cacheops': '5.0.1',
                            'debug_toolbar': '3.1.1',
                            'django_filters': '2.4.0',
                            'django_prometheus': '2.1.0',
                            'django_rq': '2.4.0',
                            'django_tables2': '2.3.3',
                            'drf_yasg': '1.20.0',
                            'mptt': '0.11.0',
                            'rest_framework': '3.12.2',
                            'taggit': '1.3.0',
                            'timezone_field': '4.0'},
         'nautobot-version': '1.0.0',
         'plugins': {},
         'python-version': '3.7.3',
         'rq-workers-running': 1}
        >>>
        """
        return Request(
            base=self.base_url,
            token=self.token,
            http_session=self.http_session,
            api_version=self.api_version,
        ).get_status()
