import logging
import time
from datetime import datetime
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


def parse_librus_time_string(time_string: str):
    # we expect time_string to be: YYYY-MM-DD HH:MM:SS (eg. >>2022-12-11 13:28:54<<)
    parsed_time = datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S')
    return parsed_time


def store_last_checked_message_time_sent_in_txt_file(message_time_sent: datetime,
                                                     last_checked_message_time_sent_filename: str):
    with open(last_checked_message_time_sent_filename, 'w', encoding='utf-8') as fp:
        fp.write(str(message_time_sent))


def read_last_checked_message_time_sent_from_txt_file(last_checked_message_time_sent_filename: str):
    try:
        with open(last_checked_message_time_sent_filename, 'r', encoding='utf-8') as fp:
            data_from_file = fp.read()

        # we expect time_string to be: YYYY-MM-DD HH:MM:SS (eg. >>2022-12-11 13:28:54<<)
        parsed_time = datetime.strptime(data_from_file, '%Y-%m-%d %H:%M:%S')
    except:
        parsed_time = None

    return parsed_time


class LibrusScraper(object):
    def __init__(self,
                 webdriver_path: str,
                 librus_base_url: str,
                 librus_username: str,
                 librus_password: str,
                 last_checked_message_sent_filename):
        self._driver = webdriver.Chrome(executable_path=webdriver_path)

        self._librus_base_url = librus_base_url
        self._librus_username = librus_username
        self._librus_password = librus_password

        self._last_checked_message_sent_filename = last_checked_message_sent_filename

        # set global wait time - we need reliability, not speed
        self._driver.implicitly_wait(5)  # in seconds

    def _login_to_librus(self):
        # open base url
        self._driver.get(self._librus_base_url)

        # accept cookies
        try:
            consent_button = self._driver.find_element(
                By.CSS_SELECTOR,
                '#consent-categories-description > div.modal-footer.justify-content-end > div > div > '
                'button.modal-button__primary'
            )
            consent_button.click()
        except NoSuchElementException as e:
            logger.error(f'No such element: consent button. || Exception: {e}')

        time.sleep(5)
        # find and navigate to login page
        try:
            login_site_button = self._driver.find_element(
                By.CSS_SELECTOR,
                'body > nav > div > div.navbar__right.navbar__right--small > div > a'
            )
            login_site_button.click()
        except NoSuchElementException as e:
            logger.error(f'No such element: login site button. || Exception: {e}')

        # login form is in the iframe - we have to switch the context
        self._driver.switch_to.frame(self._driver.find_elements(By.TAG_NAME, "iframe")[0])

        # login
        username = self._driver.find_element(By.XPATH, '//*[@id="Login"]')
        username.send_keys(self._librus_username)
        password = self._driver.find_element(By.XPATH, '//*[@id="Pass"]')
        password.send_keys(self._librus_password)
        login_button = self._driver.find_element(By.XPATH, '//*[@id="LoginBtn"]')
        login_button.click()

        # switch back to default frame
        self._driver.switch_to.default_content()

    def _close_notification_modal(self):
        # check it there is modal to close
        try:
            close_button = self._driver.find_element(
                By.NAME,
                'zapisz_zamknij'
            )
            close_button.click()

        except Exception:
            print('No modal.')

    def _navigate_to_messages(self):
        message_button = self._driver.find_element(
            By.XPATH,
            '//*[@id="icon-wiadomosci"]'
        )
        message_button.click()

    def _get_new_messages(self, last_checked_message_time_sent: Optional[datetime] = None):
        messages = []
        new_messages = []

        form_with_tables = self._driver.find_element(By.ID, 'formWiadomosci')
        # css selector .class1.class2 should match only elements with both classes
        table_with_messages = form_with_tables.find_element(By.CSS_SELECTOR, '.decorated.stretch')
        table_body = table_with_messages.find_element(By.TAG_NAME, 'tbody')
        rows = table_body.find_elements(By.TAG_NAME, 'tr')

        # collect and build all messages from page 1
        # there is very low probability, that any new messages will occur on subsequent pages
        # so - for now - do not check them
        for row in rows:
            # row structure: checkbox | attachment-icon | send_from | subject | time_sent | remove-icon
            # links to message are in send_from or topic cells
            row_cells = row.find_elements(By.TAG_NAME, 'td')
            message_sent_from = row_cells[2].text
            message_subject = row_cells[3].text
            message_time_sent = row_cells[4].text
            message_link = row_cells[3].find_element(By.TAG_NAME, 'a').get_attribute('href')
            # new and unread messages have style attribute (they are in bold)
            try:
                message_read_status = False if row_cells[2].get_attribute('style') else True
            except NoSuchElementException:
                message_read_status = True

            messages.append({'message_sent_from': message_sent_from,
                             'message_subject': message_subject,
                             'message_time_sent': parse_librus_time_string(message_time_sent),
                             'message_link': message_link,
                             'message_read_status': message_read_status})

        # collect only new messages, navigate inside and get message content
        # last_checked_message_time_sent is set to datetime of the latest collected message
        # or - on startup - current datetime minus 5 minutes
        last_checked_message_time_sent_from_file = read_last_checked_message_time_sent_from_txt_file(
            self._last_checked_message_sent_filename)
        # if there is txt file with datetime, overwrite initial on_start value
        if last_checked_message_time_sent_from_file:
            last_checked_message_time_sent = last_checked_message_time_sent_from_file

        logger.info(f'Last checked: {last_checked_message_time_sent}.')

        for message in messages:
            if message.get('message_time_sent') > last_checked_message_time_sent \
                    and not message.get('message_read_status'):
                self._driver.get(message.get('message_link'))
                message_content = self._driver.find_element(By.CSS_SELECTOR, '.container-message-content').text
                message['message_content'] = message_content
                new_messages.append(message)
                self._driver.back()

        # set new last_checked_message_time_sent
        last_checked_message_time_sent = messages[0].get('message_time_sent')
        store_last_checked_message_time_sent_in_txt_file(last_checked_message_time_sent,
                                                         self._last_checked_message_sent_filename)

        return new_messages

    def get_new_messages_from_librus(self, last_checked_message_time_sent: Optional[datetime] = None) -> list:
        logger.info('Checking, if there are new messages...')
        self._login_to_librus()
        logger.info('Logged in to LIBRUS.')
        self._close_notification_modal()
        self._navigate_to_messages()
        new_messages = self._get_new_messages(last_checked_message_time_sent)
        logger.info(f'{len(new_messages)} new message(s) found.')

        self._driver.close()

        return new_messages
