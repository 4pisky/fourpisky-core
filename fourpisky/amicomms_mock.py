email_address = 'ami-email-would-go-here'
default_requester = 'TestRequester'
request_email_subject = 'TestSubject'

def request_email(**kwargs):
    return "Dummy Email\n{}".format(kwargs)