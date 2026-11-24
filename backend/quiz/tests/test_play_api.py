from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.test import APITestCase

from quiz.models import Choice, Era, Question, QuizAttempt, Topic

PASSWORD = "kick-off-1863"


def make_question(author: User, era: Era, number: int) -> Question:
    question = Question.objects.create(
        text=f"Question {number}", explanation=f"Because of fact {number}.", era=era, author=author
    )
    Choice.objects.create(question=question, text=f"Right {number}", is_correct=True)
    Choice.objects.create(question=question, text=f"Wrong {number}")
    return question


class PlayApiTestCase(APITestCase):
    def setUp(self) -> None:
        self.curator = User.objects.create_user("curator", password=PASSWORD, is_staff=True)
        self.player = User.objects.create_user("player", password=PASSWORD)
        self.rival = User.objects.create_user("rival", password=PASSWORD)
        self.era = Era.objects.create(name="Origins", start_year=1863, end_year=1900, summary="")
        self.other_era = Era.objects.create(name="Interwar", start_year=1919, end_year=1939, summary="")
        self.topic = Topic.objects.create(name="Rules", slug="rules")
        self.questions = [make_question(self.curator, self.era, number) for number in range(3)]
        self.questions[0].topics.add(self.topic)

    def right(self, question: Question) -> Choice:
        return question.choices.get(is_correct=True)

    def wrong(self, question: Question) -> Choice:
        return question.choices.get(is_correct=False)

    def submit(self, answers: list[dict], **filters: int) -> Response:
        return self.client.post("/api/attempts/", {**filters, "answers": answers}, format="json")


class QuizTests(PlayApiTestCase):
    def test_quiz_requires_auth(self) -> None:
        self.assertEqual(self.client.get("/api/quiz/").status_code, 401)

    def test_quiz_excludes_own_questions(self) -> None:
        own = make_question(self.player, self.era, 99)
        self.client.force_authenticate(self.player)

        ids = [question["id"] for question in self.client.get("/api/quiz/?count=20").json()]

        self.assertNotIn(own.id, ids)
        self.assertEqual(len(ids), 3)

    def test_quiz_returns_fewer_when_not_enough(self) -> None:
        self.client.force_authenticate(self.player)

        response = self.client.get(f"/api/quiz/?era={self.era.id}&count=10")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

    def test_quiz_filters_by_topic(self) -> None:
        self.client.force_authenticate(self.player)

        questions = self.client.get(f"/api/quiz/?topic={self.topic.id}").json()

        self.assertEqual([question["id"] for question in questions], [self.questions[0].id])

    def test_quiz_count_is_clamped(self) -> None:
        for number in range(3, 30):
            make_question(self.curator, self.era, number)
        self.client.force_authenticate(self.player)

        self.assertEqual(len(self.client.get("/api/quiz/?count=1").json()), 5)
        self.assertEqual(len(self.client.get("/api/quiz/?count=50").json()), 20)
        self.assertEqual(len(self.client.get("/api/quiz/").json()), 10)

    def test_quiz_empty_is_200(self) -> None:
        self.client.force_authenticate(self.player)

        response = self.client.get(f"/api/quiz/?era={self.other_era.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_quiz_rejects_unknown_era(self) -> None:
        self.client.force_authenticate(self.player)

        self.assertEqual(self.client.get("/api/quiz/?era=999999").status_code, 400)
        self.assertEqual(self.client.get("/api/quiz/?era=abc").status_code, 400)

    def test_quiz_hides_answers(self) -> None:
        self.client.force_authenticate(self.player)

        question = self.client.get("/api/quiz/").json()[0]

        self.assertNotIn("explanation", question)
        self.assertTrue(all("is_correct" not in choice for choice in question["choices"]))


class AttemptTests(PlayApiTestCase):
    def test_submit_attempt_scores_and_reveals(self) -> None:
        self.client.force_authenticate(self.player)
        first, second, third = self.questions

        response = self.submit(
            [
                {"question": first.id, "choice": self.right(first).id},
                {"question": second.id, "choice": self.wrong(second).id},
                {"question": third.id, "choice": None},
            ],
            era=self.era.id,
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual((body["score"], body["total"], body["percent"]), (1, 3, 33))
        self.assertEqual(body["era_name"], "Origins")
        self.assertEqual([answer["is_correct"] for answer in body["answers"]], [True, False, False])
        self.assertEqual(body["answers"][1]["chosen_text"], "Wrong 1")
        self.assertEqual(body["answers"][1]["correct_text"], "Right 1")
        self.assertEqual(body["answers"][2]["chosen_text"], "")
        self.assertEqual(body["answers"][0]["explanation"], "Because of fact 0.")

    def test_submit_rejects_choice_from_other_question(self) -> None:
        self.client.force_authenticate(self.player)
        first, second, _ = self.questions

        response = self.submit([{"question": first.id, "choice": self.right(second).id}])

        self.assertEqual(response.status_code, 400)

    def test_submit_rejects_own_question(self) -> None:
        own = make_question(self.player, self.era, 99)
        self.client.force_authenticate(self.player)

        response = self.submit([{"question": own.id, "choice": self.right(own).id}])

        self.assertEqual(response.status_code, 400)

    def test_submit_rejects_empty_and_duplicate_answers(self) -> None:
        self.client.force_authenticate(self.player)
        first = self.questions[0]

        self.assertEqual(self.submit([]).status_code, 400)
        duplicate = [{"question": first.id, "choice": None}, {"question": first.id, "choice": None}]
        self.assertEqual(self.submit(duplicate).status_code, 400)

    def test_attempts_are_private(self) -> None:
        self.client.force_authenticate(self.rival)
        rival_attempt_id = self.submit([{"question": self.questions[0].id, "choice": None}]).json()["id"]
        self.client.force_authenticate(self.player)
        own_attempt_id = self.submit([{"question": self.questions[0].id, "choice": None}]).json()["id"]

        listed = [attempt["id"] for attempt in self.client.get("/api/attempts/").json()["results"]]

        self.assertEqual(listed, [own_attempt_id])
        self.assertEqual(self.client.get(f"/api/attempts/{rival_attempt_id}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/attempts/{rival_attempt_id}/").status_code, 404)

    def test_attempt_update_is_405(self) -> None:
        self.client.force_authenticate(self.player)
        attempt_id = self.submit([{"question": self.questions[0].id, "choice": None}]).json()["id"]

        self.assertEqual(self.client.patch(f"/api/attempts/{attempt_id}/", {"score": 9}, format="json").status_code, 405)
        self.assertEqual(self.client.put(f"/api/attempts/{attempt_id}/", {}, format="json").status_code, 405)

    def test_attempt_delete_own_is_204(self) -> None:
        self.client.force_authenticate(self.player)
        attempt_id = self.submit([{"question": self.questions[0].id, "choice": None}]).json()["id"]

        self.assertEqual(self.client.delete(f"/api/attempts/{attempt_id}/").status_code, 204)
        self.assertFalse(QuizAttempt.objects.filter(pk=attempt_id).exists())

    def test_attempt_survives_question_deletion(self) -> None:
        self.client.force_authenticate(self.player)
        first = self.questions[0]
        attempt_id = self.submit([{"question": first.id, "choice": self.right(first).id}]).json()["id"]
        first.delete()

        answer = self.client.get(f"/api/attempts/{attempt_id}/").json()["answers"][0]

        self.assertEqual((answer["question"], answer["question_text"], answer["explanation"]), (None, "Question 0", ""))


class LeaderboardTests(PlayApiTestCase):
    def test_leaderboard_is_public_and_ordered(self) -> None:
        first, second, third = self.questions
        self.client.force_authenticate(self.rival)
        self.submit([{"question": first.id, "choice": self.right(first).id}])
        self.client.force_authenticate(self.player)
        self.submit([{"question": question.id, "choice": self.right(question).id} for question in self.questions])
        self.submit([{"question": first.id, "choice": self.wrong(first).id}])
        self.client.force_authenticate(None)

        response = self.client.get("/api/leaderboard/")

        self.assertEqual(response.status_code, 200)
        rows = response.json()
        self.assertEqual([row["username"] for row in rows], ["player", "rival"])
        self.assertEqual(
            rows[0],
            {
                "rank": 1,
                "username": "player",
                "favorite_club": "",
                "attempts": 2,
                "total_correct": 3,
                "best_score_pct": 100,
            },
        )
        self.assertEqual(rows[1]["rank"], 2)

    def test_leaderboard_breaks_ties_by_best_percent(self) -> None:
        first, second, _ = self.questions
        self.client.force_authenticate(self.rival)
        self.submit([{"question": first.id, "choice": self.right(first).id}, {"question": second.id, "choice": None}])
        self.client.force_authenticate(self.player)
        self.submit([{"question": first.id, "choice": self.right(first).id}])
        self.client.force_authenticate(None)

        rows = self.client.get("/api/leaderboard/").json()

        self.assertEqual([row["username"] for row in rows], ["player", "rival"])


class StaleRoundTests(PlayApiTestCase):
    def test_submit_with_replaced_choice_counts_as_skipped(self) -> None:
        self.client.force_authenticate(self.player)
        first, second, _ = self.questions
        stale_choice_id = self.right(first).id
        first.choices.all().delete()
        Choice.objects.create(question=first, text="Right 0", is_correct=True)
        Choice.objects.create(question=first, text="Wrong 0")

        response = self.submit(
            [{"question": first.id, "choice": stale_choice_id}, {"question": second.id, "choice": self.right(second).id}]
        )

        self.assertEqual(response.status_code, 201)
        answers = response.json()["answers"]
        self.assertEqual((answers[0]["is_correct"], answers[0]["chosen_text"]), (False, ""))
        self.assertEqual(response.json()["score"], 1)

    def test_question_without_correct_choice_does_not_crash_scoring(self) -> None:
        broken = make_question(self.curator, self.era, 50)
        broken.choices.filter(is_correct=True).update(is_correct=False)
        self.client.force_authenticate(self.player)

        response = self.submit([{"question": broken.id, "choice": broken.choices.first().id}])

        self.assertEqual(response.status_code, 201)
        self.assertEqual((response.json()["score"], response.json()["answers"][0]["correct_text"]), (0, ""))
