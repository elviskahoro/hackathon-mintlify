from __future__ import annotations

import os

import openai
import reflex as rx
from sqlmodel import or_, select

from .models import GithubPullRequest

CLIENT_OPEN_AI = None


def get_openai_client():
    global CLIENT_OPEN_AI
    if CLIENT_OPEN_AI is None:
        CLIENT_OPEN_AI = openai.OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
        )

    return CLIENT_OPEN_AI


class State(rx.State):
    """The app state."""

    current_pull_request: GithubPullRequest = GithubPullRequest()
    pull_requests: list[GithubPullRequest] = []
    release_tag_start: str = ""
    release_tag_end: str = ""
    repository_url: str = ""

    products: dict[str, str] = {}
    email_content_data: str = (
        "Click 'Generate Changelog' make an AI generated changelog."
    )
    gen_response = False
    tone: str = "😊 Formal"
    length: str = "1000"
    search_value: str = ""
    sort_value: str = ""
    sort_reverse: bool = False

    def set_repository_url(
        self,
        value: str,
    ) -> None:
        self.repository_url = value
        print(self.repository_url)

    def set_release_tag_start(
        self,
        value: str,
    ) -> None:
        self.release_tag_start = value
        print(self.release_tag_start)

    def set_release_tag_end(
        self,
        value: str,
    ) -> None:
        self.release_tag_end = value
        print(self.release_tag_end)

    def load_entries(self) -> list[GithubPullRequest]:
        """Get all users from the database."""
        with rx.session() as session:
            query = select(GithubPullRequest)
            if self.search_value:
                search_value = f"%{str(self.search_value).lower()}%"
                query = query.where(
                    or_(
                        *[
                            getattr(GithubPullRequest, field).ilike(search_value)
                            for field in GithubPullRequest.get_fields()
                        ],
                    ),
                )

            self.pull_requests = session.exec(query).all()

    def sort_values(
        self,
        sort_value: str,
    ) -> None:
        self.sort_value = sort_value
        self.load_entries()

    def toggle_sort(self) -> None:
        self.sort_reverse = not self.sort_reverse
        self.load_entries()

    def filter_values(
        self,
        search_value,
    ) -> None:
        self.search_value = search_value
        self.load_entries()

    def get_pull_request(
        self,
        pull_request: GithubPullRequest,
    ) -> None:
        self.current_pull_request = pull_request

    def delete_pull_request(
        self,
        id: int,
    ):
        """Delete a customer from the database."""
        with rx.session() as session:
            pull_request = session.exec(
                select(GithubPullRequest).where(GithubPullRequest.id == id),
            ).first()
            session.delete(pull_request)
            session.commit()

        self.load_entries()
        return rx.toast.info(
            f"User {pull_request.customer_name} has been deleted.",
            position="bottom-right",
        )

    @rx.background
    async def call_openai(self):
        session = get_openai_client().chat.completions.create(
            user=self.router.session.client_token,
            stream=True,
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a product marketer at a developer tool company. You have a list of pull requests within an open source project. Your task is to write a developer-friendly changelog based on the pull requests. The changelog should be {self.tone} and {self.length} characters long.",
                },
                {
                    "role": "user",
                    "content": f"Based on these {self.pull_requests} write a changelog draft to junior level developer",
                },
            ],
        )
        for item in session:
            if hasattr(item.choices[0].delta, "content"):
                response_text = item.choices[0].delta.content
                async with self:
                    if response_text is not None:
                        self.email_content_data += response_text

                yield

        async with self:
            self.gen_response = False

    def generate_email(self):
        self.gen_response = True
        self.email_content_data = ""
        return State.call_openai
