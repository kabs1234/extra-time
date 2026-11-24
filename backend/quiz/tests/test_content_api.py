from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from quiz.models import Choice, Era, Question, Topic

PASSWORD = "kick-off-1863"


def make_question(author: User, era: Era, text: str = "Who won the first World Cup?") -> Question:
    question = Question.objects.create(text=text, explanation="Uruguay beat Argentina 4–2 in 1930.", era=era, author=author)
    Choice.objects.create(question=question, text="Uruguay", is_correct=True)
    Choice.objects.create(question=question, text="Argentina")
    return question


class ContentApiTestCase(APITestCase):
    def setUp(self) -> None:
        self.author = User.objects.create_user("author", password=PASSWORD)
        self.other = User.objects.create_user("other", password=PASSWORD)
        self.staff = User.objects.create_user("staff", password=PASSWORD, is_staff=True)
        self.era = Era.objects.create(name="Early World Cups", start_year=1930, end_year=1950, summary="")
        self.topic = Topic.objects.create(name="World Cups", slug="world-cups")
        self.question = make_question(self.author, self.era)

    def login_as(self, user: User) -> None:
        self.client.force_authenticate(user)

    def question_payload(self, correct_flags: tuple[bool, ...] = (True, False)) -> dict:
        return {
            "text": "Which country hosted the 1950 World Cup?",
            "difficulty": "easy",
            "explanation": "Brazil hosted, and Uruguay won the deciding match at the Maracanã.",
            "era": self.era.id,
            "topics": [self.topic.id],
            "choices": [{"text": f"Option {index}", "is_correct": flag} for index, flag in enumerate(correct_flags)],
        }


class AnswerSecrecyTests(ContentApiTestCase):
    def test_public_can_list_questions_without_answers(self) -> None:
        response = self.client.get("/api/questions/")

        self.assertEqual(response.status_code, 200)
        question = response.json()["results"][0]
        self.assertNotIn("explanation", question)
        self.assertTrue(all("is_correct" not in choice for choice in question["choices"]))

    def test_other_user_does_not_see_answers(self) -> None:
        self.login_as(self.other)

        question = self.client.get(f"/api/questions/{self.question.id}/").json()

        self.assertNotIn("explanation", question)
        self.assertTrue(all("is_correct" not in choice for choice in question["choices"]))

    def test_author_sees_answers(self) -> None:
        self.login_as(self.author)

        question = self.client.get(f"/api/questions/{self.question.id}/").json()

        self.assertIn("explanation", question)
        self.assertEqual([choice["is_correct"] for choice in question["choices"]], [True, False])

    def test_public_choice_list_hides_answers(self) -> None:
        choices = self.client.get("/api/choices/").json()["results"]

        self.assertTrue(all("is_correct" not in choice for choice in choices))


class WritePermissionTests(ContentApiTestCase):
    def test_anonymous_write_is_401(self) -> None:
        for path in ("/api/eras/", "/api/topics/", "/api/questions/", "/api/choices/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.post(path, {}, format="json").status_code, 401)

    def test_player_cannot_create_era(self) -> None:
        self.login_as(self.other)

        response = self.client.post("/api/eras/", {"name": "X", "start_year": 1, "end_year": 2}, format="json")

        self.assertEqual(response.status_code, 403)

    def test_staff_can_crud_era(self) -> None:
        self.login_as(self.staff)
        payload = {"name": "Modern", "start_year": 2000, "end_year": 2025, "summary": "Pressing and data."}

        created = self.client.post("/api/eras/", payload, format="json")
        era_url = f"/api/eras/{created.json()['id']}/"
        put = self.client.put(era_url, {**payload, "summary": "New"}, format="json")
        patch = self.client.patch(era_url, {"name": "Modern game"}, format="json")
        delete = self.client.delete(era_url)

        self.assertEqual([created.status_code, put.status_code, patch.status_code, delete.status_code], [201, 200, 200, 204])

    def test_era_rejects_start_after_end(self) -> None:
        self.login_as(self.staff)

        response = self.client.post("/api/eras/", {"name": "Bad", "start_year": 2000, "end_year": 1990}, format="json")

        self.assertEqual(response.status_code, 400)

    def test_non_author_cannot_edit_or_delete_question(self) -> None:
        self.login_as(self.other)
        url = f"/api/questions/{self.question.id}/"

        self.assertEqual(self.client.patch(url, {"text": "Hacked"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)

    def test_staff_can_edit_any_question(self) -> None:
        self.login_as(self.staff)

        response = self.client.patch(f"/api/questions/{self.question.id}/", {"text": "Edited"}, format="json")

        self.assertEqual(response.status_code, 200)

    def test_non_author_cannot_add_choice(self) -> None:
        self.login_as(self.other)

        response = self.client.post("/api/choices/", {"question": self.question.id, "text": "Italy"}, format="json")

        self.assertEqual(response.status_code, 403)


class QuestionWriteTests(ContentApiTestCase):
    def test_player_creates_question_with_choices(self) -> None:
        self.login_as(self.other)

        response = self.client.post("/api/questions/", self.question_payload(), format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["author"], "other")
        self.assertEqual(len(response.json()["choices"]), 2)

    def test_question_needs_exactly_one_correct_choice(self) -> None:
        self.login_as(self.other)

        for flags in ((False, False), (True, True), (True,), (True, False, False, False, False)):
            with self.subTest(flags=flags):
                response = self.client.post("/api/questions/", self.question_payload(flags), format="json")
                self.assertEqual(response.status_code, 400)
                self.assertIn("choices", response.json())

    def test_question_create_requires_choices(self) -> None:
        self.login_as(self.other)
        payload = self.question_payload()
        del payload["choices"]

        response = self.client.post("/api/questions/", payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("choices", response.json())

    def test_put_replaces_choices(self) -> None:
        self.login_as(self.author)

        response = self.client.put(
            f"/api/questions/{self.question.id}/", self.question_payload((False, True, False)), format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([choice.is_correct for choice in self.question.choices.all()], [False, True, False])

    def test_patch_without_choices_keeps_them(self) -> None:
        self.login_as(self.author)

        self.client.patch(f"/api/questions/{self.question.id}/", {"text": "Renamed"}, format="json")

        self.assertEqual(self.question.choices.count(), 2)

    def test_mine_filter_returns_only_own_questions(self) -> None:
        make_question(self.other, self.era, text="Other's question")
        self.login_as(self.author)

        results = self.client.get("/api/questions/?mine=true").json()["results"]

        self.assertEqual([question["id"] for question in results], [self.question.id])
        self.assertIn("is_correct", results[0]["choices"][0])


class ChoiceWriteTests(ContentApiTestCase):
    def test_author_cannot_add_second_correct_choice(self) -> None:
        self.login_as(self.author)

        response = self.client.post(
            "/api/choices/", {"question": self.question.id, "text": "Italy", "is_correct": True}, format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_author_adds_wrong_choice(self) -> None:
        self.login_as(self.author)

        response = self.client.post("/api/choices/", {"question": self.question.id, "text": "Italy"}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.question.choices.count(), 3)

    def test_author_cannot_add_fifth_choice(self) -> None:
        Choice.objects.create(question=self.question, text="Italy")
        Choice.objects.create(question=self.question, text="Brazil")
        self.login_as(self.author)

        response = self.client.post("/api/choices/", {"question": self.question.id, "text": "Spain"}, format="json")

        self.assertEqual(response.status_code, 400)

    def test_author_cannot_delete_the_correct_choice(self) -> None:
        Choice.objects.create(question=self.question, text="Italy")
        self.login_as(self.author)
        correct = self.question.choices.get(is_correct=True)

        response = self.client.delete(f"/api/choices/{correct.id}/")

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Choice.objects.filter(pk=correct.pk).exists())


class ChoiceMoveTests(ContentApiTestCase):
    def test_choice_cannot_move_to_another_question(self) -> None:
        other_question = make_question(self.author, self.era, text="Second question")
        wrong = self.question.choices.get(is_correct=False)
        self.login_as(self.author)

        self.client.patch(f"/api/choices/{wrong.id}/", {"question": other_question.id}, format="json")

        wrong.refresh_from_db()
        self.assertEqual(wrong.question_id, self.question.id)
        self.assertEqual(self.question.choices.count(), 2)


class AdminChoiceRuleTests(ContentApiTestCase):
    def test_admin_rejects_question_without_correct_choice(self) -> None:
        superuser = User.objects.create_superuser("root", password=PASSWORD)
        self.client.force_login(superuser)
        form = {
            "text": "Admin question",
            "difficulty": "easy",
            "explanation": "",
            "era": self.era.id,
            "author": superuser.id,
            "choices-TOTAL_FORMS": "2",
            "choices-INITIAL_FORMS": "0",
            "choices-MIN_NUM_FORMS": "0",
            "choices-MAX_NUM_FORMS": "1000",
            "choices-0-text": "A",
            "choices-1-text": "B",
        }

        response = self.client.post("/admin/quiz/question/add/", form)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Question.objects.filter(text="Admin question").exists())


class ChoiceOwnershipTests(ContentApiTestCase):
    def test_non_author_gets_403_even_when_the_choice_set_would_be_invalid(self) -> None:
        self.login_as(self.other)

        response = self.client.post(
            "/api/choices/", {"question": self.question.id, "text": "Italy", "is_correct": True}, format="json"
        )

        self.assertEqual(response.status_code, 403)
