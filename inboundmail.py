import logging
import webapp2

from google.appengine.ext.webapp.mail_handlers import InboundMailHandler


class LogSenderHandler(InboundMailHandler):
	def receive(self, mail_message):
		logging.info("Received a message from: " + mail_message.sender)
		logging.info('Subject: '+mail_message.subject)
		logging.info('To: '+mail_message.to)
		logging.info('Cc: '+mail_message.cc)

		plaintext_bodies = mail_message.bodies('text/plain')
		logging.info('Message in plain text: ')
		for content_type, body in plaintext_bodies:
			decoded_body = body.decode()
			logging.info(decoded_body)

		html_bodies = mail_message.bodies('text/html')
		logging.info('Message in HTML: ')
		for content_type, body in html_bodies:
			decoded_body = body.decode()
			logging.info(decoded_body)


app = webapp2.WSGIApplication([LogSenderHandler.mapping()], debug=True)

