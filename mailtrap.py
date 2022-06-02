import smtplib

sender = "Private Person <from@example.com>"
receiver = "A Test User <to@example.com>"

message = f"""\
Subject: Howdy Partner
To: {receiver}
From: {sender}

This is a test e-mail message. just more testing"""

with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
    server.login("4a66b131d7db9f", "f5344258bc82a1")
    server.sendmail(sender, receiver, message)