"""spark_session — the one local SparkSession builder, Windows and WSL/Linux.

    from audio_features.spark_session import build_spark
    spark = build_spark("dev")

One home for the Spark settings. dbt-spark's `session` method builds its OWN session
(dbt/adapters/spark/session.py: `SparkSession.builder.enableHiveSupport()`, then `.config(k, v)`
for every entry of the target's `server_side_parameters`, then `getOrCreate()`), so the settings
dbt needs — the warehouse dir under data/<environment>/, the Derby metastore URL under
metastore_db/, the loopback bind, the shuffle partitions — live in profiles.yml per target and
are read from there by build_spark(), never duplicated here. The builder adds only what YAML
cannot express: the environment scrub, the worker-interpreter override, `local[*]`, Hive
support, the Windows-only worker tax, the Linux-only scratch dir, and the log level. Because
both sides call `getOrCreate()`, a session this module built in a process is the one dbt reuses.

profiles.yml is read as plain YAML from the repo root — no Jinja, so every value under
`server_side_parameters` must be a literal. Until the file exists (the dbt project lands in the
same slice) the parameters fall back to an empty mapping and Spark's defaults apply; a target
missing from an existing file is a KeyError naming the known targets.

Hosts (/spark-env). Windows has no winutils.exe / hadoop.dll, so Spark there starts, parses and
computes (UDFs included) but every local-file WRITE and every Hive `create database` fails with
"HADOOP_HOME and hadoop.home.dir are unset": Windows is the debug, parse and compile host; WSL
is the build host (scripts/spark_wsl.ps1 -Run "dbt build --target dev"). Pin parity: pyspark
3.5.6 on CPython 3.11 on both.

Why the scrub and the override (both from vercilloanalytics' builder, journals #5, #42, #43):
the pyspark wheel bundles a complete Spark, so SPARK_HOME / HADOOP_HOME are only ever overrides,
and a dead one (the variable outlives the directory, or WSL inherits a Windows path) fails the
gateway launch with a pathless FileNotFoundError; and PYSPARK_PYTHON must be OVERRIDDEN to this
interpreter, because a machine-global value or the system python3 (3.14 in WSL) would answer for
the workers and every UDF would die on a worker-socket or version-mismatch error.
"""
from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path

import yaml

from audio_features.layers import ENVIRONMENTS, REPO_ROOT

PROFILES_PATH = REPO_ROOT / "profiles.yml"
PROFILE_NAME = "audio_features"
LINUX_SCRATCH_DIR = "/tmp"  # shuffle spill belongs on ext4, never on /mnt/c (playbook principle 5)

_IS_WINDOWS = os.name == "nt"


def _scrub_foreign_spark_home() -> list[str]:
    """Drop SPARK_HOME/HADOOP_HOME that can't work here; return what was dropped.

    Two ways an override goes bad, both silent until the gateway won't launch: the directory was
    deleted but the variable outlived it; or WSL inherits the Windows environment and a Linux
    session sees a `C:\\...` path (or its `/mnt/c/...` translation) holding `.cmd` launchers it
    cannot execute. In both cases pyspark's own bundled distribution is the right answer.
    """
    dropped = []
    for var in ("SPARK_HOME", "HADOOP_HOME"):
        val = os.environ.get(var)
        if not val:
            continue
        foreign = not _IS_WINDOWS and (":\\" in val or val.startswith("/mnt/"))
        if foreign or not Path(val).is_dir():
            os.environ.pop(var)
            dropped.append(f"{var}={val}")
    return dropped


def profile_spark_config(environment: str, profiles_path: Path = PROFILES_PATH) -> dict[str, str]:
    """The target's `server_side_parameters` from profiles.yml, as the `.config()` pairs dbt applies.

    Missing file -> {} (the dbt project may not exist yet). Missing profile or target -> KeyError
    naming what the file does define. Values are stringified, as Spark would receive them.
    """
    if environment not in ENVIRONMENTS:
        raise ValueError(f"unknown environment {environment!r}; expected one of {', '.join(ENVIRONMENTS)}")
    if not profiles_path.exists():
        return {}
    profiles = yaml.safe_load(profiles_path.read_text(encoding="utf-8")) or {}
    if PROFILE_NAME not in profiles:
        raise KeyError(f"{profiles_path.name} has no profile {PROFILE_NAME!r}; found {sorted(profiles)}")
    outputs = profiles[PROFILE_NAME].get("outputs") or {}
    if environment not in outputs:
        raise KeyError(f"{profiles_path.name} has no target {environment!r}; known targets: {sorted(outputs)}")
    params = outputs[environment].get("server_side_parameters") or {}
    return {str(k): str(v) for k, v in params.items()}


def build_spark(
    environment: str = "dev",
    app_name: str = "audio_features",
    overrides: Mapping[str, str] | None = None,
    ui: bool = False,
    verbose: bool = False,
):
    """Return the configured local SparkSession for one environment.

    overrides are extra `.config()` pairs applied LAST, after the profile's and after the host
    defaults below (a test points the warehouse and the metastore at tmp_path this way; a caller
    can move the Linux scratch dir). ui=True serves the Spark UI at http://localhost:4040; under
    WSL2 localhost forwards, so it opens in the Windows browser. verbose=True prints which stale
    overrides were dropped, if any.
    """
    config = profile_spark_config(environment)
    if _IS_WINDOWS:
        # Windows-only tax: a fresh Python process per task. Linux keeps the default (reuse on);
        # verified on both that UDFs pass either way once the profile's loopback bind is in place.
        config.setdefault("spark.python.worker.reuse", "false")
    else:
        config.setdefault("spark.local.dir", LINUX_SCRATCH_DIR)
    config.update(overrides or {})

    dropped = _scrub_foreign_spark_home()
    if dropped and verbose:
        print(f"build_spark: ignoring unusable {', '.join(dropped)} -> using pyspark's bundled Spark")

    # OVERRIDE, never setdefault: the workers must be THIS interpreter (see the module docstring).
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    from pyspark.sql import SparkSession

    builder = (
        SparkSession.builder.appName(f"{app_name}-{environment}")
        .master("local[*]")
        .enableHiveSupport()
        .config("spark.ui.enabled", "true" if ui else "false")
    )
    for key, value in config.items():
        builder = builder.config(key, value)

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark
