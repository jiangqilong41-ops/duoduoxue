import json
import unittest
from pathlib import Path


class CodexCourseContentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parent
        cls.course = json.loads(
            (cls.root / "codex-harness.json").read_text(encoding="utf-8")
        )
        cls.lab = (cls.root / "labs" / "codex.md").read_text(encoding="utf-8")
        cls.decks = {deck["code"]: deck for deck in cls.course["decks"]}

    def question(self, code: str, number: int) -> dict:
        return self.decks[code]["questions"][number - 1]

    def test_strict_validation_uses_supported_offline_runtime_command(self) -> None:
        combined = json.dumps(self.course, ensure_ascii=False) + self.lab

        self.assertNotIn("codex --strict-config features", combined)
        self.assertIn("codex --strict-config mcp-server </dev/null", combined)
        self.assertIn("codex features list", combined)

    def test_global_agents_override_is_checked_before_base_file(self) -> None:
        question = json.dumps(self.question("CX03", 2), ensure_ascii=False)

        self.assertIn("$HOME/.codex/AGENTS.override.md", self.lab)
        self.assertIn("AGENTS.override.md", question)
        self.assertLess(
            self.lab.index("$HOME/.codex/AGENTS.override.md"),
            self.lab.index("$HOME/.codex/AGENTS.md"),
        )

    def test_effective_config_requires_valid_layer_and_managed_constraints(self) -> None:
        question = self.question("CX02", 1)
        combined = question["answer"] + question["explanation"]

        self.assertIn("所在层允许", combined)
        self.assertIn("requirements", combined)

    def test_policy_probe_only_emits_known_top_level_enum_values(self) -> None:
        section = self.lab.split("## CX02", 1)[0]

        self.assertNotIn("value=substr", section)
        self.assertIn("in_table", section)
        self.assertIn('print "approval_policy=never"', section)
        self.assertIn('print "sandbox_mode=danger-full-access"', section)

    def test_project_config_probe_walks_repo_root_to_cwd(self) -> None:
        section = self.lab.split("## CX04", 1)[1].split("## CX05", 1)[0]

        self.assertIn("project_config[", section)
        self.assertIn("relative_to(root)", section)
        self.assertNotIn("cwd_project_config=", section)

    def test_skill_probe_covers_all_documented_source_classes(self) -> None:
        section = self.lab.split("## CX05", 1)[1].split("## CX06", 1)[0]

        for marker in (
            "CWD 到仓库根",
            "$HOME/.agents/skills",
            "/etc/codex/skills",
            "SYSTEM",
            "Plugin",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, section)

    def test_diagnostic_axes_mark_non_applicable_states(self) -> None:
        section = self.lab.split("## CX10", 1)[1]
        questions = json.dumps(
            [self.question("CX10", 1), self.question("CX10", 2)],
            ensure_ascii=False,
        )

        self.assertIn("N/A", section)
        self.assertIn("不适用", questions)
        self.assertNotIn("缺哪列就停在哪列", section)

    def test_rules_lab_has_side_effect_free_match_vectors(self) -> None:
        section = self.lab.split("## CX08", 1)[1].split("## CX09", 1)[0]

        self.assertIn('match = ["git status", "git status --short"]', section)
        self.assertIn('not_match = ["git push"]', section)
        self.assertIn("codex execpolicy check --pretty", section)

    def test_subagent_sandbox_inheritance_is_qualified_as_default(self) -> None:
        section = self.lab.split("## CX09", 1)[1].split("## CX10", 1)[0]

        self.assertIn("默认继承父任务沙箱", section)
        self.assertIn("sandbox_mode", section)


if __name__ == "__main__":
    unittest.main()
