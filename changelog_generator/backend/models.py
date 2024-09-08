import reflex as rx


class GithubPullRequest(
    rx.Model,
    table=True,
):  # type: ignore

    title: str
    number: int
    body: str
    author: str
    merged_at: str
    url: str
