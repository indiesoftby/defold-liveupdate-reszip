#!/usr/bin/env python3
# Change log:
# 2026-05-27: Added detection for follow-up API removals:
# - render.draw_debug2d(), removed in defold/defold#12462; use render.draw_debug3d().
# - "set_constant" message id strings, removed in defold/defold#12463; use go.set().
# - spine.set_constant(), removed in defold/extension-spine#278; use go.set().
"""Scan Defold projects for Lua APIs removed by defold/defold#12441 and follow-up PRs."""

from __future__ import annotations

import argparse
import bisect
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import quote, unquote, urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_LUA_SUFFIXES = (
    ".lua",
    ".script",
    ".gui_script",
    ".render_script",
    ".editor_script",
)

DEFAULT_SKIP_DIR_PATTERNS = (
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".gradle",
    "node_modules",
    "build",
    "build-*",
    "dist",
    "out",
    "target",
)


REMOVED_API_MIGRATIONS: tuple[tuple[str, str | None], ...] = (
    ("go.get_scale_vector", "go.get_scale()"),
    ("go.delete_all", "go.delete()"),
    ("camera.acquire_focus", None),
    ("camera.release_focus", None),
    ("label.get_text_metrics", "resource.get_text_metrics()"),
    ("model.play", "model.play_anim()"),
    ("model.set_constant", "go.set()"),
    ("physics.set_listener", "physics.set_event_listener()"),
    ("physics.ray_cast", "physics.raycast_async()"),
    ("spine.set_constant", "go.set()"),
    ("sprite.set_constant", "go.set()"),
    ("tilemap.set_constant", "go.set()"),
    ("gui.cancel_animation", "gui.cancel_animations()"),
    ("gui.get_text_metrics", "resource.get_text_metrics()"),
    ("gui.get_text_metrics_from_node", "resource.get_text_metrics()"),
    ("render.enable_render_target", "render.set_render_target()"),
    ("render.disable_render_target", "render.set_render_target(render.RENDER_TARGET_DEFAULT)"),
    ("render.draw_debug2d", "render.draw_debug3d()"),
    ("vmath.matrix4_from_quat", "vmath.matrix4_quat()"),
    (
        "sys.get_config",
        "sys.get_config_string(), sys.get_config_int(), or sys.get_config_number()",
    ),
    ("render.STATE_DEPTH_TEST", "graphics.STATE_DEPTH_TEST"),
    ("render.STATE_STENCIL_TEST", "graphics.STATE_STENCIL_TEST"),
    ("render.STATE_ALPHA_TEST", "graphics.STATE_ALPHA_TEST"),
    ("render.STATE_BLEND", "graphics.STATE_BLEND"),
    ("render.STATE_CULL_FACE", "graphics.STATE_CULL_FACE"),
    ("render.STATE_POLYGON_OFFSET_FILL", "graphics.STATE_POLYGON_OFFSET_FILL"),
    # The PR table and migrated project files contain both documented names and legacy aliases.
    ("render.FORMAT_LUMINANCE", "graphics.TEXTURE_FORMAT_LUMINANCE"),
    ("render.FORMAT_RGB", "graphics.TEXTURE_FORMAT_RGB"),
    ("render.RGB", "graphics.TEXTURE_FORMAT_RGB"),
    ("render.FORMAT_RGBA", "graphics.TEXTURE_FORMAT_RGBA"),
    ("render.FORMAT_DEPTH", "graphics.TEXTURE_FORMAT_DEPTH"),
    ("render.FORMAT_STENCIL", "graphics.TEXTURE_FORMAT_STENCIL"),
    ("render.FORMAT_RGB16F", "graphics.TEXTURE_FORMAT_RGB16F"),
    ("render.RGB16F", "graphics.TEXTURE_FORMAT_RGB16F"),
    ("render.FORMAT_RGB32F", "graphics.TEXTURE_FORMAT_RGB32F"),
    ("render.RGB32F", "graphics.TEXTURE_FORMAT_RGB32F"),
    ("render.FORMAT_RGBA16F", "graphics.TEXTURE_FORMAT_RGBA16F"),
    ("render.RGBA16F", "graphics.TEXTURE_FORMAT_RGBA16F"),
    ("render.FORMAT_RGBA32F", "graphics.TEXTURE_FORMAT_RGBA32F"),
    ("render.RGBA32F", "graphics.TEXTURE_FORMAT_RGBA32F"),
    ("render.FORMAT_R16F", "graphics.TEXTURE_FORMAT_R16F"),
    ("render.R16F", "graphics.TEXTURE_FORMAT_R16F"),
    ("render.FORMAT_RG16F", "graphics.TEXTURE_FORMAT_RG16F"),
    ("render.RG16F", "graphics.TEXTURE_FORMAT_RG16F"),
    ("render.FORMAT_R32F", "graphics.TEXTURE_FORMAT_R32F"),
    ("render.R32F", "graphics.TEXTURE_FORMAT_R32F"),
    ("render.FORMAT_RG32F", "graphics.TEXTURE_FORMAT_RG32F"),
    ("render.RG32F", "graphics.TEXTURE_FORMAT_RG32F"),
    ("render.FILTER_LINEAR", "graphics.TEXTURE_FILTER_LINEAR"),
    ("render.FILTER_NEAREST", "graphics.TEXTURE_FILTER_NEAREST"),
    ("render.WRAP_CLAMP", "graphics.TEXTURE_WRAP_CLAMP_TO_EDGE"),
    ("render.WRAP_CLAMP_TO_BORDER", "graphics.TEXTURE_WRAP_CLAMP_TO_BORDER"),
    ("render.WRAP_CLAMP_TO_EDGE", "graphics.TEXTURE_WRAP_CLAMP_TO_EDGE"),
    ("render.WRAP_MIRRORED_REPEAT", "graphics.TEXTURE_WRAP_MIRRORED_REPEAT"),
    ("render.WRAP_REPEAT", "graphics.TEXTURE_WRAP_REPEAT"),
    ("render.BLEND_ZERO", "graphics.BLEND_FACTOR_ZERO"),
    ("render.BLEND_ONE", "graphics.BLEND_FACTOR_ONE"),
    ("render.BLEND_SRC_COLOR", "graphics.BLEND_FACTOR_SRC_COLOR"),
    ("render.BLEND_ONE_MINUS_SRC_COLOR", "graphics.BLEND_FACTOR_ONE_MINUS_SRC_COLOR"),
    ("render.BLEND_DST_COLOR", "graphics.BLEND_FACTOR_DST_COLOR"),
    ("render.BLEND_ONE_MINUS_DST_COLOR", "graphics.BLEND_FACTOR_ONE_MINUS_DST_COLOR"),
    ("render.BLEND_SRC_ALPHA", "graphics.BLEND_FACTOR_SRC_ALPHA"),
    ("render.BLEND_FACTOR_SRC_ALPHA", "graphics.BLEND_FACTOR_SRC_ALPHA"),
    ("render.BLEND_ONE_MINUS_SRC_ALPHA", "graphics.BLEND_FACTOR_ONE_MINUS_SRC_ALPHA"),
    ("render.BLEND_FACTOR_ONE_MINUS_SRC_ALPHA", "graphics.BLEND_FACTOR_ONE_MINUS_SRC_ALPHA"),
    ("render.BLEND_DST_ALPHA", "graphics.BLEND_FACTOR_DST_ALPHA"),
    ("render.BLEND_ONE_MINUS_DST_ALPHA", "graphics.BLEND_FACTOR_ONE_MINUS_DST_ALPHA"),
    ("render.BLEND_SRC_ALPHA_SATURATE", "graphics.BLEND_FACTOR_SRC_ALPHA_SATURATE"),
    ("render.BLEND_CONSTANT_COLOR", "graphics.BLEND_FACTOR_CONSTANT_COLOR"),
    ("render.BLEND_ONE_MINUS_CONSTANT_COLOR", "graphics.BLEND_FACTOR_ONE_MINUS_CONSTANT_COLOR"),
    ("render.BLEND_CONSTANT_ALPHA", "graphics.BLEND_FACTOR_CONSTANT_ALPHA"),
    ("render.BLEND_ONE_MINUS_CONSTANT_ALPHA", "graphics.BLEND_FACTOR_ONE_MINUS_CONSTANT_ALPHA"),
    ("render.BLEND_EQUATION_ADD", "graphics.BLEND_EQUATION_ADD"),
    ("render.BLEND_EQUATION_SUBTRACT", "graphics.BLEND_EQUATION_SUBTRACT"),
    ("render.BLEND_EQUATION_REVERSE_SUBTRACT", "graphics.BLEND_EQUATION_REVERSE_SUBTRACT"),
    ("render.BLEND_EQUATION_MIN", "graphics.BLEND_EQUATION_MIN"),
    ("render.BLEND_EQUATION_MAX", "graphics.BLEND_EQUATION_MAX"),
    ("render.COMPARE_FUNC_NEVER", "graphics.COMPARE_FUNC_NEVER"),
    ("render.COMPARE_FUNC_LESS", "graphics.COMPARE_FUNC_LESS"),
    ("render.COMPARE_FUNC_LEQUAL", "graphics.COMPARE_FUNC_LEQUAL"),
    ("render.COMPARE_FUNC_GREATER", "graphics.COMPARE_FUNC_GREATER"),
    ("render.COMPARE_FUNC_GEQUAL", "graphics.COMPARE_FUNC_GEQUAL"),
    ("render.COMPARE_FUNC_EQUAL", "graphics.COMPARE_FUNC_EQUAL"),
    ("render.COMPARE_FUNC_NOTEQUAL", "graphics.COMPARE_FUNC_NOTEQUAL"),
    ("render.COMPARE_FUNC_ALWAYS", "graphics.COMPARE_FUNC_ALWAYS"),
    ("render.STENCIL_OP_KEEP", "graphics.STENCIL_OP_KEEP"),
    ("render.STENCIL_OP_ZERO", "graphics.STENCIL_OP_ZERO"),
    ("render.STENCIL_OP_REPLACE", "graphics.STENCIL_OP_REPLACE"),
    ("render.STENCIL_OP_INCR", "graphics.STENCIL_OP_INCR"),
    ("render.STENCIL_OP_INCR_WRAP", "graphics.STENCIL_OP_INCR_WRAP"),
    ("render.STENCIL_OP_DECR", "graphics.STENCIL_OP_DECR"),
    ("render.STENCIL_OP_DECR_WRAP", "graphics.STENCIL_OP_DECR_WRAP"),
    ("render.STENCIL_OP_INVERT", "graphics.STENCIL_OP_INVERT"),
    ("render.FACE_FRONT", "graphics.FACE_TYPE_FRONT"),
    ("render.FACE_BACK", "graphics.FACE_TYPE_BACK"),
    ("render.FACE_FRONT_AND_BACK", "graphics.FACE_TYPE_FRONT_AND_BACK"),
    ("render.BUFFER_COLOR_BIT", "graphics.BUFFER_TYPE_COLOR0_BIT"),
    ("render.BUFFER_COLOR0_BIT", "graphics.BUFFER_TYPE_COLOR0_BIT"),
    ("render.BUFFER_COLOR1_BIT", "graphics.BUFFER_TYPE_COLOR1_BIT"),
    ("render.BUFFER_COLOR2_BIT", "graphics.BUFFER_TYPE_COLOR2_BIT"),
    ("render.BUFFER_COLOR3_BIT", "graphics.BUFFER_TYPE_COLOR3_BIT"),
    ("render.BUFFER_DEPTH_BIT", "graphics.BUFFER_TYPE_DEPTH_BIT"),
    ("render.BUFFER_STENCIL_BIT", "graphics.BUFFER_TYPE_STENCIL_BIT"),
    ("render.BUFFER_TYPE_COLOR_BIT", "graphics.BUFFER_TYPE_COLOR0_BIT"),
    ("resource.TEXTURE_TYPE_2D", "graphics.TEXTURE_TYPE_2D"),
    ("resource.TEXTURE_TYPE_CUBE_MAP", "graphics.TEXTURE_TYPE_CUBE_MAP"),
    ("resource.TEXTURE_TYPE_2D_ARRAY", "graphics.TEXTURE_TYPE_2D_ARRAY"),
    ("resource.TEXTURE_TYPE_IMAGE_2D", "graphics.TEXTURE_TYPE_IMAGE_2D"),
    ("resource.BUFFER_TYPE_COLOR0_BIT", "graphics.BUFFER_TYPE_COLOR0_BIT"),
    ("resource.BUFFER_TYPE_COLOR1_BIT", "graphics.BUFFER_TYPE_COLOR1_BIT"),
    ("resource.BUFFER_TYPE_COLOR2_BIT", "graphics.BUFFER_TYPE_COLOR2_BIT"),
    ("resource.BUFFER_TYPE_COLOR3_BIT", "graphics.BUFFER_TYPE_COLOR3_BIT"),
    ("resource.BUFFER_TYPE_DEPTH_BIT", "graphics.BUFFER_TYPE_DEPTH_BIT"),
    ("resource.BUFFER_TYPE_STENCIL_BIT", "graphics.BUFFER_TYPE_STENCIL_BIT"),
    ("resource.TEXTURE_USAGE_FLAG_SAMPLE", "graphics.TEXTURE_USAGE_FLAG_SAMPLE"),
    ("resource.TEXTURE_USAGE_FLAG_MEMORYLESS", "graphics.TEXTURE_USAGE_FLAG_MEMORYLESS"),
    ("resource.TEXTURE_USAGE_FLAG_STORAGE", "graphics.TEXTURE_USAGE_FLAG_STORAGE"),
    ("resource.TEXTURE_FORMAT_LUMINANCE", "graphics.TEXTURE_FORMAT_LUMINANCE"),
    ("resource.TEXTURE_FORMAT_RGB", "graphics.TEXTURE_FORMAT_RGB"),
    ("resource.TEXTURE_FORMAT_RGBA", "graphics.TEXTURE_FORMAT_RGBA"),
    ("resource.TEXTURE_FORMAT_DEPTH", "graphics.TEXTURE_FORMAT_DEPTH"),
    ("resource.TEXTURE_FORMAT_STENCIL", "graphics.TEXTURE_FORMAT_STENCIL"),
    ("resource.TEXTURE_FORMAT_RGB_PVRTC_2BPPV1", "graphics.TEXTURE_FORMAT_RGB_PVRTC_2BPPV1"),
    ("resource.TEXTURE_FORMAT_RGB_PVRTC_4BPPV1", "graphics.TEXTURE_FORMAT_RGB_PVRTC_4BPPV1"),
    ("resource.TEXTURE_FORMAT_RGBA_PVRTC_2BPPV1", "graphics.TEXTURE_FORMAT_RGBA_PVRTC_2BPPV1"),
    ("resource.TEXTURE_FORMAT_RGBA_PVRTC_4BPPV1", "graphics.TEXTURE_FORMAT_RGBA_PVRTC_4BPPV1"),
    ("resource.TEXTURE_FORMAT_RGB_ETC1", "graphics.TEXTURE_FORMAT_RGB_ETC1"),
    ("resource.TEXTURE_FORMAT_RGBA_ETC2", "graphics.TEXTURE_FORMAT_RGBA_ETC2"),
    ("resource.TEXTURE_FORMAT_RGBA_ASTC_4X4", "graphics.TEXTURE_FORMAT_RGBA_ASTC_4X4"),
    ("resource.TEXTURE_FORMAT_RGBA_ASTC_4x4", "graphics.TEXTURE_FORMAT_RGBA_ASTC_4X4"),
    ("resource.TEXTURE_FORMAT_RGB_BC1", "graphics.TEXTURE_FORMAT_RGB_BC1"),
    ("resource.TEXTURE_FORMAT_RGBA_BC3", "graphics.TEXTURE_FORMAT_RGBA_BC3"),
    ("resource.TEXTURE_FORMAT_R_BC4", "graphics.TEXTURE_FORMAT_R_BC4"),
    ("resource.TEXTURE_FORMAT_RG_BC5", "graphics.TEXTURE_FORMAT_RG_BC5"),
    ("resource.TEXTURE_FORMAT_RGBA_BC7", "graphics.TEXTURE_FORMAT_RGBA_BC7"),
    ("resource.TEXTURE_FORMAT_RGB16F", "graphics.TEXTURE_FORMAT_RGB16F"),
    ("resource.TEXTURE_FORMAT_RGB32F", "graphics.TEXTURE_FORMAT_RGB32F"),
    ("resource.TEXTURE_FORMAT_RGBA16F", "graphics.TEXTURE_FORMAT_RGBA16F"),
    ("resource.TEXTURE_FORMAT_RGBA32F", "graphics.TEXTURE_FORMAT_RGBA32F"),
    ("resource.TEXTURE_FORMAT_R16F", "graphics.TEXTURE_FORMAT_R16F"),
    ("resource.TEXTURE_FORMAT_RG16F", "graphics.TEXTURE_FORMAT_RG16F"),
    ("resource.TEXTURE_FORMAT_R32F", "graphics.TEXTURE_FORMAT_R32F"),
    ("resource.TEXTURE_FORMAT_RG32F", "graphics.TEXTURE_FORMAT_RG32F"),
    ("resource.COMPRESSION_TYPE_DEFAULT", "graphics.COMPRESSION_TYPE_DEFAULT"),
    ("resource.COMPRESSION_TYPE_BASIS_UASTC", "graphics.COMPRESSION_TYPE_BASIS_UASTC"),
)


REMOVED_MESSAGE_MIGRATIONS: tuple[tuple[str, str | None], ...] = (
    ('"set_constant" message id string', "go.set()"),
)
SET_CONSTANT_MESSAGE_API = REMOVED_MESSAGE_MIGRATIONS[0][0]

API_REPLACEMENTS = dict(REMOVED_API_MIGRATIONS + REMOVED_MESSAGE_MIGRATIONS)
REMOVED_DOTTED_APIS = tuple(api for api, _ in REMOVED_API_MIGRATIONS)
REMOVED_APIS = REMOVED_DOTTED_APIS + tuple(api for api, _ in REMOVED_MESSAGE_MIGRATIONS)
IDENTIFIER_CHARS = r"A-Za-z0-9_"
DOCS_BASE_URL = "https://defold.com/ref/alpha"
API_REF_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\b")
SET_CONSTANT_MESSAGE_RE = re.compile(
    r"(['\"])set_constant\1"
)
CUSTOM_DOC_LINKS: dict[str, tuple[tuple[str, str], ...]] = {
    "camera.acquire_focus": (
        ("Using the camera", "https://defold.com/manuals/camera/index.html#using-the-camera"),
    ),
    "camera.release_focus": (
        ("Using the camera", "https://defold.com/manuals/camera/index.html#using-the-camera"),
    ),
    "gui.get_text_metrics": (
        (
            "gui.get_font_resource",
            "https://defold.com/ref/gui-lua/index.html#gui.get_font_resource:font_name",
        ),
    ),
    "gui.get_text_metrics_from_node": (
        (
            "gui.get_font_resource",
            "https://defold.com/ref/gui-lua/index.html#gui.get_font_resource:font_name",
        ),
    ),
}
URL_RE = re.compile(
    r"(?:https?://|ssh://|git@|file://|github\.com/)[^\s)>\]]+|"
    r"(?<![\w.-])[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?(?![\w.-])"
)


@dataclass(frozen=True)
class Match:
    path: str
    line_number: int
    api: str


@dataclass
class RepoReport:
    source: str
    label: str
    matches: list[Match]
    error: str | None = None


class HelpFormatter(argparse.RawDescriptionHelpFormatter):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, max_help_position=28, width=100, **kwargs)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a local Defold project folder, clone a Git repository, clone "
            "repositories listed in a text file, or clone all repositories in a "
            "GitHub organization or user account, and report Lua uses of APIs removed by "
            "defold/defold#12441 and follow-up PRs."
        ),
        formatter_class=HelpFormatter,
        epilog="""examples:
  %(prog)s --folder /path/to/local/project
  %(prog)s --repo https://github.com/defold/tutorial-side-scroller
  %(prog)s --repo defold/tutorial-side-scroller
  %(prog)s --org defold
  %(prog)s --org AGulev
  %(prog)s --repos repos.txt
  %(prog)s --folder /path/to/local/project --report reports
  %(prog)s --list-apis

repo list files may contain plain URLs, owner/repo names, local paths, or Markdown links.
Git is only required when cloning repositories instead of scanning local folders.
Organization/account scans use the GitHub REST API. Set GITHUB_TOKEN for private organization
repositories, private repositories owned by the authenticated user, or higher rate limits.""",
    )

    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--folder",
        metavar="PATH",
        help="Local Defold project folder to scan.",
    )
    source_group.add_argument(
        "--repo",
        metavar="URL_OR_OWNER_REPO",
        help="Git repository URL or GitHub owner/repo name to clone and scan.",
    )
    source_group.add_argument(
        "--repos",
        metavar="PATH",
        help="Text file containing repository URLs/names or local paths to scan.",
    )
    source_group.add_argument(
        "--org",
        metavar="GITHUB_OWNER",
        help="GitHub organization or user account whose repositories should be cloned and scanned.",
    )
    parser.add_argument(
        "--extensions",
        default=",".join(DEFAULT_LUA_SUFFIXES),
        help=(
            "Comma-separated Lua file suffixes to scan "
            f"(default: {', '.join(DEFAULT_LUA_SUFFIXES)})."
        ),
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep cloned repositories in the temporary directory after the scan.",
    )
    parser.add_argument(
        "--skip-dir",
        action="append",
        default=list(DEFAULT_SKIP_DIR_PATTERNS),
        metavar="PATTERN",
        help=(
            "Directory name pattern to skip while scanning. Can be passed multiple "
            f"times (defaults: {', '.join(DEFAULT_SKIP_DIR_PATTERNS)})."
        ),
    )
    parser.add_argument(
        "--fail-on-match",
        action="store_true",
        help="Exit with status 1 when removed API usages are found.",
    )
    parser.add_argument(
        "--report",
        nargs="?",
        const="removed-lua-api-reports",
        metavar="DIR",
        help=(
            "Write one Markdown report per scanned repository/folder to DIR. "
            "If DIR is omitted, uses removed-lua-api-reports."
        ),
    )
    parser.add_argument(
        "--list-apis",
        action="store_true",
        help="Print the removed API names, suggested replacements, and docs links, then exit.",
    )
    return parser


def parse_args() -> argparse.Namespace:
    return build_arg_parser().parse_args()


def compile_patterns(apis: Iterable[str]) -> list[tuple[str, re.Pattern[str]]]:
    patterns = []
    for api in apis:
        module, name = api.split(".", 1)
        pattern = re.compile(
            rf"(?<![{IDENTIFIER_CHARS}.])"
            rf"{re.escape(module)}\s*\.\s*{re.escape(name)}"
            rf"(?![{IDENTIFIER_CHARS}])"
        )
        patterns.append((api, pattern))
    return patterns


def extract_repo_sources(target: str) -> list[str]:
    target_path = Path(target).expanduser()
    if target_path.is_file():
        sources: list[str] = []
        for raw_line in target_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            local_dir = source_to_local_dir(line)
            if local_dir is not None:
                sources.append(str(local_dir))
                continue
            match = URL_RE.search(line)
            if match:
                sources.append(match.group(0).rstrip(".,;"))
            else:
                sources.append(line)
        return sources
    return [target]


def github_api_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "defold-removed-lua-api-checker",
    }
    token = github_api_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_api_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def log_progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


class GitHubAPIRequestError(RuntimeError):
    def __init__(
        self,
        owner_kind: str,
        owner: str,
        status_code: int,
        reason: str,
        detail: str,
    ) -> None:
        super().__init__(
            f"GitHub API request for {owner_kind} `{owner}` failed: "
            f"HTTP {status_code} {reason}. {detail}"
        )
        self.status_code = status_code


def fetch_github_repo_sources(
    owner: str,
    owner_kind: str,
    url_for_page: Callable[[int], str],
) -> list[str]:
    sources: list[str] = []
    page = 1
    while True:
        log_progress(f"Fetching GitHub {owner_kind} `{owner}` repositories, page {page}...")
        url = url_for_page(page)
        request = Request(url, headers=github_api_headers())
        try:
            with urlopen(request, timeout=30) as response:
                repos = json.load(response)
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace").strip()
            raise GitHubAPIRequestError(
                owner_kind, owner, error.code, error.reason, detail
            ) from error
        except URLError as error:
            raise RuntimeError(
                f"GitHub API request for {owner_kind} `{owner}` failed: {error.reason}"
            ) from error

        if not isinstance(repos, list):
            raise RuntimeError(f"GitHub API returned an unexpected response for `{owner}`.")
        if not repos:
            break

        for repo in repos:
            if not isinstance(repo, dict):
                continue
            clone_url = repo.get("clone_url") or repo.get("html_url")
            if isinstance(clone_url, str):
                sources.append(clone_url)

        if len(repos) < 100:
            break
        page += 1

    log_progress(f"Found {len(sources)} GitHub repositories for {owner_kind} `{owner}`.")
    return sources


def fetch_authenticated_github_login() -> str | None:
    if github_api_token() is None:
        return None

    request = Request("https://api.github.com/user", headers=github_api_headers())
    try:
        with urlopen(request, timeout=30) as response:
            profile = json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace").strip()
        raise GitHubAPIRequestError(
            "authenticated user", "token", error.code, error.reason, detail
        ) from error
    except URLError as error:
        raise RuntimeError(
            f"GitHub API request for authenticated user failed: {error.reason}"
        ) from error

    if isinstance(profile, dict):
        login = profile.get("login")
        if isinstance(login, str):
            return login
    return None


def fetch_user_repo_sources(user: str) -> list[str]:
    authenticated_login = fetch_authenticated_github_login()
    if authenticated_login is not None and authenticated_login.lower() == user.lower():
        log_progress(
            f"Authenticated as `{authenticated_login}`; fetching public and private owned repositories."
        )
        return fetch_github_repo_sources(
            user,
            "authenticated user",
            lambda page: (
                "https://api.github.com/user/repos"
                f"?affiliation=owner&visibility=all&per_page=100&page={page}"
            ),
        )

    return fetch_github_repo_sources(
        user,
        "user",
        lambda page: (
            f"https://api.github.com/users/{quote(user, safe='')}/repos"
            f"?type=all&per_page=100&page={page}"
        ),
    )


def fetch_org_repo_sources(org: str) -> list[str]:
    owner = org.strip().removeprefix("@")
    try:
        return fetch_github_repo_sources(
            owner,
            "organization",
            lambda page: (
                f"https://api.github.com/orgs/{quote(owner, safe='')}/repos"
                f"?type=all&per_page=100&page={page}"
            ),
        )
    except GitHubAPIRequestError as error:
        if error.status_code != 404:
            raise
        log_progress(f"GitHub organization `{owner}` was not found; trying user account `{owner}`...")
    return fetch_user_repo_sources(owner)


def resolve_sources(args: argparse.Namespace) -> list[str]:
    if args.folder:
        local_dir = source_to_local_dir(args.folder)
        if local_dir is None:
            raise ValueError(f"Local folder does not exist: {args.folder}")
        return [str(local_dir)]
    if args.repo:
        return [args.repo]
    if args.repos:
        repos_file = Path(args.repos).expanduser()
        if not repos_file.is_file():
            raise ValueError(f"Repository list file does not exist: {args.repos}")
        return extract_repo_sources(str(repos_file))
    if args.org:
        return fetch_org_repo_sources(args.org)
    return []


def normalize_repo_source(source: str) -> str:
    source = source.strip()
    if source.startswith("git@") or source.startswith("ssh://") or source.startswith("file://"):
        return source
    if source.startswith("github.com/"):
        source = "https://" + source

    parsed = urlparse(source)
    if parsed.netloc.lower() == "github.com":
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2:
            repo = parts[1]
            if repo.endswith(".git"):
                repo = repo[:-4]
            return f"https://github.com/{parts[0]}/{repo}.git"

    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?", source):
        owner, repo = source.split("/", 1)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return f"https://github.com/{owner}/{repo}.git"

    return source


def source_to_local_dir(source: str) -> Path | None:
    local_path = Path(source).expanduser()
    if local_path.is_dir():
        return local_path

    parsed = urlparse(source)
    if parsed.scheme == "file":
        file_path = Path(unquote(parsed.path)).expanduser()
        if file_path.is_dir():
            return file_path

    return None


def repo_label(source: str) -> str:
    parsed = urlparse(source)
    if parsed.netloc.lower() == "github.com":
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1].removesuffix('.git')}"
    if source.startswith("git@github.com:"):
        repo = source.split(":", 1)[1].removesuffix(".git")
        return repo
    return source.rstrip("/").removesuffix(".git").split("/")[-1]


def safe_dir_name(label: str, index: int) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("._")
    return f"{index:03d}_{safe or 'repo'}"


def clone_repo(source: str, destination: Path) -> None:
    if shutil.which("git") is None:
        raise MissingDependencyError("git")
    subprocess.run(
        ["git", "clone", "--quiet", "--depth", "1", normalize_repo_source(source), str(destination)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class MissingDependencyError(Exception):
    def __init__(self, command: str) -> None:
        super().__init__(command)
        self.command = command


def install_hint(command: str) -> str:
    if command == "git":
        if sys.platform == "darwin":
            return (
                "Install Git with Xcode Command Line Tools (`xcode-select --install`) "
                "or Homebrew (`brew install git`)."
            )
        if sys.platform.startswith("linux"):
            return "Install Git with your package manager, for example `sudo apt install git`."
        return "Install Git from https://git-scm.com/downloads and make sure it is on PATH."
    return f"Install `{command}` and make sure it is on PATH."


def needs_git(source: str) -> bool:
    return source_to_local_dir(source) is None


def find_missing_dependencies(sources: Iterable[str]) -> list[str]:
    missing = []
    if any(needs_git(source) for source in sources) and shutil.which("git") is None:
        missing.append("git")
    return missing


def sanitize_lua(text: str) -> str:
    """Replace Lua strings and comments with spaces while preserving line numbers."""
    out: list[str] = []
    i = 0
    length = len(text)

    while i < length:
        char = text[i]
        next_char = text[i + 1] if i + 1 < length else ""

        if char == "-" and next_char == "-":
            long_end = long_bracket_end(text, i + 2)
            if long_end is not None:
                replacement, i = blank_preserving_newlines(text, i, long_end)
                out.append(replacement)
                continue
            line_end = text.find("\n", i)
            if line_end == -1:
                out.append(" " * (length - i))
                break
            out.append(" " * (line_end - i))
            out.append("\n")
            i = line_end + 1
            continue

        if char in ("'", '"'):
            replacement, i = blank_quoted_string(text, i, char)
            out.append(replacement)
            continue

        if char == "[":
            long_end = long_bracket_end(text, i)
            if long_end is not None:
                replacement, i = blank_preserving_newlines(text, i, long_end)
                out.append(replacement)
                continue

        out.append(char)
        i += 1

    return "".join(out)


def sanitize_lua_comments(text: str) -> str:
    """Replace Lua comments and long strings while preserving short string literals."""
    out: list[str] = []
    i = 0
    length = len(text)

    while i < length:
        char = text[i]
        next_char = text[i + 1] if i + 1 < length else ""

        if char == "-" and next_char == "-":
            long_end = long_bracket_end(text, i + 2)
            if long_end is not None:
                replacement, i = blank_preserving_newlines(text, i, long_end)
                out.append(replacement)
                continue
            line_end = text.find("\n", i)
            if line_end == -1:
                out.append(" " * (length - i))
                break
            out.append(" " * (line_end - i))
            out.append("\n")
            i = line_end + 1
            continue

        if char in ("'", '"'):
            start = i
            i += 1
            while i < length:
                current = text[i]
                i += 1
                if current == "\\" and i < length:
                    i += 1
                    continue
                if current == char:
                    break
            out.append(text[start:i])
            continue

        if char == "[":
            long_end = long_bracket_end(text, i)
            if long_end is not None:
                replacement, i = blank_preserving_newlines(text, i, long_end)
                out.append(replacement)
                continue

        out.append(char)
        i += 1

    return "".join(out)


def long_bracket_end(text: str, start: int) -> int | None:
    match = re.match(r"\[(=*)\[", text[start:])
    if not match:
        return None
    equals = match.group(1)
    content_start = start + len(match.group(0))
    closing = "]" + equals + "]"
    end = text.find(closing, content_start)
    if end == -1:
        return len(text)
    return end + len(closing)


def blank_preserving_newlines(text: str, start: int, end: int) -> tuple[str, int]:
    return ("".join("\n" if char == "\n" else " " for char in text[start:end]), end)


def blank_quoted_string(text: str, start: int, quote: str) -> tuple[str, int]:
    out = [" "]
    i = start + 1
    while i < len(text):
        char = text[i]
        if char == "\n":
            out.append("\n")
            i += 1
            continue
        out.append(" ")
        if char == "\\":
            i += 1
            if i < len(text):
                out.append("\n" if text[i] == "\n" else " ")
            i += 1
            continue
        i += 1
        if char == quote:
            break
    return ("".join(out), i)


def scan_file(path: Path, root: Path, patterns: list[tuple[str, re.Pattern[str]]]) -> list[Match]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")

    sanitized = sanitize_lua(text)
    line_starts = [0]
    for index, char in enumerate(sanitized):
        if char == "\n":
            line_starts.append(index + 1)

    matches: set[Match] = set()
    rel_path = path.relative_to(root).as_posix()
    for api, pattern in patterns:
        for match in pattern.finditer(sanitized):
            line_number = bisect.bisect_right(line_starts, match.start())
            matches.add(Match(rel_path, line_number, api))
    matches.update(scan_removed_messages(text, line_starts, rel_path))
    return sorted(matches, key=lambda item: (item.path, item.line_number, item.api))


def scan_removed_messages(
    text: str,
    line_starts: list[int],
    rel_path: str,
) -> set[Match]:
    matches: set[Match] = set()
    comment_sanitized = sanitize_lua_comments(text)
    for match in SET_CONSTANT_MESSAGE_RE.finditer(comment_sanitized):
        line_number = bisect.bisect_right(line_starts, match.start())
        matches.add(Match(rel_path, line_number, SET_CONSTANT_MESSAGE_API))
    return matches


def git_scan_files(root: Path, suffixes: tuple[str, ...]) -> list[Path] | None:
    if shutil.which("git") is None:
        return None
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        return None
    files = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        rel_path = Path(os.fsdecode(raw_path))
        if rel_path.name.endswith(suffixes):
            files.append(root / rel_path)
    return files


def walk_scan_files(
    root: Path,
    suffixes: tuple[str, ...],
    skip_dir_patterns: tuple[str, ...],
) -> Iterable[Path]:
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if not any(fnmatch.fnmatch(dirname, pattern) for pattern in skip_dir_patterns)
        ]
        current_path = Path(current_root)
        for filename in filenames:
            if filename.endswith(suffixes):
                yield current_path / filename


def scan_repo(
    root: Path,
    suffixes: tuple[str, ...],
    patterns: list[tuple[str, re.Pattern[str]]],
    skip_dir_patterns: tuple[str, ...],
) -> list[Match]:
    matches: list[Match] = []
    files = git_scan_files(root, suffixes)
    if files is None:
        files = list(walk_scan_files(root, suffixes, skip_dir_patterns))
    for path in files:
        if path.is_file():
            matches.extend(scan_file(path, root, patterns))
    return sorted(matches, key=lambda item: (item.path, item.line_number, item.api))


def scan_sources(
    sources: list[str],
    suffixes: tuple[str, ...],
    patterns: list[tuple[str, re.Pattern[str]]],
    skip_dir_patterns: tuple[str, ...],
    keep_temp: bool,
) -> list[RepoReport]:
    temp_dir = Path(tempfile.mkdtemp(prefix="defold-removed-api-scan-"))
    reports: list[RepoReport] = []
    total = len(sources)
    log_progress(f"Using temporary clone directory: {temp_dir}")
    try:
        for index, source in enumerate(sources, start=1):
            label = repo_label(source)
            local_path = source_to_local_dir(source)
            prefix = f"[{index}/{total}] {label}"
            try:
                if local_path is not None:
                    root = local_path
                    log_progress(f"{prefix}: using local folder {root}")
                else:
                    root = temp_dir / safe_dir_name(label, index)
                    log_progress(f"{prefix}: cloning {normalize_repo_source(source)}...")
                    clone_repo(source, root)
                    log_progress(f"{prefix}: clone complete.")
                log_progress(f"{prefix}: analyzing Lua files...")
                matches = scan_repo(root, suffixes, patterns, skip_dir_patterns)
                log_progress(
                    f"{prefix}: analysis complete, found {len(matches)} removed API usage"
                    f"{'' if len(matches) == 1 else 's'}."
                )
                reports.append(RepoReport(source, label, matches))
            except subprocess.CalledProcessError as error:
                stderr = error.stderr.strip() if error.stderr else str(error)
                log_progress(f"{prefix}: clone failed.")
                reports.append(RepoReport(source, label, [], f"clone failed: {stderr}"))
            except MissingDependencyError as error:
                log_progress(f"{prefix}: missing dependency `{error.command}`.")
                reports.append(
                    RepoReport(
                        source,
                        label,
                        [],
                        f"missing dependency: `{error.command}`. {install_hint(error.command)}",
                    )
                )
            except OSError as error:
                log_progress(f"{prefix}: failed with error: {error}")
                reports.append(RepoReport(source, label, [], str(error)))
    finally:
        if keep_temp:
            log_progress(f"Temporary repositories kept in {temp_dir}")
        else:
            log_progress(f"Removing temporary clone directory: {temp_dir}")
            shutil.rmtree(temp_dir)
    return reports


def replacement_hint(api: str) -> str:
    replacement = API_REPLACEMENTS[api]
    if replacement is None:
        return "no direct replacement"
    return f"use {replacement} instead"


def api_docs_url(api: str) -> str:
    namespace = api.split(".", 1)[0]
    return f"{DOCS_BASE_URL}/{namespace}/#{api}"


def api_module_docs_url(api: str) -> str:
    namespace = api.split(".", 1)[0]
    return f"{DOCS_BASE_URL}/{namespace}/"


def replacement_doc_apis(api: str) -> tuple[str, ...]:
    replacement = API_REPLACEMENTS[api]
    if replacement is None:
        return ()

    refs = []
    seen = set()
    for match in API_REF_RE.finditer(replacement):
        ref = match.group(0)
        if ref not in seen:
            refs.append(ref)
            seen.add(ref)
    return tuple(refs)


def docs_urls(api: str) -> str:
    custom_links = CUSTOM_DOC_LINKS.get(api)
    if custom_links is not None:
        return ", ".join(url for _, url in custom_links)

    refs = replacement_doc_apis(api)
    if refs:
        return ", ".join(api_docs_url(ref) for ref in refs)
    return api_module_docs_url(api)


def docs_hint(api: str) -> str:
    return f"docs: {docs_urls(api)}"


def list_api_entry(api: str) -> str:
    replacement = API_REPLACEMENTS[api]
    replacement_text = "no direct replacement" if replacement is None else replacement
    return f"{api} -> {replacement_text} : {docs_urls(api)}"


def markdown_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def markdown_code(text: str) -> str:
    return "`" + markdown_text(text).replace("`", "\\`") + "`"


def markdown_doc_links(api: str) -> str:
    custom_links = CUSTOM_DOC_LINKS.get(api)
    if custom_links is not None:
        return ", ".join(f"[{markdown_text(label)}]({url})" for label, url in custom_links)

    refs = replacement_doc_apis(api)
    if refs:
        return ", ".join(f"[{markdown_code(ref)}]({api_docs_url(ref)})" for ref in refs)

    namespace = api.split(".", 1)[0]
    return f"[{markdown_text(namespace)} API]({api_module_docs_url(api)})"


def report_file_name(label: str, used_names: set[str]) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("._") or "report"
    name = f"{stem}.md"
    suffix = 2
    while name in used_names:
        name = f"{stem}-{suffix}.md"
        suffix += 1
    used_names.add(name)
    return name


def markdown_report(report: RepoReport) -> str:
    lines = [
        f"# Removed Lua API Report: {markdown_text(report.label)}",
        "",
        f"Source: {markdown_code(report.source)}",
        "",
    ]

    if report.error:
        lines.extend(("## Error", "", markdown_text(report.error), ""))
        return "\n".join(lines)

    if not report.matches:
        lines.extend(("No removed APIs found.", ""))
        return "\n".join(lines)

    lines.extend(
        (
            f"Found {len(report.matches)} removed API usage"
            f"{'' if len(report.matches) == 1 else 's'}.",
            "",
            "| File | Line | Removed API | Suggested replacement | API docs |",
            "| --- | ---: | --- | --- | --- |",
        )
    )
    for match in report.matches:
        replacement = API_REPLACEMENTS[match.api]
        suggestion = "No direct replacement" if replacement is None else f"Use {markdown_code(replacement)}"
        lines.append(
            f"| {markdown_code(match.path)} | {match.line_number} | "
            f"{markdown_code(match.api)} | {suggestion} | {markdown_doc_links(match.api)} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_markdown_reports(reports: list[RepoReport], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    used_names: set[str] = set()
    paths = []
    log_progress(f"Saving Markdown reports to {output_dir.resolve()}...")
    for report in reports:
        path = output_dir / report_file_name(report.label, used_names)
        if not report.error and not report.matches:
            if path.exists():
                path.unlink()
                log_progress(f"Removed report with no removed APIs: {path.resolve()}")
            else:
                log_progress(f"Skipped report with no removed APIs: {path.resolve()}")
            continue
        path.write_text(markdown_report(report), encoding="utf-8")
        log_progress(f"Saved report: {path.resolve()}")
        paths.append(path)
    return paths


def print_reports(reports: list[RepoReport]) -> None:
    multiple = len(reports) > 1
    for repo_index, report in enumerate(reports):
        if multiple:
            if repo_index:
                print()
            print(report.label)
        if report.error:
            print(f"ERROR: {report.error}")
            continue
        if not report.matches:
            print("No removed APIs found.")
            continue
        for index, match in enumerate(report.matches, start=1):
            print(
                f"{index}. {match.path}:{match.line_number} - "
                f"removed API {match.api} used; {replacement_hint(match.api)}; {docs_hint(match.api)}"
            )


def main() -> int:
    parser = build_arg_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        return 2
    args = parser.parse_args()

    if args.list_apis:
        for api in REMOVED_APIS:
            print(list_api_entry(api))
        return 0

    try:
        sources = resolve_sources(args)
    except (RuntimeError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2

    if not sources:
        print("One source option is required: --folder, --repo, --repos, or --org.", file=sys.stderr)
        return 2
    log_progress(f"Resolved {len(sources)} source{'' if len(sources) == 1 else 's'} to scan.")

    suffixes = tuple(suffix.strip() for suffix in args.extensions.split(",") if suffix.strip())
    if not suffixes:
        print("No file extensions configured.", file=sys.stderr)
        return 2

    missing_dependencies = find_missing_dependencies(sources)
    if missing_dependencies:
        for command in missing_dependencies:
            print(f"Missing dependency: `{command}`. {install_hint(command)}", file=sys.stderr)
        return 2

    patterns = compile_patterns(REMOVED_DOTTED_APIS)
    reports = scan_sources(sources, suffixes, patterns, tuple(args.skip_dir), args.keep_temp)
    print_reports(reports)

    if args.report:
        output_dir = Path(args.report).expanduser()
        try:
            report_paths = write_markdown_reports(reports, output_dir)
        except OSError as error:
            print(f"Could not write Markdown reports to {output_dir}: {error}", file=sys.stderr)
            return 2
        if report_paths:
            log_progress(f"Markdown reports written to {output_dir.resolve()}")
        else:
            log_progress(f"No Markdown reports written to {output_dir.resolve()}")

    if any(report.error for report in reports):
        return 2
    if args.fail_on_match and any(report.matches for report in reports):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

