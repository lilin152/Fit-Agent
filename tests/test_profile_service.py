from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import BodyProfilePatch, ExerciseHistoryInput, InjuryInput
from app.services.profile_service import ProfileService


class ProfileServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = TemporaryDirectory()
        repository = ProfileRepository(
            Path(self.temp_directory.name) / "fitness.db"
        )
        repository.initialize()
        with repository._connect() as connection:
            connection.execute(
                """
                INSERT INTO users (email, password_hash, username)
                VALUES ('test@example.com', 'hash', 'Tester')
                """
            )
            connection.commit()
        self.service = ProfileService(repository)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_validate_profile_patch_requires_core_fields(self) -> None:
        result = self.service.validate_patch(1, BodyProfilePatch(height_cm=175))

        self.assertFalse(result.ready_to_save)
        self.assertIn("sex", result.missing_fields)
        self.assertIn("weight_kg", result.missing_fields)
        self.assertIn("goals", result.missing_fields)

    def test_complete_profile_patch_is_normalized(self) -> None:
        result = self.service.validate_patch(
            1,
            BodyProfilePatch(
                sex="male",
                height_cm=175,
                weight_kg=70,
                exercise_history=ExerciseHistoryInput(
                    summary="每周训练三次，坚持半年",
                    sessions_per_week=3,
                    continuous_months=6,
                ),
                goals=["fat_loss"],
            ),
        )

        self.assertTrue(result.ready_to_save)
        self.assertEqual(
            result.normalized_profile["experience_level"], "intermediate"
        )
        self.assertEqual(result.normalized_profile["assessment_status"], "pending")

    def test_current_pain_blocks_fitness_assessment(self) -> None:
        patch = BodyProfilePatch(
            sex="female",
            height_cm=165,
            weight_kg=55,
            exercise_history=ExerciseHistoryInput(
                summary="很少锻炼", sessions_per_week=0, continuous_months=0
            ),
            goals=["fat_loss"],
            injuries=[
                InjuryInput(
                    body_part="left_knee",
                    side="left",
                    status="active",
                    pain_score=5,
                    description="深蹲疼痛",
                )
            ],
        )

        result = self.service.validate_patch(1, patch)

        self.assertTrue(result.ready_to_save)
        self.assertEqual(result.normalized_profile["assessment_status"], "blocked")
        safety = self.service.assess_safety(result.normalized_profile)
        self.assertFalse(safety.assessment_allowed)
        self.assertIn("CURRENT_PAIN", safety.reason_codes)

    def test_save_patch_persists_improvement_areas_and_injuries(self) -> None:
        patch = BodyProfilePatch.model_validate(
            {
                "sex": "female",
                "height_cm": 166,
                "weight_kg": 58,
                "exercise_history": {
                    "summary": "每周一次瑜伽",
                    "sessions_per_week": 1,
                    "continuous_months": 2,
                },
                "goals": ["fat_loss"],
                "improvement_areas": [
                    {"body_part": "shoulder_posture", "description": "改善圆肩"}
                ],
                "injuries": [
                    {
                        "body_part": "ankle",
                        "side": "left",
                        "status": "previous",
                        "pain_score": 0,
                        "description": "旧伤",
                    },
                    {
                        "body_part": "wrist",
                        "side": "right",
                        "status": "previous",
                        "pain_score": 0,
                    }
                ],
            }
        )

        saved = self.service.save_patch(1, patch, expected_version=1)

        self.assertEqual(saved["version"], 2)
        self.assertEqual(
            saved["improvement_areas"][0]["body_part"], "shoulder_posture"
        )
        self.assertEqual(saved["injuries"][0]["body_part"], "ankle")

        updated = self.service.save_patch(
            1,
            BodyProfilePatch(
                injuries=[
                    InjuryInput(
                        body_part="ankle",
                        side="left",
                        status="recovering",
                        pain_score=2,
                    )
                ]
            ),
            expected_version=2,
        )

        self.assertEqual(len(updated["injuries"]), 2)
        self.assertEqual(updated["injuries"][0]["status"], "recovering")
        self.assertEqual(updated["injuries"][0]["description"], "旧伤")
        self.assertEqual(updated["injuries"][1]["body_part"], "wrist")


if __name__ == "__main__":
    unittest.main()
