#!/usr/bin/env python3
# vim: set fileencoding=utf-8:

"""
Build creativecommons.org primary site includes (scripts, styles, navigation
header, and navigation footer) based on WordPress REST API
"""

# Standard library
from pprint import pprint  # DEBUG/TODO
import argparse
import os
import sys
import traceback

# Third-party
import jinja2
import requests


DOMAINS = {
    "prod": "creativecommons.org",
    "stage": "stage.creativecommons.org",
}
ENDPOINTS = [
    "/wp-json/ccnavigation-header/menu",
    "/wp-json/ccnavigation-footer/menu",
    "/wp-json/cc-wpscripts/get",
    "/wp-json/cc-wpstyles/get",
]
REQUESTS_TIMEOUT = 3


class ScriptError(Exception):
    def __init__(self, message, code=None):
        self.code = code if code else 1
        message = "({}) {}".format(self.code, message)
        super(ScriptError, self).__init__(message)


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def setup():
    """Instantiate and configure argparse and logging.

    Return argsparse namespace.
    """

    def default_from_env(ENV_KEY):
        default_value = None
        if ENV_KEY in os.environ and os.environ[ENV_KEY]:
            default_value = os.environ[ENV_KEY]
        return default_value

    default_password = default_from_env("FETCH_PASSWORD")
    default_username = default_from_env("FETCH_USERNAME")

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="debug mode: list changes without modification",
    )
    ap.add_argument(
        "--domain", default=DOMAINS["prod"], help=argparse.SUPPRESS,
    )
    ap.add_argument(
        "env",
        help="specify which environment to fetch from",
        choices=["prod", "stage"],
    )
    ap.add_argument(
        "-p",
        "--password",
        default=default_password,
        help=(
            "HTTP Basic Auth password (required with 'stage' environment)."
            " The FETCH_PASSWORD environment variable may also be used."
        ),
    )
    ap.add_argument(
        "-u",
        "--username",
        default=default_username,
        help=(
            "HTTP Basic Auth username (required with 'stage' environment)."
            " The FETCH_PASSWORD environment variable may also be used."
        ),
    )

    args = ap.parse_args()
    args.domain = DOMAINS[args.env]
    if args.env == "prod" and (args.username or args.password):
        ap.error(
            "the 'prod' environment does not use HTTP Basic Auth: do not use"
            " the --username and --password options"
        )
    if args.env == "stage" and (not args.username or not args.password):
        ap.error(
            "the 'stage' environment requires both the --username and"
            " --password options for HTTP Basic Auth"
        )
    return args


def request_data(args, end_url, json=True):
    auth = None
    if args.username and args.password:
        auth = requests.auth.HTTPBasicAuth(args.username, args.password)
    try:
        response = requests.get(end_url, auth=auth, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()
        if json:
            fetched_data = response.json()
        else:
            fetched_data = response.content
    except requests.HTTPError as e:
        raise ScriptError(f"FAILED to retrieve data due to HTTP {e}", 1)
    except requests.exceptions.ConnectionError:
        raise ScriptError(
            f"FAILED to retrieve data due to ConnectionError for url:"
            " {end_url}",
            1,
        )
    except requests.exceptions.Timeout:
        raise ScriptError(
            f"FAILED to retrieve data due to Timeout for url: {end_url}", 1,
        )
    return fetched_data


def prime_style_script_cache(args):
    # Prime script/style cache
    __ = request_data(args, f"https://{args.domain}/", json=False)


def format_ccnavigation_header(args, j2env, data):
    print("###", sys._getframe(0).f_code.co_name)  # DEBUG/TODO
    for index, header in enumerate(data):
        data[index]["url"] = remove_prefix(
            header["url"], f"https://{args.domain}"
        )
    template = j2env.get_template("site-header.html")
    rendered = template.render(data=data)
    print(rendered)  # DEBUG/TODO
    print()  # DEBUG/TODO


def format_ccnavigation_footer(args, j2env, data):
    print("###", sys._getframe(0).f_code.co_name)  # DEBUG/TODO
    for header in data:  # DEBUG/TODO
        print(  # DEBUG/TODO
            f"ID: {header['ID']}, title: {header['title']},"  # DEBUG/TODO
            f" url: {header['url']}"  # DEBUG/TODO
        )  # DEBUG/TODO
    print()  # DEBUG/TODO


def format_cc_wpscripts(args, j2env, data):
    print("###", sys._getframe(0).f_code.co_name)  # DEBUG/TODO
    print()  # DEBUG/TODO


def format_cc_wpstyles(args, j2env, data):
    print("###", sys._getframe(0).f_code.co_name)  # DEBUG/TODO
    print()  # DEBUG/TODO


def main():
    args = setup()
    j2loader = jinja2.FileSystemLoader("templates")
    j2env = jinja2.Environment(loader=j2loader)
    prime_style_script_cache(args)
    for endpoint in ENDPOINTS:
        end_url = f"https://{args.domain}{endpoint}"
        format_function = f"format_{endpoint.split('/')[2].replace('-', '_')}"
        data = request_data(args, end_url)
        globals()[format_function](args, j2env, data)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        sys.exit(e.code)
    except KeyboardInterrupt:
        print("INFO (130) Halted via KeyboardInterrupt.", file=sys.stderr)
        sys.exit(130)
    except ScriptError:
        error_type, error_value, error_traceback = sys.exc_info()
        print("CRITICAL {}".format(error_value), file=sys.stderr)
        sys.exit(error_value.code)
    except:  # noqa: ignore flake8: E722 do not use bare 'except'
        print("ERROR (1) Unhandled exception:", file=sys.stderr)
        print(traceback.print_exc(), file=sys.stderr)
        sys.exit(1)
