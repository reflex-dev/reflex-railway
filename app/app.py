"""Guestbook: a small Reflex app backed by Postgres and Redis."""

import reflex as rx
import sqlalchemy as sa
import sqlmodel

from app.models import MAX_MESSAGE_LENGTH, MAX_NAME_LENGTH, Entry, engine

PAGE_SIZE = 50


class GuestbookState(rx.State):
    """Per-session state; Redis holds it so any backend worker can serve the session."""

    entries: list[Entry] = []

    @rx.event
    def load_entries(self):
        """Load the newest entries from the database."""
        with sqlmodel.Session(engine()) as session:
            self.entries = list(
                session.exec(
                    sqlmodel.select(Entry)
                    .order_by(sa.desc(Entry.created_at), sa.desc(Entry.id))
                    .limit(PAGE_SIZE)
                ).all()
            )

    @rx.event
    def sign(self, form_data: dict):
        """Validate and save a new entry.

        Args:
            form_data: The submitted form fields.

        Returns:
            A toast describing the result.
        """
        name = str(form_data.get("name", "")).strip()
        message = str(form_data.get("message", "")).strip()
        if not name or not message:
            return rx.toast.error("Add your name and a message.")
        if len(name) > MAX_NAME_LENGTH or len(message) > MAX_MESSAGE_LENGTH:
            return rx.toast.error("That entry is too long.")
        with sqlmodel.Session(engine()) as session:
            session.add(Entry(name=name, message=message))
            session.commit()
        self.load_entries()
        return rx.toast.success("Thanks for signing!")

    @rx.event
    def delete(self, entry_id: int):
        """Delete an entry.

        Args:
            entry_id: The id of the entry to delete.
        """
        with sqlmodel.Session(engine()) as session:
            if entry := session.get(Entry, entry_id):
                session.delete(entry)
                session.commit()
        self.load_entries()


def entry_card(entry: Entry) -> rx.Component:
    """Render one guestbook entry.

    Args:
        entry: The entry to render.

    Returns:
        The entry card.
    """
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.text(entry.name, weight="bold"),
                    rx.moment(entry.created_at, from_now=True, color_scheme="gray"),
                    align="baseline",
                    spacing="2",
                ),
                rx.text(entry.message, white_space="pre-wrap"),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.icon_button(
                rx.icon("trash-2", size=16),
                on_click=GuestbookState.delete(entry.id),
                variant="ghost",
                color_scheme="gray",
                aria_label="Delete entry",
            ),
            width="100%",
            align="start",
        ),
        width="100%",
    )


def sign_form() -> rx.Component:
    """Render the form for signing the guestbook.

    Returns:
        The form.
    """
    return rx.form(
        rx.vstack(
            rx.input(
                name="name",
                placeholder="Your name",
                max_length=MAX_NAME_LENGTH,
                required=True,
                width="100%",
            ),
            rx.text_area(
                name="message",
                placeholder="Leave a message",
                max_length=MAX_MESSAGE_LENGTH,
                required=True,
                width="100%",
            ),
            rx.button("Sign the guestbook", type="submit"),
            width="100%",
            align="end",
        ),
        on_submit=GuestbookState.sign,
        reset_on_submit=True,
        width="100%",
    )


def index() -> rx.Component:
    """Render the guestbook page.

    Returns:
        The page component.
    """
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("Reflex on Railway", size="8"),
            rx.text(
                "A Python web app with a static frontend, a Reflex backend, "
                "Postgres, and Redis, each running as its own Railway service.",
                color_scheme="gray",
            ),
            sign_form(),
            rx.cond(
                GuestbookState.entries,
                rx.vstack(
                    rx.foreach(GuestbookState.entries, entry_card),
                    width="100%",
                ),
                rx.text("No entries yet. Be the first!", color_scheme="gray"),
            ),
            spacing="5",
            padding_y="10vh",
        ),
        size="2",
    )


app = rx.App()
app.add_page(
    index,
    title="Reflex on Railway",
    description="A Reflex app deployed on Railway with Postgres and Redis.",
    on_load=GuestbookState.load_entries,
)
