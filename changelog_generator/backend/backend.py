from __future__ import annotations

import os

import openai
import reflex as rx
from sqlmodel import or_, select
import requests
from datetime import datetime

# Replace with your GitHub Personal Access Token
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', 'your-github-token')
# GitHub API base URL
GITHUB_API_URL = 'https://api.github.com'



from .models import GithubPullRequest

_client = None

def fetch_user_orgs():
    """
    Fetches all organizations the authenticated user is part of.
    :return: List of organizations.
    """
    url = f"{GITHUB_API_URL}/user/orgs"
    headers = {
        'Authorization': f"Bearer {GITHUB_TOKEN}",
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_repos(owner):
    """
    Fetch all repositories for a given owner (organization or user).
    :param owner: GitHub organization or user
    :return: A list of repositories
    """
    url = f"{GITHUB_API_URL}/users/{owner}/repos"
    headers = {
        'Authorization': f"Bearer {GITHUB_TOKEN}",
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_pull_requests(owner, repo, state='open', per_page=5):
    """
    Fetch pull requests from a given repository.
    :param owner: Repository owner (GitHub username or organization)
    :param repo: Repository name
    :param state: The state of the pull requests ('open', 'closed', or 'all')
    :param per_page: Number of pull requests per page
    :return: A list of pull requests
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls"
    headers = {
        'Authorization': f"Bearer {GITHUB_TOKEN}",
        'Accept': 'application/vnd.github.v3+json'
    }
    params = {
        'state': state,
        'per_page': per_page
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise an exception for non-2xx responses
    return response.json()

def get_openai_client():
    global _client
    if _client is None:
        _client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    return _client



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
