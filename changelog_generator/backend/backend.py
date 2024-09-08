from __future__ import annotations

import os

import openai
import reflex as rx
from sqlmodel import asc, desc, func, or_, select

from .models import GithubPullRequest

products: dict[str, dict] = {
    "T-shirt": {
        "description": "A plain white t-shirt made of 100% cotton.",
        "price": 10.99,
    },
    "Jeans": {
        "description": "A pair of blue denim jeans with a straight leg fit.",
        "price": 24.99,
    },
    "Hoodie": {
        "description": "A black hoodie made of a cotton and polyester blend.",
        "price": 34.99,
    },
    "Cardigan": {
        "description": "A grey cardigan with a V-neck and long sleeves.",
        "price": 36.99,
    },
    "Joggers": {
        "description": "A pair of black joggers made of a cotton and polyester blend.",
        "price": 44.99,
    },
    "Dress": {"description": "A black dress made of 100% polyester.", "price": 49.99},
    "Jacket": {
        "description": "A navy blue jacket made of 100% cotton.",
        "price": 55.99,
    },
    "Skirt": {
        "description": "A brown skirt made of a cotton and polyester blend.",
        "price": 29.99,
    },
    "Shorts": {
        "description": "A pair of black shorts made of a cotton and polyester blend.",
        "price": 19.99,
    },
    "Sweater": {
        "description": "A white sweater with a crew neck and long sleeves.",
        "price": 39.99,
    },
}

_client = None


def get_openai_client():
    global _client
    if _client is None:
        _client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    return _client


class State(rx.State):
    """The app state."""

    current_pull_request: GithubPullRequest = GithubPullRequest()
    pull_requests: list[GithubPullRequest] = []
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

            if self.sort_value:
                sort_column = getattr(GithubPullRequest, self.sort_value)
                if self.sort_value == "salary":
                    order = desc(sort_column) if self.sort_reverse else asc(sort_column)

                else:
                    order = (
                        desc(func.lower(sort_column))
                        if self.sort_reverse
                        else asc(func.lower(sort_column))
                    )

                query = query.order_by(order)

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
                    "content": f"Based on these {products} write a sales email to {self.current_pull_request.customer_name} and email {self.current_pull_request.email} who is {self.current_pull_request.age} years old and a {self.current_pull_request.gender} gender. {self.current_pull_request.customer_name} lives in {self.current_pull_request.location} and works as a {self.current_pull_request.job} and earns {self.current_pull_request.salary} per year. Make sure the email recommends one product only and is personalized to {self.current_pull_request.customer_name}. The company is named Reflex its website is https://reflex.dev.",
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

    def generate_email(self, user: GithubPullRequest):
        self.current_pull_request = GithubPullRequest(**user)
        self.gen_response = True
        self.email_content_data = ""
        return State.call_openai
