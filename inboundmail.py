import logging
import webapp2

from models import AdminEmail

from google.appengine.api import mail
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler

def forwardEmail():
	message = mail.EmailMessage(
		sender='busybici <busybici@bikeshareapp.appspotmail.com>',
		subject='busybici update',
		to=to,
		body=body
	)
	message.send()

class LogSenderHandler(InboundMailHandler):
	def receive(self, mail_message):
		logging.info("Received a message from: " + mail_message.sender)
		original_sender = 'Original sender: '+mail_message.sender+'\n'

		logging.info('Subject: '+mail_message.subject)
		forward_subject = 'new message from busybici user: '+mail_message.subject

		logging.info('To: '+mail_message.to)
		original_to = 'Original to: '+mail_message.to+'\n'

		try:
			logging.info('Cc: '+mail_message.cc)
			original_cc = 'Original cc: '+mail_message.cc+'\n'
		except:
			original_cc=''

		forward_body_contents = []
		forward_body_contents.append(original_sender)
		forward_body_contents.append(original_to)
		forward_body_contents.append(original_cc)
		forward_body_contents.append('\n')

		forward_html_contents = []
		forward_html_contents.append(original_sender)
		forward_html_contents.append(original_to)
		forward_html_contents.append(original_cc)
		forward_html_contents.append('\n')

		for content_type, body in mail_message.bodies('text/plain'):
			decoded_body = body.decode()
			logging.info(decoded_body)
			forward_body_contents.append(decoded_body)

		for content_type, body in mail_message.bodies('text/html'):
			decoded_body = body.decode()
			logging.info(decoded_body)
			forward_html_contents.append(decoded_body)

		forward_body = ''.join(forward_body_contents)
		forward_html = ''.join(forward_html_contents)

		admin_entity = AdminEmail.query().get()
		forward_to = admin_entity.email

		message = mail.EmailMessage(
			sender='busybici carrier <carrier@bikeshareapp.appspotmail.com>',
			subject=forward_subject,
			to=forward_to,
			body=forward_body,
			html=forward_html,
			)
		message.send()


app = webapp2.WSGIApplication([LogSenderHandler.mapping()], debug=True)

