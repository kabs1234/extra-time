"""Who may write quiz content, and who may see a question's correct answer."""

from django.contrib.auth.models import AnonymousUser, User
from django.db.models import Model
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from quiz.models import Question


def is_author_or_staff(user: User | AnonymousUser, question: Question) -> bool:
    return user.is_authenticated and (user.is_staff or question.author_id == user.id)


def can_see_answers(user: User | AnonymousUser, question: Question) -> bool:
    """Correct answers and explanations are only for the question's author and staff."""
    return is_author_or_staff(user, question)


class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.method in SAFE_METHODS or bool(request.user.is_authenticated and request.user.is_staff)


class IsAuthorOrStaffOrReadOnly(BasePermission):
    """Anyone reads; logged-in users create; only the author (``obj.author_id``) or staff edit."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request: Request, view: APIView, obj: Model) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff or obj.author_id == request.user.id
