import requests
import json
import logging
import sentry_sdk
import zipfile

from sentry_sdk.integrations.logging import LoggingIntegration

from billing.models import AstrologyBooking, WalletPlanUsage
from datetime import datetime, timezone, date, timedelta
from time import sleep

import pdfkit
from django.template.loader import get_template
from django.core.mail import EmailMessage
from users.utils import number_to_word

from astrologer.models import Astrologer
from billing.models import WalletTxn

options = {
    'page-size':'A4',
    'margin-top':'.4in',
    'margin-right':'.4in',
    'margin-bottom':'.4in',
    'margin-left':'.4in'
}

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.INFO
)

def trigger_call(agent, customer, talktime):
	try:
		url = "https://kpi.knowlarity.com/Basic/v1/account/call/makecall"
		payload = json.dumps({
                    "k_number": "+919513319029",
                		  "agent_number": f"{agent}",
                		  "customer_number": f"{customer}",
                		  "caller_id": "+918047225028",
                		  "additional_params": {
                                      "max_talktime": f"{talktime}"
                                  }
		})
		headers = {
                    'Authorization': 'f2f8716c-47d4-4c4a-8372-e5780ee54768',
                		  'x-api-key': '1yWupUw5p26qOU7Vc9Un85GoDw09X0mP8c4CYlW5',
                		  'Content-Type': 'application/json'
		}
		response = requests.request("POST", url, headers=headers, data=payload)
		if response.status_code == 200:
			logging.info(
				f'Booking triggered with success resp : ', response.text)
			print(f'Booking triggered with success resp : ', response.text)
			return 1
		else:
			debug_dict = {'agent':agent, 'customer':customer, 'talktime':talktime, 'response':response.text}
			logging.error('Invalid response received from Knowlarity.', extra=debug_dict)
			return 0
	except Exception as err:
		return 0

def online_enabler():
	try:
		astrologers = Astrologer.objects.all()
		for astrologer in astrologers:
			try:
				current_time = datetime.utcnow().replace(tzinfo=timezone.utc).time()
				if current_time < astrologer.availibility_start or current_time > astrologer.availibility_end:
					astrologer.online = False
				if current_time > astrologer.availibility_start and current_time < astrologer.availibility_end:
					astrologer.online = True
				astrologer.save()
			except Exception as err:
				logging.error(err)
	except Exception as err:
		logging.error(err)

def generate_invoice(data):
	try:
		print('generating...')
		gst_amnt = data.invoice.txn_amount + 18/100*data.invoice.txn_amount
		in_words = number_to_word(gst_amnt)
		today = datetime.now()
		d = {
			'item' : data,
			'words': in_words,
			'total': gst_amnt,
			'gst'  : 18/100*data.invoice.txn_amount,
			'today': today
			}
		temp = get_template('booking_invoice.html')
		html = temp.render(d)
		pdfkit.from_string(html,"{}.pdf".format(data.invoice.order_id), options = options)
	except Exception as err:
		logging.error(err)

def monthly_invoice_generator():
	try:
		# dt_string = input('type the month and year: ')
		# dt = datetime.strptime(dt_string, '%B %Y')
		zip_files = []
		dtime = date.today()
		first = dtime.replace(day=1)
		dt = first - timedelta(days=1)
		items = WalletTxn.objects.filter(updated_at__year = dt.year, updated_at__month = dt.month, description__startswith = 'Wallet Recharge')
		for data in items:
			try:
				print('generating...')
				in_words = number_to_word(data.txn_amount)
				due_date = data.updated_at
				title = data.description
				subtotal = data.txn_amount_sans_tax
				d = {
					'item'     : data,
					'words'    : in_words,
					'total'    : data.txn_amount,
					'gst'      : round(18/100*data.txn_amount_sans_tax,2),
					'due_date' : due_date, 
					'title'    : title, 
					'sub_total': subtotal, 
					}
				temp = get_template('wallettxn_invoice.html')
				html = temp.render(d)
				pdfkit.from_string(html,"{}.pdf".format(data.invoice.paygw_order), options = options)
				zip_files.append("{}.pdf".format(data.invoice.paygw_order))
			except Exception as err:
				logging.error(err)
		with zipfile.ZipFile('monthly_invoices_{}-{}.zip'.format(dt.month, dt.year),'w') as zipF:
			for file in zip_files:
				zipF.write(file, compress_type = zipfile.ZIP_DEFLATED)
		email = EmailMessage(
					'You Have Got the Invoices from Astrothought!',
					'Hi,<br>Please find the Wallet recharge invoices for month {}-{} in attachments.'.format(dt.month, dt.year),
					'AstroThought <noreply@astrothought.com>',
					['bhaskar@greybits.in','vipin@greybits.in'],
				)
		email.content_subtype = 'html'
		email.attach_file('monthly_invoices_{}-{}.zip'.format(dt.month, dt.year))
		email.send()
	except Exception as err:
		logging.error(err)

def trigger():
	try:
		requests.get("https://hc-ping.com/e61fd9ef-28ae-4576-b30d-4d10cf3f8261", timeout=4)
	except Exception as er:
		logging.error(er)
		pass
	online_enabler()
	ds = AstrologyBooking.objects.filter(invoice__success=True, completed=False)
	now = datetime.utcnow().replace(tzinfo=timezone.utc)
	for item in ds:
		try:
			diff = item.start_time-now
			if diff.seconds < 75:
				for i in range(4):
					user_phone = item.user.user.phone
					if len(user_phone)!=13:
						user_phone = f"+91{user_phone}"
						item.associate.user.phone
					associate_phone = item.associate.user.phone
					if len(associate_phone) != 13:
						associate_phone = f"+91{associate_phone}"
					logging.info(f'Booking triggered for {item.associate} with {user_phone} for {item.duration}')
					trigger = trigger_call(associate_phone,
					                       user_phone, item.duration*60)
					if trigger:
						generate_invoice(item)
						item.completed = True
						item.save()
						print("Booking trigger complete!")
						logging.info('Booking trigger complete!')
						break
		except Exception as err:
			logging.error(err)
			continue


sentry_sdk.init(
    dsn="https://18b46f1f7f114359bac107ae2c83d41f@o950260.ingest.sentry.io/6024265",
    traces_sample_rate=1.0,
   	integrations=[sentry_logging]
)

# while True:
# 	sleep(10)
# 	trigger()

# if __name__ == '__main__':
# 	ds = AstrologyBooking.objects.filter(invoice__success=True, completed=False)[0]
# 	generate_invoice(ds)
