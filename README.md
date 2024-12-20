# session-info2

[![PyPI - Version](https://img.shields.io/pypi/v/session-info2.svg)](https://pypi.org/project/session-info2)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/session-info2.svg)](https://pypi.org/project/session-info2)
[![Docs](https://readthedocs.org/projects/session-info2/badge/)](https://session-info2.readthedocs.io/)

## Installation

```console
pip install session-info2
```

## Usage

See <https://session-info2.readthedocs.io/>
In short:

Import whayever your script/notebook relies on,
as well as [session_info][].

```pycon
>>> httpx
>>> from session_info2 import session_info
```

Some usage examples (see links above for more).
Minimal output:

```pycon
>>> session_info(os=False)
httpx	0.28.1
----	----
Python	3.12.5 (main, Aug  6 2024, 19:08:49) [Clang 16.0.6 ]
Updated	2024-12-20 14:22
```

With indirect dependencies:

```pycon
>>> session_info(dependencies=True)
httpx	0.28.1
----	----
anyio	4.7.0
h11	0.14.0
sniffio	1.3.1
session-info2	0.1.2
certifi	2024.12.14
httpcore	1.0.7
appdirs	1.4.4
----	----
Python	3.12.5 (main, Aug  6 2024, 19:08:49) [Clang 16.0.6 ]
OS	macOS-15.1.1-arm64-arm-64bit
Updated	2024-12-20 14:24
```

[session_info]: https://session-info2.readthedocs.io/en/stable/api.html#session_info2.session_info
