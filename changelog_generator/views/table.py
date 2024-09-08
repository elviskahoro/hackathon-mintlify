import reflex as rx

from changelog_generator.backend.backend import GithubPullRequest, State
from changelog_generator.components.gender_badges import gender_badge


def _header_cell(text: str, icon: str):
    return rx.table.column_header_cell(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(text),
            align="center",
            spacing="2",
        ),
    )


def _show_pull_request(pull_request: GithubPullRequest):
    """Show a customer in a table row."""
    return rx.table.row(
        rx.table.row_header_cell(pull_request.customer_name),
        rx.table.cell(pull_request.email),
        rx.table.cell(pull_request.age),
        rx.table.cell(
            rx.match(
                pull_request.gender,
                ("Male", gender_badge("Male")),
                ("Female", gender_badge("Female")),
                ("Other", gender_badge("Other")),
                gender_badge("Other"),
            ),
        ),
        rx.table.cell(pull_request.location),
        rx.table.cell(pull_request.job),
        rx.table.cell(pull_request.salary),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    (State.current_pull_request.id == pull_request.id),
                    rx.button(
                        rx.icon("mail-plus", size=22),
                        rx.text("Generate Email", size="3"),
                        color_scheme="blue",
                        on_click=State.generate_email(pull_request),
                        loading=State.gen_response,
                    ),
                    rx.button(
                        rx.icon("mail-plus", size=22),
                        rx.text("Generate Email", size="3"),
                        color_scheme="blue",
                        on_click=State.generate_email(pull_request),
                        disabled=State.gen_response,
                    ),
                ),
                rx.icon_button(
                    rx.icon("trash-2", size=22),
                    on_click=lambda: State.delete_pull_request(pull_request.id),
                    size="2",
                    variant="solid",
                    color_scheme="red",
                ),
                min_width="max-content",
            ),
        ),
        style={"_hover": {"bg": rx.color("accent", 2)}},
        align="center",
    )


def main_table():
    return rx.fragment(
        rx.flex(
            rx.flex(
                rx.input(
                    placeholder="Repository url",
                    size="3",
                    max_width="225px",
                    width="100%",
                    variant="surface",
                    on_change=lambda value: State.set_repository_url(value),
                ),
                rx.input(
                    placeholder="Start tag",
                    size="3",
                    max_width="225px",
                    width="100%",
                    variant="surface",
                    on_change=lambda value: State.set_release_tag_start(value),
                ),
                rx.input(
                    placeholder="End tag",
                    size="3",
                    max_width="225px",
                    width="100%",
                    variant="surface",
                    on_change=lambda value: State.set_release_tag_end(value),
                ),
            ),
            rx.spacer(),
            rx.select(
                [
                    "customer_name",
                    "email",
                    "age",
                    "gender",
                    "location",
                    "job",
                    "salary",
                ],
                placeholder="Sort By: Name",
                size="3",
                on_change=lambda sort_value: State.sort_values(sort_value),
            ),
            justify="end",
            align="center",
            spacing="3",
            wrap="wrap",
            width="100%",
            padding_bottom="1em",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    _header_cell("Name", "square-user-round"),
                    _header_cell("Email", "mail"),
                    _header_cell("Age", "person-standing"),
                    _header_cell("Gender", "user-round"),
                    _header_cell("Location", "map-pinned"),
                    _header_cell("Job", "briefcase"),
                    _header_cell("Salary", "dollar-sign"),
                    _header_cell("Actions", "cog"),
                ),
            ),
            rx.table.body(
                rx.foreach(State.pull_requests, _show_pull_request),
            ),
            variant="surface",
            size="3",
            width="100%",
        ),
    )
