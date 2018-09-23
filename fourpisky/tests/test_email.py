from fourpisky.comms.email import send_email
from fourpisky.local import contacts
import pytest

@pytest.mark.skipif(contacts.sendgrid_api_key is None,
                   reason="No SendGrid API Key supplied")
def test_email_send():
    print("KEY", contacts.sendgrid_api_key)
    response = send_email(
        recipient_addresses=[c.email for c in contacts.error_contacts],
        subject="[TEST] Unit-testing email for fourpisky-core (again)",
        body_text="Astronomy alerts from the 4PiSky project\n"
                  "Another line of text"
        ,
    )
    assert response.status_code == 202