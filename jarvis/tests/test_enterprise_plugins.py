"""Tests fuer die 128 generierten Enterprise-Katalog-Plugins in ``plugins/``."""

import json
import subprocess
import sys
from pathlib import Path
from unittest import TestCase

from open_jarvis.enterprise.catalog import all_plugins
from open_jarvis.plugins.registry import build_plugin_registry

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = REPO_ROOT / "plugins"
REQUIRED_MANIFEST_FIELDS = {"id", "name", "version", "entrypoint", "description", "permissions"}
EXPECTED_PERMISSIONS = ["commands.register", "ui.notify"]
EXAMPLE_PLUGIN_ID = "enterprise_enterprise_live_ticker"
# Zusaetzliche, nicht aus dem Katalog generierte Plugins (echte Funktions-Plugins).
EXTRA_PLUGIN_IDS = {"agent_jarvis_agent"}


class EnterprisePluginsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = build_plugin_registry(PLUGINS_ROOT)
        cls.entries = cls.registry["plugins"]
        # Nur die 128 aus dem Katalog generierten Plugins.
        cls.catalog_entries = [e for e in cls.entries if e["id"] not in EXTRA_PLUGIN_IDS]

    def test_registry_contains_128_catalog_plugins_plus_extras(self):
        self.assertEqual(len(self.catalog_entries), 128)
        self.assertEqual(len(self.entries), 128 + len(EXTRA_PLUGIN_IDS))
        self.assertEqual(self.registry["summary"]["total"], 128 + len(EXTRA_PLUGIN_IDS))
        for extra_id in EXTRA_PLUGIN_IDS:
            self.assertIn(extra_id, {e["id"] for e in self.entries})

    def test_registry_has_zero_issues_across_all_entries(self):
        problems = {entry["id"]: entry["issues"] for entry in self.entries if entry["issues"]}
        self.assertEqual(problems, {})
        self.assertEqual(self.registry["summary"]["blocked"], 0)
        self.assertEqual(self.registry["summary"]["missing"], 0)

    def test_plugin_ids_are_unique_and_well_formed(self):
        ids = [entry["id"] for entry in self.entries]
        self.assertEqual(len(ids), len(set(ids)))
        for plugin_id in ids:
            self.assertRegex(plugin_id, r"^[a-z][a-z0-9_-]{2,63}$")

    def test_every_manifest_has_required_fields_and_expected_permissions(self):
        for entry in self.entries:
            manifest = entry["manifest"]
            missing = REQUIRED_MANIFEST_FIELDS - set(manifest)
            self.assertEqual(missing, set(), f"{entry['id']}: fehlende Felder {sorted(missing)}")
            self.assertEqual(manifest["permissions"], EXPECTED_PERMISSIONS, entry["id"])
            self.assertEqual(manifest["version"], "1.0.0", entry["id"])
            self.assertEqual(manifest["entrypoint"], "main.py", entry["id"])
            self.assertFalse(entry["legacy"], entry["id"])
            self.assertTrue(str(manifest["description"]).strip(), entry["id"])

    def test_example_entrypoint_runs_and_prints_valid_json(self):
        entrypoint = PLUGINS_ROOT / EXAMPLE_PLUGIN_ID / "main.py"
        self.assertTrue(entrypoint.is_file())

        result = subprocess.run(
            [sys.executable, str(entrypoint)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["plugin_id"], EXAMPLE_PLUGIN_ID)
        self.assertEqual(payload["kategorie"], "Enterprise")
        self.assertTrue(3 <= len(payload["befehle"]) <= 5)
        for command in payload["befehle"]:
            self.assertIsInstance(command, str)
            self.assertTrue(command.strip())

    def test_manifest_names_match_catalog_plugins_exactly(self):
        catalog_names = all_plugins()
        manifest_names = [entry["manifest"]["name"] for entry in self.catalog_entries]
        self.assertEqual(len(catalog_names), 128)
        self.assertEqual(len(manifest_names), len(set(manifest_names)))
        self.assertEqual(set(manifest_names), set(catalog_names))
