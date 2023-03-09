import sys
import logging
import os
import time

from dotenv import load_dotenv

from librus_scraper.scraper import LibrusScraper
from librus_scraper.scraper import parse_librus_time_string
from notification_sender.mail_sender import MailNotificationSender


logger = logging.getLogger(__name__)

# set up logging
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fhandler = logging.FileHandler('librus_notification_handler.log', encoding='utf-8')
strhandler = logging.StreamHandler(sys.stdout)
fhandler.setFormatter(formatter)
strhandler.setFormatter(formatter)

logging.root.addHandler(strhandler)
logging.root.addHandler(fhandler)
logging.root.setLevel(level=logging.INFO)

# get environment from CLI
# if there is no environment provided, assume it is an empty string == local
try:
    ENV = sys.argv[1]
except IndexError:
    ENV = 'local'

# load environment variables based on CLI args
if ENV == 'production':
    dotenv_file = '.env.production'
else:
    dotenv_file = '.env.local'

load_dotenv(dotenv_file)

librus_base_url = os.getenv('LIBRUS_BASE_URL')
librus_username = os.getenv('LIBRUS_USERNAME')
librus_password = os.getenv('LIBRUS_PASSWORD')

mail_smtp_server_host = os.getenv('MAIL_SMTP_SERVER_HOST')
mail_smtp_server_port = os.getenv('MAIL_SMTP_SERVER_PORT')
mail_username = os.getenv('MAIL_USERNAME')
mail_password = os.getenv('MAIL_PASSWORD')

last_checked_message_time_sent_filename = os.getenv('LAST_CHECKED_MESSAGE_TIME_SENT_FILENAME')
message_check_interval = os.getenv('MESSAGE_CHECK_INTERVAL')

notification_recipient = os.getenv('NOTIFICATION_RECIPIENT')

logger.info(f'Starting main loop - will check for new messages every {message_check_interval} minutes...')
while True:
    scraper = LibrusScraper(r'C:\WebDriver\bin\chromedriver.exe',
                            librus_base_url,
                            librus_username,
                            librus_password,
                            last_checked_message_time_sent_filename)

    on_start_time = parse_librus_time_string('2023-03-07 13:09:54')
    scraped_new_messages = scraper.get_new_messages_from_librus(on_start_time)

    if scraped_new_messages:
        logger.info('Starting sending notifications...')
        mail_sender = MailNotificationSender(mail_username,
                                             mail_password,
                                             mail_smtp_server_host,
                                             mail_smtp_server_port)
        mail_sender.send_notifications(notification_recipient,
                                       scraped_new_messages)
        logger.info('Done.')

    time.sleep(60 * int(message_check_interval))
