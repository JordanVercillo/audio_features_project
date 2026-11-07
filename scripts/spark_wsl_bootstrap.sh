#!/usr/bin/env bash
# Linux half of scripts/spark_wsl.ps1 — the WSL Spark toolchain for audio_features.
#
# WSL is the BUILD host: Windows Spark has no winutils.exe / hadoop.dll, so it parses and
# computes but cannot write Parquet or create a Hive database; every `dbt build` runs here.
#
# NOT a package manager. `ensure` installs uv if missing, fetches CPython 3.11 through uv and
# runs `uv sync --frozen` into a venv OUTSIDE the repo. Everything after day one is plain
# `uv add` / `uv lock` on Windows, then `ensure` again here. It writes NOTHING to ~/.profile or
# ~/.bashrc: those files export UV_PROJECT_ENVIRONMENT for another repo (vercilloanalytics), and
# this script overrides that variable for its own process only, so both repos keep working.
#
# Runnable on its own from inside WSL:
#     SPARK_WSL_REPO=/mnt/c/Users/jverc/audio_features_project \
#       bash /mnt/c/Users/jverc/audio_features_project/scripts/spark_wsl_bootstrap.sh check
set -uo pipefail

REPO="${SPARK_WSL_REPO:-}"          # linux path to the repo, passed by the .ps1
UV="$HOME/.local/bin/uv"
VENV="$HOME/.venvs/audio-features"  # OUTSIDE the repo — see the note in cmd_ensure
PY_MINOR="3.11"                     # pin parity with Windows (pyproject: >=3.11,<3.12)

# The load-bearing line, scoped to THIS process (never written to an rc file): without it, `uv`
# run inside a /mnt/c checkout targets ./.venv — the WINDOWS venv — sees a foreign platform and
# rebuilds it as Linux, breaking every Windows `uv run` afterwards (/spark-env journal #43).
INHERITED_UV_ENV="${UV_PROJECT_ENVIRONMENT:-}"
export UV_PROJECT_ENVIRONMENT="$VENV"

ok()   { printf '  ok    %s\n' "$*"; }
warn() { printf '  WARN  %s\n' "$*"; }
bad()  { printf '  FAIL  %s\n' "$*"; }

# Detector for a failure that actually happened in vercilloanalytics: the repo's .venv rebuilt
# for Linux. A Windows venv's pyvenv.cfg says `home = C:\...`; a Linux one says `home = /...`.
windows_venv_damaged() {
  [ -f "$REPO/.venv/pyvenv.cfg" ] && grep -qE '^home = /' "$REPO/.venv/pyvenv.cfg"
}

# ---------------------------------------------------------------- check ----
cmd_check() {
  local rc=0
  echo "WSL Spark toolchain (audio_features)"
  echo

  if [ "$(id -u)" -eq 0 ]; then
    bad "running as root (HOME=$HOME) — the toolchain belongs to the default user, not root"
    rc=1
  else
    ok "user  $(id -un)  HOME=$HOME"
  fi

  if command -v java >/dev/null 2>&1; then
    ok "java  $(java -version 2>&1 | head -1)"
  else
    bad "no java — sudo apt update && sudo apt install -y openjdk-17-jre-headless"
    rc=1
  fi

  if [ -x "$UV" ]; then
    ok "uv    $("$UV" --version)"
  else
    bad "uv not installed — run this script with 'ensure'"
    rc=1
  fi

  if [ -n "$REPO" ] && [ -d "$REPO" ]; then
    ok "repo  $REPO"
  else
    bad "repo not reachable at '${REPO:-<unset>}'"
    rc=1
  fi

  if [ -n "$INHERITED_UV_ENV" ] && [ "$INHERITED_UV_ENV" != "$VENV" ]; then
    ok "UV_PROJECT_ENVIRONMENT inherited as $INHERITED_UV_ENV (another repo's); overridden here to $VENV"
  fi

  if [ -x "$VENV/bin/python" ]; then
    ok "venv  $VENV ($("$VENV/bin/python" -V 2>&1))"
    local pv
    pv=$("$VENV/bin/python" -c 'import pyspark;print(pyspark.__version__)' 2>/dev/null)
    if [ -n "$pv" ]; then ok "pyspark $pv"; else bad "pyspark missing from the venv — run 'ensure'"; rc=1; fi
  else
    bad "no venv at $VENV — run this script with 'ensure'"
    rc=1
  fi

  if windows_venv_damaged; then
    bad "the repo's .venv has been rebuilt for LINUX — the Windows env is broken"
    echo "        Repair:  rm -rf '$REPO/.venv'   then, from Windows:  uv sync"
    echo "        Cause:   a uv command ran here without UV_PROJECT_ENVIRONMENT set."
    rc=1
  fi

  echo
  [ "$rc" -eq 0 ] && echo "READY" || echo "NOT READY — see FAIL lines above"
  return "$rc"
}

# --------------------------------------------------------------- ensure ----
cmd_ensure() {
  if [ "$(id -u)" -eq 0 ]; then
    bad "running as root — the toolchain would be stranded in /root. Run as the default user."
    return 1
  fi

  command -v java >/dev/null 2>&1 || {
    bad "no java. Install it, then re-run:"
    echo "        sudo apt update && sudo apt install -y openjdk-17-jre-headless"
    return 1
  }

  if [ ! -x "$UV" ]; then
    echo "installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || {
      bad "uv install failed"; return 1; }
  fi
  ok "uv $("$UV" --version)"

  [ -d "$REPO" ] || { bad "repo not reachable at '$REPO'"; return 1; }

  # uv fetches a managed CPython 3.11: Ubuntu ships 3.14 and pyspark 3.5.x predates it.
  "$UV" python install "$PY_MINOR" --quiet || { bad "could not install CPython $PY_MINOR through uv"; return 1; }
  ok "python $("$UV" python find "$PY_MINOR")"

  # --frozen: uv.lock is the tracked contract and is written on Windows (`uv lock`); a WSL run
  # must never rewrite it. An out-of-date lock is therefore a FAIL here, not a silent relock.
  echo "syncing the locked environment into $VENV ..."
  ( cd "$REPO" && "$UV" sync --frozen --python "$PY_MINOR" ) || {
    bad "uv sync --frozen failed — if uv.lock is out of date, run 'uv lock' on Windows first"
    return 1; }

  if windows_venv_damaged; then
    bad "the repo's .venv was rebuilt for Linux during sync — this should be impossible with UV_PROJECT_ENVIRONMENT set"
    return 1
  fi

  ok "venv ready: $("$VENV/bin/python" -V 2>&1), pyspark $("$VENV/bin/python" -c 'import pyspark;print(pyspark.__version__)')"
  echo
  echo "READY — prove it with:  scripts\\spark_wsl.ps1 -Verify"
}

# ---------------------------------------------------------------- verify ---
# Known-answer probe: proves Spark COMPUTES CORRECTLY and WRITES here, not merely that a
# session starts. Group-by, a Python UDF, a Parquet write read back, and a Hive database +
# CTAS (the path dbt-spark takes) all run against a scratch dir on ext4; emits one JSON line.
cmd_verify() {
  [ -x "$VENV/bin/python" ] || { echo '{"ok": false, "error": "no venv — run ensure"}'; return 1; }
  local scratch
  scratch=$(mktemp -d /tmp/audio-features-verify.XXXXXX)
  ( cd "$REPO" && SPARK_WSL_SCRATCH="$scratch" "$VENV/bin/python" - <<'PY'
import json, os, platform, shutil, sys
out = {"ok": False}
scratch = os.environ["SPARK_WSL_SCRATCH"]
try:
    import pyspark
    from pyspark.sql import functions as F
    from audio_features.spark_session import build_spark
    overrides = {
        "spark.sql.shuffle.partitions": "8",
        "spark.sql.warehouse.dir": f"file://{scratch}/warehouse",
        "spark.driver.host": "127.0.0.1",
        "spark.driver.bindAddress": "127.0.0.1",
        "spark.hadoop.javax.jdo.option.ConnectionURL": f"jdbc:derby:;databaseName={scratch}/metastore_db;create=true",
    }
    spark = build_spark("dev", app_name="wsl-verify", overrides=overrides)
    df = spark.createDataFrame([(1, "a"), (2, "b"), (3, "a")], ["n", "k"])
    agg = sorted(tuple(r) for r in df.groupBy("k").agg(F.sum("n").alias("t")).collect())
    udf = df.select(F.udf(lambda x: x * 10, "int")("n").alias("u")).agg(F.sum("u")).collect()[0][0]
    df.write.mode("overwrite").parquet(f"{scratch}/plain")
    written = spark.read.parquet(f"{scratch}/plain").count()
    spark.sql("create database if not exists verify_db")
    spark.sql(f"create table verify_db.things using parquet location '{scratch}/verify_db/things' "
              "as select * from values (1, 'a'), (2, 'b'), (3, 'a') as t(n, k)")
    hive = spark.sql("select sum(n) from verify_db.things").collect()[0][0]
    out.update(
        python=platform.python_version(),
        executable=sys.executable,
        pyspark=pyspark.__version__,
        spark=spark.version,
        java=spark.sparkContext._jvm.System.getProperty("java.version"),
        local_dir=spark.conf.get("spark.local.dir", None),
        agg_ok=(agg == [("a", 4), ("b", 2)]),
        udf_ok=(udf == 60),
        write_ok=(written == 3),
        hive_ok=(hive == 6),
    )
    out["ok"] = out["agg_ok"] and out["udf_ok"] and out["write_ok"] and out["hive_ok"]
    spark.stop()
except Exception as exc:
    out["error"] = f"{type(exc).__name__}: {str(exc).splitlines()[0][:300]}"
finally:
    shutil.rmtree(scratch, ignore_errors=True)
print(json.dumps(out))
PY
  )
}

# ------------------------------------------------------------------- run ---
# `uv run <args>` in the repo, in THIS venv. The command line arrives base64-encoded in
# SPARK_WSL_CMD_B64 because PowerShell 5.1 mangles embedded quotes on the way to a native
# command; `eval set --` then applies bash's own word splitting, so quoted -c payloads survive.
cmd_run() {
  [ -x "$VENV/bin/python" ] || { bad "no venv at $VENV — run: scripts\\spark_wsl.ps1 -Setup"; return 127; }
  [ -n "${SPARK_WSL_CMD_B64:-}" ] || { bad "nothing to run"; return 2; }
  local cmdline
  cmdline=$(printf '%s' "$SPARK_WSL_CMD_B64" | base64 -d)
  eval "set -- $cmdline"
  cd "$REPO" && exec "$UV" run "$@"
}

case "${1:-check}" in
  check)  cmd_check ;;
  ensure) cmd_ensure ;;
  verify) cmd_verify ;;
  run)    cmd_run ;;
  *) echo "usage: $0 {check|ensure|verify|run}" >&2; exit 2 ;;
esac
