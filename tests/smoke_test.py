"""
Integration smoke test — exercises cogs/amp.py helpers against a live AMP instance.

Requirements:
    - A populated .env file (same one used to run the bot)
    - A running AMP installation reachable at AMP_URL
    - At least one AMP instance registered

Usage:
    source .venv/bin/activate
    python tests/smoke_test.py

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

import asyncio
import os
import sys

# Add the project root to sys.path so cogs can be imported when running
# this script directly (e.g. python tests/smoke_test.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import aiohttp
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------ #
#  Configure the instance name to use for targeted checks             #
# ------------------------------------------------------------------ #
TEST_INSTANCE_NAME = "VRising01"
# ------------------------------------------------------------------ #

# Validate required env vars before importing the cog
_required = ["AMP_URL", "AMP_USER", "AMP_PASS", "NETWORKADMIN_ROLE_ID"]
_missing = [k for k in _required if not os.getenv(k)]
if _missing:
    print(f"[SKIP] Missing env vars: {', '.join(_missing)}")
    print("       Populate your .env file and try again.")
    sys.exit(1)

from ampapi import AMPInstance, AMPMinecraftInstance
from ampapi.modules import ActionResultError, Players
from cogs.amp import _find_instance, _get_all_instances

_PASS = "\033[32mPASS\033[0m"
_FAIL = "\033[31mFAIL\033[0m"
_results: list[tuple[str, bool, str]] = []


def _record(name: str, passed: bool, detail: str = ""):
    _results.append((name, passed, detail))
    status = _PASS if passed else _FAIL
    suffix = f" — {detail}" if detail else ""
    print(f"  [{status}] {name}{suffix}")


async def run_checks():
    print("\n=== AMP Smoke Test ===\n")
    session = aiohttp.ClientSession()

    try:
        # ---------------------------------------------------------- #
        # Check 1: _get_all_instances returns a non-empty list        #
        # ---------------------------------------------------------- #
        print("1. Fetching all instances...")
        try:
            instances = await _get_all_instances(session)
            if instances:
                names = [getattr(i, "friendly_name", repr(i)) for i in instances]
                _record(
                    "_get_all_instances returns instances",
                    True,
                    f"{len(instances)} found: {', '.join(names)}",
                )
            else:
                _record("_get_all_instances returns instances", False, "empty list")
        except Exception as e:
            _record("_get_all_instances returns instances", False, str(e))

        # ---------------------------------------------------------- #
        # Check 2: _find_instance finds TEST_INSTANCE_NAME            #
        # ---------------------------------------------------------- #
        print(f"2. Finding instance '{TEST_INSTANCE_NAME}'...")
        instance = None
        try:
            instance = await _find_instance(TEST_INSTANCE_NAME, session)
            if instance is not None:
                _record(
                    f"_find_instance finds '{TEST_INSTANCE_NAME}'",
                    True,
                    f"type={type(instance).__name__}, state={instance.app_state}",
                )
            else:
                _record(
                    f"_find_instance finds '{TEST_INSTANCE_NAME}'",
                    False,
                    "returned None — check TEST_INSTANCE_NAME",
                )
        except Exception as e:
            _record(f"_find_instance finds '{TEST_INSTANCE_NAME}'", False, str(e))

        # ---------------------------------------------------------- #
        # Check 3: _find_instance returns None for unknown name       #
        # ---------------------------------------------------------- #
        print("3. Confirming unknown instance returns None...")
        try:
            result = await _find_instance("__nonexistent_xyz_smoke__", session)
            _record(
                "_find_instance returns None for unknown name",
                result is None,
                "" if result is None else f"unexpectedly returned {result}",
            )
        except Exception as e:
            _record("_find_instance returns None for unknown name", False, str(e))

        # ---------------------------------------------------------- #
        # Check 4: get_status returns valid metrics (if instance found)
        # ---------------------------------------------------------- #
        print("4. Fetching instance status/metrics...")
        if instance is not None:
            try:
                status = await instance.get_status(format_data=True)
                if isinstance(status, ActionResultError):
                    _record("get_status returns valid Status", False, str(status))
                else:
                    has_metrics = status.metrics is not None
                    _record(
                        "get_status returns valid Status",
                        True,
                        f"metrics={'present' if has_metrics else 'none'}",
                    )
            except ConnectionError:
                _record(
                    "get_status returns valid Status",
                    False,
                    "ConnectionError — instance may be offline",
                )
            except Exception as e:
                _record("get_status returns valid Status", False, str(e))
        else:
            _record(
                "get_status returns valid Status",
                False,
                "skipped — instance not found in check 2",
            )

        # ---------------------------------------------------------- #
        # Check 5: get_user_list returns a Players object             #
        # ---------------------------------------------------------- #
        print("5. Fetching player list...")
        if instance is not None:
            try:
                players = await instance.get_user_list(format_data=True)
                if isinstance(players, ActionResultError):
                    _record("get_user_list returns Players", False, str(players))
                elif isinstance(players, Players):
                    _record(
                        "get_user_list returns Players",
                        True,
                        f"{len(players.sorted)} player(s) online",
                    )
                else:
                    _record(
                        "get_user_list returns Players",
                        False,
                        f"unexpected type: {type(players).__name__}",
                    )
            except ConnectionError:
                _record(
                    "get_user_list returns Players",
                    False,
                    "ConnectionError — instance may be offline",
                )
            except Exception as e:
                _record("get_user_list returns Players", False, str(e))
        else:
            _record(
                "get_user_list returns Players",
                False,
                "skipped — instance not found in check 2",
            )

    finally:
        await session.close()

    # ---------------------------------------------------------- #
    # Summary                                                      #
    # ---------------------------------------------------------- #
    print(
        f"\n=== Results: {sum(p for _, p, _ in _results)}/{len(_results)} passed ===\n"
    )
    failed = [(n, d) for n, p, d in _results if not p]
    if failed:
        print("Failed checks:")
        for name, detail in failed:
            print(f"  - {name}" + (f": {detail}" if detail else ""))
        print()
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(run_checks())
