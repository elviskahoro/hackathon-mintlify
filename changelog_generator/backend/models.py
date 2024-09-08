import reflex as rx


class GithubPullRequest(
    rx.Model,
    table=True,
):  # type: ignore

    customer_name: str
    email: str
    age: int
    gender: str
    location: str
    job: str
    salary: int
