"""Run the demo."""

import asyncio
from contextlib import contextmanager
import os
from os import getenv
import sys
import time

from colorama import Style, Fore
import colorama

from . import Controller, logging_to_stdout
from .scenarios import connected


ISSUER = getenv("ISSUER", "http://localhost:3003")
VERIFIER = getenv("VERIFIER", "http://localhost:3005")
HOLDER = getenv("HOLDER", "http://localhost:3001")
LOG_LEVEL = getenv("LOG_LEVEL", "debug")


@contextmanager
def section(title: str):
    if sys.stdout.isatty():
        size = os.get_terminal_size()
        left = "=" * (int(size.columns / 2) - int((len(title) + 1) / 2))
        right = "=" * (size.columns - (len(left) + len(title) + 2))
        print(f"{Fore.BLUE}{Style.BRIGHT}{left} {title} {right}")
    else:
        print(title)
    yield


async def main():
    """Run steps."""
    colorama.init(autoreset=True)
    logging_to_stdout()

    issuer = Controller("issuer", ISSUER)
    holder = Controller("holder", HOLDER)

    with section("Establish Connection"):
        issuer_conn, holder_conn = await connected(issuer, holder)

    with section("Prepare for writing to the ledger"):
        await issuer.onboard()

    with section("Prepare credential ledger artifacts"):
        schema_id = await issuer.publish_schema(
            attributes=["firstname", "age"],
            schema_name="revocation_testing",
            schema_version="0.1.0",
        )
        cred_def_id = await issuer.publish_cred_def(schema_id, support_revocation=True)

    with section("Issue credential and request presentation"):
        async with issuer.listening(), holder.listening():
            issuer_cred_ex = await issuer_conn.issue_credential(
                cred_def_id=cred_def_id,
                firstname="Bob",
                age="42",
            )
            holder_cred_ex = await holder_conn.receive_cred_ex()
            await holder_cred_ex.send_request()
            await issuer_cred_ex.request_received()
            await holder_cred_ex.credential_received()
            await holder_cred_ex.store()
            await issuer_cred_ex.credential_acked()
            await holder_cred_ex.credential_acked()

        non_revoked_time = int(time.time())
        async with issuer.listening(), holder.listening():
            issuer_pres = await issuer_conn.request_presentation(
                comment="Before revocation (should verify true)",
                requested_attributes=[
                    {
                        "name": "firstname",
                        "restrictions": [{"cred_def_id": cred_def_id}],
                    }
                ],
                non_revoked={"from": non_revoked_time, "to": non_revoked_time},
            )
            holder_pres = await holder_conn.receive_pres_ex()
            relevant_creds = await holder_pres.fetch_relevant_credentials()
            pres_spec = await holder_pres.auto_prepare_presentation(relevant_creds)
            await holder_pres.send_presentation(pres_spec)

            await issuer_pres.presentation_received()
            await issuer_pres.verify_presentation()
            await issuer_pres.verified()
            await holder_pres.presentation_acked()

    with section("Revoke credential"):
        async with issuer.listening(), holder.listening():
            await issuer_cred_ex.revoke(publish=False, comment="revoked by demo")
            await issuer.publish_revocations()
            await holder_cred_ex.receive_revocation_notification()
            print("Waiting 10 seconds for revocation to propagate...")
            time.sleep(10)

    with section("Request proof from holder again after revoking"):
        before_revoking_time = non_revoked_time
        async with issuer.listening(), holder.listening():
            non_revoked_time = int(time.time())
            issuer_pres = await issuer_conn.request_presentation(
                comment="After revoking (should verify false)",
                requested_attributes=[
                    {
                        "name": "firstname",
                        "restrictions": [{"cred_def_id": cred_def_id}],
                    }
                ],
                non_revoked={"from": non_revoked_time - 1, "to": non_revoked_time},
            )
            holder_pres = await holder_conn.receive_pres_ex()
            relevant_creds = await holder_pres.fetch_relevant_credentials()
            pres_spec = await holder_pres.auto_prepare_presentation(relevant_creds)
            await holder_pres.send_presentation(pres_spec)

            await issuer_pres.presentation_received()
            await issuer_pres.verify_presentation()
            await issuer_pres.verified()
            await holder_pres.presentation_acked()

    with section(
        "Attempt another proof with non_revoked interval to before revocation"
    ):
        async with issuer.listening(), holder.listening():
            issuer_pres = await issuer_conn.request_presentation(
                comment="After revoking, interval before revocation (should verify true)",
                requested_attributes=[
                    {
                        "name": "firstname",
                        "restrictions": [{"cred_def_id": cred_def_id}],
                    }
                ],
                non_revoked={"from": before_revoking_time, "to": before_revoking_time},
            )
            holder_pres = await holder_conn.receive_pres_ex()
            relevant_creds = await holder_pres.fetch_relevant_credentials()
            pres_spec = await holder_pres.auto_prepare_presentation(relevant_creds)
            await holder_pres.send_presentation(pres_spec)

            await issuer_pres.presentation_received()
            await issuer_pres.verify_presentation()
            await issuer_pres.verified()
            await holder_pres.presentation_acked()

    with section("Attempt another proof with no non_revoked interval"):
        async with issuer.listening(), holder.listening():
            issuer_pres = await issuer_conn.request_presentation(
                comment="After revoking, no revocation interval (should verify true)",
                requested_attributes=[
                    {
                        "name": "firstname",
                        "restrictions": [{"cred_def_id": cred_def_id}],
                    }
                ],
            )
            holder_pres = await holder_conn.receive_pres_ex()
            relevant_creds = await holder_pres.fetch_relevant_credentials()
            pres_spec = await holder_pres.auto_prepare_presentation(relevant_creds)
            await holder_pres.send_presentation(pres_spec)

            await issuer_pres.presentation_received()
            await issuer_pres.verify_presentation()
            await issuer_pres.verified()
            await holder_pres.presentation_acked()

    with section(
        "Attempt another proof with non_revoked interval and local non_revoked override"
    ):
        non_revoked_time = int(time.time())
        async with issuer.listening(), holder.listening():
            issuer_pres = await issuer_conn.request_presentation(
                comment=(
                    "After revocation, non_revoked interval and local "
                    "non_revoked override (should verify true)"
                ),
                requested_attributes=[
                    {
                        "name": "firstname",
                        "restrictions": [{"cred_def_id": cred_def_id}],
                        "non_revoked": {
                            "from": before_revoking_time,
                            "to": before_revoking_time,
                        },
                    }
                ],
                non_revoked={"from": non_revoked_time, "to": non_revoked_time},
            )
            holder_pres = await holder_conn.receive_pres_ex()
            relevant_creds = await holder_pres.fetch_relevant_credentials()
            pres_spec = await holder_pres.auto_prepare_presentation(relevant_creds)
            await holder_pres.send_presentation(pres_spec)

            await issuer_pres.presentation_received()
            await issuer_pres.verify_presentation()
            await issuer_pres.verified()
            await holder_pres.presentation_acked()

    with section("Attempt another proof with only local non_revoked interval"):
        non_revoked_time = int(time.time())
        async with issuer.listening(), holder.listening():
            issuer_pres = await issuer_conn.request_presentation(
                comment=(
                    "After revocation, local non_revoked interval only "
                    "(should verify false)"
                ),
                requested_attributes=[
                    {
                        "name": "firstname",
                        "restrictions": [{"cred_def_id": cred_def_id}],
                        "non_revoked": {
                            "from": non_revoked_time,
                            "to": non_revoked_time,
                        },
                    }
                ],
            )
            holder_pres = await holder_conn.receive_pres_ex()
            relevant_creds = await holder_pres.fetch_relevant_credentials()
            pres_spec = await holder_pres.auto_prepare_presentation(relevant_creds)
            await holder_pres.send_presentation(pres_spec)

            await issuer_pres.presentation_received()
            await issuer_pres.verify_presentation()
            await issuer_pres.verified()
            await holder_pres.presentation_acked()

    with section("Query presentations"):
        presentations = await issuer_conn.get_pres_ex_records()

    with section("Presentation Summary"):
        for pres in presentations:
            print(pres.summary())


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
