"""layers.py and spark_session.py's profile reader are facts; these tests pin them (no JVM, no network).

LAYERS is duplicated on purpose between the package and the audit script (the audit runs as a
`sys.executable -I` script and cannot import the package), so "shared" means the first test here
asserts the two literals agree.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from audio_features import layers
from audio_features.spark_session import PROFILES_PATH, profile_spark_config

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT = REPO_ROOT / ".claude" / "skills" / "warehouse-audit" / "audit_warehouse.py"


def load_audit_module():
    """Import the audit script from its path, the way its `main()` guard allows (no side effects)."""
    spec = importlib.util.spec_from_file_location("audit_warehouse", AUDIT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_layers_literal_matches_the_audit_script():
    audit = load_audit_module()
    assert tuple(audit.LAYERS) == layers.LAYERS
    assert layers.LAYERS == ("ingest", "cleansed", "staging", "modeled", "report")


def test_layer_path_mirrors_environment_layer_source_table():
    path = layers.layer_path("dev", "cleansed", "musicbrainz", "artists")
    assert path.as_posix().endswith("data/dev/cleansed/musicbrainz/artists")
    assert path == layers.DATA_ROOT / "dev" / "cleansed" / "musicbrainz" / "artists"


def test_layer_path_honours_data_root_and_omits_table_when_absent(tmp_path: Path):
    assert layers.layer_path("prd", "staging", "musicbrainz", "a", data_root=tmp_path) == (
        tmp_path / "prd" / "staging" / "musicbrainz" / "a"
    )
    assert layers.layer_path("prd", "report", "music", data_root=tmp_path) == (
        tmp_path / "prd" / "report" / "music"
    )


def test_schema_name_is_layer_underscore_source():
    assert layers.schema_name("cleansed", "musicbrainz") == "cleansed_musicbrainz"
    assert layers.schema_name("modeled", "music") == "modeled_music"


def test_unknown_layer_and_environment_are_value_errors_naming_the_allowed_values():
    with pytest.raises(ValueError, match="unknown layer 'bronze'.*ingest, cleansed, staging"):
        layers.layer_path("dev", "bronze", "musicbrainz")
    with pytest.raises(ValueError, match="unknown layer 'bronze'"):
        layers.schema_name("bronze", "musicbrainz")
    with pytest.raises(ValueError, match="unknown environment 'test'.*dev, prd"):
        layers.environment_root("test")
    with pytest.raises(ValueError, match="unknown environment 'test'.*dev, prd"):
        profile_spark_config("test")


def test_profile_spark_config_missing_file_is_empty(tmp_path: Path):
    assert profile_spark_config("dev", profiles_path=tmp_path / "profiles.yml") == {}


def test_profile_spark_config_missing_target_is_key_error_naming_known_targets(tmp_path: Path):
    profiles = tmp_path / "profiles.yml"
    profiles.write_text(
        "audio_features:\n"
        "  target: dev\n"
        "  outputs:\n"
        "    dev:\n"
        "      type: spark\n"
        "      method: session\n"
        "      server_side_parameters:\n"
        "        spark.sql.shuffle.partitions: 8\n",
        encoding="utf-8",
    )
    with pytest.raises(KeyError, match=r"no target 'prd'.*known targets: \['dev'\]"):
        profile_spark_config("prd", profiles_path=profiles)
    assert profile_spark_config("dev", profiles_path=profiles) == {
        "spark.sql.shuffle.partitions": "8"
    }


def test_profile_spark_config_missing_profile_is_key_error(tmp_path: Path):
    profiles = tmp_path / "profiles.yml"
    profiles.write_text("other_project:\n  outputs: {}\n", encoding="utf-8")
    with pytest.raises(KeyError, match="no profile 'audio_features'.*other_project"):
        profile_spark_config("dev", profiles_path=profiles)


def test_repo_profiles_targets_share_keys_and_root_the_warehouse_under_their_data_dir():
    assert PROFILES_PATH == REPO_ROOT / "profiles.yml"
    dev = profile_spark_config("dev")
    prd = profile_spark_config("prd")
    assert set(dev) == set(prd)
    for target, config in (("dev", dev), ("prd", prd)):
        assert config["spark.sql.warehouse.dir"].startswith(f"data/{target}/")
        assert f"databaseName=metastore_db/{target}" in config[
            "spark.hadoop.javax.jdo.option.ConnectionURL"
        ]
        assert config["spark.sql.legacy.allowNonEmptyLocationInCTAS"] == "true"
