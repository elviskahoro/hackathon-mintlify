from __future__ import annotations

import os

import openai
import reflex as rx

from github import Github
from sqlmodel import or_, select

from .models import GithubPullRequest

CLIENT_OPEN_AI = None
CLIENT_GITHUB = None


def get_github_client():
    global CLIENT_GITHUB
    if CLIENT_GITHUB is None:
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")

        CLIENT_GITHUB = Github(github_token)

    return CLIENT_GITHUB


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

    @rx.background
    async def fetch_pull_requests_between_tags(
        self,
    ) -> list[GithubPullRequest]:
        repo_url: str = self.repository_url
        start_tag: str = self.release_tag_start
        end_tag: str = self.release_tag_end
        client = get_github_client()
        repo = client.get_repo(repo_url)

        # Get the commit SHAs for the start and end tags
        start_commit = repo.get_git_ref(f"tags/{start_tag}").object.sha
        end_commit = repo.get_git_ref(f"tags/{end_tag}").object.sha

        # Get all pull requests between the two commits
        pulls = repo.get_pulls(state="closed", sort="created", direction="desc")

        pull_requests = []
        for pr in pulls:
            if pr.merge_commit_sha and (
                repo.compare(start_commit, pr.merge_commit_sha).ahead_by >= 0
                and repo.compare(pr.merge_commit_sha, end_commit).ahead_by >= 0
            ):
                pull_requests.append(
                    GithubPullRequest(
                        title=pr.title,
                        number=pr.number,
                        body=pr.body,
                        author=pr.user.login,
                        merged_at=pr.merged_at,
                        url=pr.html_url,
                    ),
                )

        self.pull_requests = pull_requests
        return pull_requests
