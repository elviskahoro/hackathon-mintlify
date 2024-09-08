import reflex as rx

from changelog_generator.backend.backend import GithubPullRequest, State
from changelog_generator.components.form_field import form_field
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
                _update_customer_dialog(pull_request),
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


def _update_customer_dialog(pull_request):
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.icon_button(
                rx.icon("square-pen", size=22),
                color_scheme="green",
                size="2",
                variant="solid",
                on_click=lambda: State.get_pull_request(pull_request),
            ),
        ),
        rx.dialog.content(
            rx.hstack(
                rx.badge(
                    rx.icon(tag="square-pen", size=34),
                    color_scheme="blue",
                    radius="full",
                    padding="0.65rem",
                ),
                rx.vstack(
                    rx.dialog.title(
                        "Edit Customer",
                        weight="bold",
                        margin="0",
                    ),
                    rx.dialog.description(
                        "Edit the customer's info",
                    ),
                    spacing="1",
                    height="100%",
                    align_items="start",
                ),
                height="100%",
                spacing="4",
                margin_bottom="1.5em",
                align_items="center",
                width="100%",
            ),
            rx.flex(
                rx.form.root(
                    rx.flex(
                        rx.hstack(
                            # Name
                            form_field(
                                "Name",
                                "Customer Name",
                                "text",
                                "customer_name",
                                "user",
                                pull_request.customer_name,
                            ),
                            # Location
                            form_field(
                                "Location",
                                "Customer Location",
                                "text",
                                "location",
                                "map-pinned",
                                pull_request.location,
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        rx.hstack(
                            # Email
                            form_field(
                                "Email",
                                "user@reflex.dev",
                                "email",
                                "email",
                                "mail",
                                pull_request.email,
                            ),
                            # Job
                            form_field(
                                "Job",
                                "Customer Job",
                                "text",
                                "job",
                                "briefcase",
                                pull_request.job,
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        # Gender
                        rx.vstack(
                            rx.hstack(
                                rx.icon("user-round", size=16, stroke_width=1.5),
                                rx.text("Gender"),
                                align="center",
                                spacing="2",
                            ),
                            rx.select(
                                ["Male", "Female", "Other"],
                                default_value=pull_request.gender,
                                name="gender",
                                direction="row",
                                as_child=True,
                                required=True,
                                width="100%",
                            ),
                            width="100%",
                        ),
                        rx.hstack(
                            # Age
                            form_field(
                                "Age",
                                "Customer Age",
                                "number",
                                "age",
                                "person-standing",
                                pull_request.age.to(str),
                            ),
                            # Salary
                            form_field(
                                "Salary",
                                "Customer Salary",
                                "number",
                                "salary",
                                "dollar-sign",
                                pull_request.salary.to(str),
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        direction="column",
                        spacing="3",
                    ),
                    rx.flex(
                        rx.dialog.close(
                            rx.button(
                                "Cancel",
                                variant="soft",
                                color_scheme="gray",
                            ),
                        ),
                        rx.form.submit(
                            rx.dialog.close(
                                rx.button("Update Customer"),
                            ),
                            as_child=True,
                        ),
                        padding_top="2em",
                        spacing="3",
                        mt="4",
                        justify="end",
                    ),
                    on_submit=State.update_customer_to_db,
                    reset_on_submit=False,
                ),
                width="100%",
                direction="column",
                spacing="4",
            ),
            max_width="450px",
            padding="1.5em",
            border=f"2px solid {rx.color('accent', 7)}",
            border_radius="25px",
        ),
    )


def main_table():
    return rx.fragment(
        rx.flex(
            rx.spacer(),
            rx.cond(
                State.sort_reverse,
                rx.icon(
                    "arrow-down-z-a",
                    size=28,
                    stroke_width=1.5,
                    cursor="pointer",
                    on_click=State.toggle_sort,
                ),
                rx.icon(
                    "arrow-down-a-z",
                    size=28,
                    stroke_width=1.5,
                    cursor="pointer",
                    on_click=State.toggle_sort,
                ),
            ),
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
            rx.input(
                rx.input.slot(rx.icon("search")),
                placeholder="Search here...",
                size="3",
                max_width="225px",
                width="100%",
                variant="surface",
                on_change=lambda value: State.filter_values(value),
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
