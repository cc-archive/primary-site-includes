#!/usr/bin/env python3
# vim: set fileencoding=utf-8:

"""
Build creativecommons.org primary site includes (scripts, styles, navigation
header, and navigation footer) based on WordPress REST API
"""

# Standard library
import argparse
import copy
import os
import sys
import traceback

# Third-party
import colorama
import jinja2
import requests


colorama.init()
C_GRAY = f"{colorama.Style.DIM}{colorama.Fore.WHITE}"
C_RESET = colorama.Style.RESET_ALL
C_WHITE = f"{colorama.Style.BRIGHT}{colorama.Fore.WHITE}"
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
REQUESTS_TIMEOUT = 5


class ScriptError(Exception):
    def __init__(self, message, code=None):
        self.code = code if code else 1
        message = "({}) {}".format(self.code, message)
        super(ScriptError, self).__init__(message)


def debug_function_name(args, name):
    if args.debug:
        print()
        print()
        print(f"{C_WHITE}## {name}{C_RESET}")


def process_header_footer_data(args, data_full):
    data_path = copy.deepcopy(data_full)
    info = [["ID", "Title", "Uniform Resource Locator (URL)"]]
    prefix = f"https://{args.domain}"
    for index, header in enumerate(data_full):
        id_ = header["ID"]
        title = header["title"]
        url_full = header["url"]
        url_path = remove_prefix(copy.copy(url_full), prefix)
        data_path[index]["url"] = url_path
        info_url = url_full
        if url_full != url_path:
            info_url = f"{C_GRAY}https://{args.domain}{C_RESET}{url_path}"
        info.append([id_, title, info_url])
    debug_info(args, info)
    data_full = {"prefix": prefix, "json": data_full}
    data_path = {"prefix": "", "json": data_path}
    return data_full, data_path


def process_scripts_styles_data(args, data_full):
    data_path = copy.deepcopy(data_full)
    info = [["ID", "Uniform Resource Locator (URL)"]]
    prefix = f"https://{args.domain}"
    for id_, url_full in data_full.items():
        url_path = remove_prefix(copy.copy(url_full), prefix)
        data_path[id_] = url_path
        info_url = url_full
        if url_full != url_path:
            info_url = f"{C_GRAY}https://{args.domain}{C_RESET}{url_path}"
        info.append([id_, info_url])
    debug_info(args, info)
    data_full = {"prefix": prefix, "json": data_full}
    data_path = {"prefix": "", "json": data_path}
    return data_full, data_path


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix) :]  # noqa: E203
    return text


def debug_info(args, info):
    if not args.debug:
        return
    print()
    print(list_of_lists_to_md_table(info))
    print()


def render_write_include(args, type_, file_name, data, write_file=True):
    template = args.j2env.get_template(file_name)
    rendered = template.render(data=data).strip()
    if type_ == "full":
        message = "- Data includes full CC URLs"
        directory = "includes_full"
    elif type_ == "path":
        message = "- Data includes path-only CC URLs"
        directory = "includes_path"
    else:
        raise ScriptError(
            f"Invalid type_ argument (must be 'full' or 'path'): {type_}", 1
        )
    if args.debug:
        print(message)
        print(f"  - Template: templates/{file_name}")
    include_file = os.path.join(directory, file_name)
    if write_file:
        with open(include_file, "w", encoding="utf-8") as file_out:
            file_out.write(f"{rendered}\n")
        if args.debug:
            print(f"  - Written to file: {include_file}")
    else:
        return rendered


def list_of_lists_to_md_table(rows):
    """Convert a list (rows) of lists (columns) to a Markdown table.

    The last (right-most) column will not have any trailing whitespace so that
    it wraps as cleanly as possible.

    Based on solution provided by antak in http://stackoverflow.com/a/12065663
    CC-BY-SA 4.0 (International)
    https://creativecommons.org/licenses/by-sa/4.0/
    """
    lines = []
    widths = [max(map(len, map(str, col))) for col in zip(*rows)]

    for r, row in enumerate(rows):
        formatted = []
        last_col = len(row) - 1
        for i, col in enumerate(row):
            if i == last_col:
                formatted.append(str(col))
            else:
                formatted.append(str(col).ljust(widths[i]))
        lines.append(f"| {' | '.join(formatted)} |")

    formatted = []
    last_col = len(rows[0]) - 1
    for i, col in enumerate(rows[0]):
        if i == last_col:
            formatted.append("-" * (len(col)))
        else:
            formatted.append("-" * widths[i])
    lines.insert(1, f"| {' | '.join(formatted)} |")

    return "\n".join(lines)


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
            "FAILED to retrieve data due to ConnectionError for url:"
            f" {end_url}",
            1,
        )
    except requests.exceptions.Timeout:
        raise ScriptError(
            f"FAILED to retrieve data due to Timeout for url: {end_url}", 1,
        )
    return fetched_data


def prime_style_script_cache(args):
    """Prime script/style cache
    """
    request_data(args, f"https://{args.domain}/", json=False)


def format_ccnavigation_header(args, data):
    debug_function_name(args, sys._getframe(0).f_code.co_name)
    data_full, data_path = process_header_footer_data(args, data)
    render_write_include(args, "full", "site-header.html", data_full)
    render_write_include(args, "path", "site-header.html", data_path)


def format_ccnavigation_footer(args, data):
    debug_function_name(args, sys._getframe(0).f_code.co_name)
    data_full, data_path = process_header_footer_data(args, data)
    render_write_include(args, "full", "site-footer.html", data_full)
    render_write_include(args, "path", "site-footer.html", data_path)


def format_cc_wpscripts(args, data):
    debug_function_name(args, sys._getframe(0).f_code.co_name)
    data_full, data_path = process_scripts_styles_data(args, data)
    rendered = render_write_include(
        args, "full", "footer-scripts.html", data_full, write_file=False
    )
    footer_file = os.path.join("includes_full", "site-footer.html")
    with open(footer_file, "a", encoding="utf-8") as file_out:
        file_out.write(f"{rendered}\n")
    if args.debug:
        print(f"  - Appended to file: {footer_file}")
    render_write_include(
        args, "path", "footer-scripts.html", data_path, write_file=False
    )
    footer_file = os.path.join("includes_path", "site-footer.html")
    with open(footer_file, "a", encoding="utf-8") as file_out:
        file_out.write(f"{rendered}\n")
    if args.debug:
        print(f"  - Appended to file: {footer_file}")


def format_cc_wpstyles(args, data):
    debug_function_name(args, sys._getframe(0).f_code.co_name)
    data_full, data_path = process_scripts_styles_data(args, data)
    render_write_include(args, "full", "html-head.html", data_full)
    render_write_include(args, "path", "html-head.html", data_path)


def main():
    args = setup()
    j2loader = jinja2.FileSystemLoader("templates")
    args.j2env = jinja2.Environment(loader=j2loader)
    prime_style_script_cache(args)
    for endpoint in ENDPOINTS:
        end_url = f"https://{args.domain}{endpoint}"
        format_function = f"format_{endpoint.split('/')[2].replace('-', '_')}"
        data = request_data(args, end_url)
        globals()[format_function](args, data)
    if args.debug:
        print()
        print()


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
