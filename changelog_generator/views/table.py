import reflex as rx

from changelog_generator.backend.backend import GithubPullRequest, State


def _header_cell(
    text: str,
):
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(text),
            align="center",
            spacing="2",
        ),
    )


def _show_pull_request(
    pull_request: GithubPullRequest,
):
    """Show a customer in a table row."""
    return rx.table.row(
        rx.table.row_header_cell(pull_request.number),
        rx.table.cell(pull_request.author),
        rx.table.cell(pull_request.title),
        rx.table.cell(pull_request.merged_at),
        rx.table.cell(pull_request.url),
        rx.table.cell(
            rx.icon_button(
                rx.icon("trash-2", size=22),
                on_click=lambda: State.delete_pull_request(pull_request.id),
                size="2",
                variant="solid",
                color_scheme="red",
            ),
            min_width="max-content",
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
            ),
            rx.spacer(),
            rx.flex(
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
                    _header_cell("PR #"),
                    _header_cell("Author"),
                    _header_cell("Title"),
                    _header_cell("Merged at"),
                    _header_cell("URL"),
                    _header_cell("Actions"),
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
