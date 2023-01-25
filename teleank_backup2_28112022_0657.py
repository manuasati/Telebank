import os
import sys
import csv
import time
import shutil
import urllib
import warnings
import traceback
import pandas as pd
import datetime as dt
from calendar import calendar
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium. webdriver. common. keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, StaleElementReferenceException, NoSuchElementException, WebDriverException, ElementClickInterceptedException, TimeoutException

import utils
import config
from helpers.g_sheet_handler import GoogleSheetHandler

warnings.filterwarnings("ignore")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class DataScrapping():

    def __init__(
        self, browser, username, password, recent_transactions, dep_checks, multi_txns, check_date_diff, transaction_date_diff,
        start_date_transactions, start_date_checks, start_date_multi_txn, gdrive_folder_id, multi_txn_date_diff
    ):
        self.browser = browser
        self.username = username
        self.password = password
        self.user_login = False
        self.recent_transactions = recent_transactions
        self.dep_checks = dep_checks
        self.multi_txns = multi_txns
        self.start_date_transactions = start_date_transactions
        self.start_date_checks = start_date_checks
        self.start_date_multi_txn = start_date_multi_txn
        self.gdrive_folder_id = gdrive_folder_id
        self.check_date_diff = check_date_diff
        self.transaction_date_diff = transaction_date_diff
        self.multi_txn_date_diff = multi_txn_date_diff

        self.dep_checks_data = []
        self.recent_transactions_data = []
        self.multi_txns_data = []
        self.image_name = {}
        self.all_data_map = {'dep_checks_data': config.SHEET_CHECKS_TAB_NAME+'_'+self.username,
                             'recent_transactions_data': config.SHEET_DATA_TAB_NAME+'_'+self.username,
                             'Multi_txn_data': config.SHEET_MULTI_TXN_NAME+'_'+self.username}

    def login_to_site(self):
        print("\n\tStart user login..\n")
        try:
            self.browser.get(config.WEB_LINK)
            time.sleep(3)
            self.browser.find_element(By.ID, 'tzId').send_keys(self.username)
            self.browser.find_element(
                By.ID, 'tzPassword').send_keys(self.password)
            time.sleep(5)
            WebDriverWait(self.browser, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))).click()
            # self.browser.find_element(
            #     By.CSS_SELECTOR, 'button[type="submit"]').click()
            print('Clicked')
            self.user_login = True
            time.sleep(3)

            if self.browser.current_url == 'https://start.telebank.co.il/login/GENERAL_ERROR':
                print('\n\tRetrying... Login!\n')
                self.browser.delete_all_cookies()
                self.login_to_site()
            print('\n\tLogin successfull\n')
        except:
            print("\n\tLogin Failed !!\n")
            time.sleep(3)
            self.login_to_site()

    def create_directories(self):
        print(
            f'\n\n\t\t* * * * ** Creating Directory for Images & PDF for USER: {self.username} * * * * * * ')
        utils.create_dir(f'images_{self.username}')
        utils.create_dir('pdf')
        if os.path.isdir(f'csv_{self.username}'):
            print('\n\tCSV directory already exists!\n')
        else:
            os.makedirs(f'csv_{self.username}')

    def logout(self):
        time.sleep(5)
        try:
            self.browser.find_element(By.CSS_SELECTOR, '#logOutLink').click()
            self.user_login = False
            time.sleep(5)
            print('\n\tLogged out user(%s) successfully!\n' % self.username)
            return self.user_login
        except ElementNotInteractableException:
            print('ElementNotInteractableException Occured: [IGNORE]')
            pass
        except NoSuchElementException:
            print('NoSuchElementException Occured: [IGNORE]')
            pass
        except StaleElementReferenceException:
            print('StaleElementReferenceException Occured: [IGNORE]')
            pass
        except ElementClickInterceptedException:
            print('ElementClickInterceptedException Occured: [IGNORE]')
            pass

    def is_checks_left(self):
        if self.dep_checks.upper() == 'NO':
            print('\n\tSkipping Deposit Checks Data\n')
            return False
        date, sheet_df = utils.get_last_sheet_record_checks(self.username)
        print(f'\n\tDATE:{date}')
        print('\n\tGetting Deposit Checks Data....\n')
        time.sleep(3)
        self.browser.get(
            'https://start.telebank.co.il/apollo/business/#/CHKVEW')
        self.browser.refresh()
        time.sleep(7)
        if self.check_date_diff >= 360:
            WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable((By.ID, "dropdownMenu2"))).click()
            WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="checks-by-dates-4"]/a'))).click()
        else:
            self.filter_data_for_dep_checks()
            pass
        time.sleep(7)
        ''' Sorting Data rows in Ascending Order'''
        old_calendar = False
        try:
            self.browser.find_element(
                By.CSS_SELECTOR, '#main-content > div.moduleLoadedContent.ng-scope > feature-flag > div > flag-off-component > div > div > div > div:nth-child(2) > div:nth-child(1) > div.bg-white > div > div > section > table > thead > tr > th.mobile-first-cell.arrow-down').click()
            old_calendar = True
            time.sleep(2)
        except NoSuchElementException:
            pass
        flag = True
        MAX_RETRY = 2
        while MAX_RETRY > 0:
            try:
                try:
                    print("checking condition self.browser===")
                    self.browser.find_element(
                        By.CSS_SELECTOR, '#rc-table-td-CheckValueDate > div').click()
                    print("we didn't found page")
                    time.sleep(2)
                except NoSuchElementException or WebDriverException:
                    print("inside exception 1")
                    pass
                    
                    # self.browser.find_element(
                    #     By.CSS_SELECTOR, '#main-content > div.moduleLoadedContent.ng-scope > feature-flag > div > flag-off-component > div > div > div > div > div:nth-child(2) > div:nth-child(1) > div.bg-white > div > div > section > table > thead > tr > th.mobile-first-cell.arrow-down').click()
                except WebDriverException:
                    print("inside exception 2")
                    pass
                try:
                    print("now checking in inside try")
                    flag = self.is_old_check_calendar(date, sheet_df)
                    print("found flag inside inner try")
                    return flag
                except:
                    print("inside inner exception=====")
                    flag = self.is_new_check_calendar(date, sheet_df)
                    print("inside inner except after check===")
                    return flag

            except WebDriverException:
                print('Error')
                if not flag:
                    return False
                MAX_RETRY -= 1
                if MAX_RETRY == 0:
                    break
                print("\n\tCouldn't find the page [RETRYING]\n")
                self.browser.refresh()
                time.sleep(15)
                # self.is_checks_left()
                

            except Exception as err:
                print(f"Error in : {traceback.format_exc()}")
                print("\t\nNo table found between selected dates!\n")
                return False

    def is_new_check_calendar(self, date, sheet_df):
        print('new cal')
        try:
            data_rows = WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located(
                (By.XPATH, '/html/body/div[2]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-on-component/lobby-checks2/db-module-container/div[2]/div/div/div/div[2]/div[1]/div[2]/div/div/deposited-cash-table/section/ev-table/div/div/div[1]/div[2]/div/div')))
            row_count = 0
            print('data rows found!')
            if len(data_rows) == 0:
                return False
            for row in data_rows:
                row_data = row.text.split('\n')
                check_no = row_data[5]
                print(check_no)
                print("check_no not in sheet_df['5']", int(
                    check_no) not in sheet_df['5'].values)
                # print(sheet_df['5'].values)
                if int(check_no) not in sheet_df['5'].values:
                    row.click()
                    time.sleep(3)
                    front_image = self.browser.find_element(
                        By.XPATH, '/html/body/ngb-modal-window/div/div/expanded-view-horizontal-popup/section/div[3]/check-expand/div/div/div[1]/section[2]/div/div[1]/div/img').get_attribute('src')
                    WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                        (By.XPATH, '/html/body/ngb-modal-window/div/div/expanded-view-horizontal-popup/section/div[3]/check-expand/div/div/div[1]/section[2]/button'))).click()
                    time.sleep(2)
                    back_image = self.browser.find_element(
                        By.XPATH, '/html/body/ngb-modal-window/div/div/expanded-view-horizontal-popup/section/div[3]/check-expand/div/div/div[1]/section[2]/div/div[1]/div/img').get_attribute('src')
                    front_img_name = os.path.join(
                        ROOT_DIR, f'images_{self.username}', f'{check_no}_1.jpg')
                    urllib.request.urlretrieve(front_image, front_img_name)
                    back_img_name = os.path.join(
                        ROOT_DIR, f'images_{self.username}', f'{check_no}_2.jpg')
                    urllib.request.urlretrieve(back_image, back_img_name)
                    time.sleep(2)
                    self.browser.find_element(
                        By.CSS_SELECTOR, 'body > ngb-modal-window > div > div > expanded-view-horizontal-popup > section > button').click()
                    print('Front Image:', front_img_name)
                    print('Back Image:', back_img_name)
                    row_data.insert(9, front_img_name)
                    row_data.insert(10, back_img_name)
                    row_data.pop(0)
                    row_data.insert(
                        0, datetime.now().date().strftime('%d/%m/%Y'))
                    self.dep_checks_data.append(row_data)
                row_count += 1
            if row_count < len(data_rows):
                return True
            return False

        except WebDriverException:
            print(WebDriverException, 'Occured!')
            return True

    def is_old_check_calendar(self, date, sheet_df):
        total_records = 0
        try:
            print("Check")
            try:
                try:
                     data_rows = WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located(
                    (By.XPATH, '/html/body/div[2]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-on-component/lobby-checks/common-lobby-checks/db-module-container/div[2]/div/div/div/div[2]/div[1]/div[2]/div/div/deposited-cash-table/section/ev-table/div/div/div[1]/div[2]/div/div')))
                     print("Data Rows 1")
                except:
                     data_rows = WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located(
                                # /html/body/div[2]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[2]/div[1]/div[2]/div/div/section/table/tbody/tr[1]
                    (By.XPATH,'/html/body/div[1]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[2]/div[1]/div[2]/div/div/section/table/tbody/tr')))
                     print("Data Rows 2")
                    
            except:
                data_rows = WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located(
                    (By.XPATH, '//*[@id="main-content"]/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[2]/div[1]/div[2]/div/div/section/table/tbody/tr')))
                print("Data Rows 3")
                
            print("Check 2")
            total_records = len(data_rows)
            # print("total_records", total_records)
            if total_records == 0:
                return False
            print("total_records", total_records)
            # all_records_processed = False
            # while not all_records_processed:
            try:
                row_count = 0
                row_count = self.get_check_data(data_rows, sheet_df, row_count)
                if row_count < (total_records - 1):
                    raise Exception
            except Exception as err:
                print(err)
                self.get_check_data(data_rows, sheet_df, row_count+1)

        except WebDriverException:
            if len(self.dep_checks_data) > 0:
                if len(self.dep_checks_data) != total_records:
                    return True
                else:
                    return False
            print("\n\tCouldn't find the page [RETRYING]\n")
            self.browser.refresh()
            time.sleep(15)
            self.is_checks_left()
            
        except Exception as err:
            print('Error Occured:', err)
            
    def get_check_data(self, data_rows, sheet_df, row_count):
        try:
            print("start for loop")
            print('Starting for row count:', row_count)
            for idx,row in enumerate(data_rows):
                print("inside loop")
                idx = row_count
                print('idx:', idx)
                # print("Data Row",data_rows)
                print(len(data_rows))
                print("Rows ",row.text)
                # row_data = row.text.split()
                row_data = data_rows[idx].text.split()
                del row_data[:7]
                print(row_data)
                if not row_data and idx < (len(data_rows) - 1):
                    print("ROW data not found trying again using xpath")
                    row = WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located(
                    (By.XPATH, f'//*[@id="main-content"]/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[2]/div[1]/div[2]/div/div/section/table/tbody/tr[{idx}]')))
                    print('---------\n', row, '\n--------------')
                    # print("row",row[0].get_attribute("textContent").split())
                    # row_data = row[0]/
                    row = row.get_attribute("textContent").split()
                    del row_data[:7]
                    print(row_data)
                    
                if row_data:
                    check_no = row_data[4]
                else:
                    break
                print(check_no)
                print("check_no not in sheet_df['5']", int(
                    check_no) not in sheet_df['5'].values)
                # print(sheet_df['5'].values)
                if int(check_no) not in sheet_df['5'].values:
                    row.click()
                    time.sleep(3)
                    try:
                        front_image = self.browser.find_element(
                            By.XPATH, '/html/body/div[*]/div/div/div/div[*]/div[2]/section[2]/div/div/img').get_attribute('src')
                    except:
                        front_image = self.browser.find_element(
                            By.XPATH, '/html/body/ngb-modal-window/div/div/expanded-view-horizontal-popup/section/div[3]/check-expand/div/div/div[1]/section[2]/div/div[1]/div/img').get_attribute('src')
                    try:
                        try:                                #
                            WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                                (By.XPATH, '/html/body/div[*]/div/div/div/div[3]/div[2]/section[2]/button'))).click()
                        except:
                            WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                                (By.XPATH, '/html/body/div[*]/div/div/div/div[2]/div[2]/section[2]/button'))).click()
                    except:
                        WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                            (By.XPATH, '/html/body/ngb-modal-window/div/div/expanded-view-horizontal-popup/section/div[3]/check-expand/div/div/div[1]/section[2]/button'))).click()
                    time.sleep(2)
                    try:
                        back_image = self.browser.find_element(
                            By.XPATH, '/html/body/div[*]/div/div/div/div[*]/div[2]/section[2]/div/div/img').get_attribute('src')
                    except:
                        back_image = self.browser.find_element(
                            By.XPATH, '/html/body/ngb-modal-window/div/div/expanded-view-horizontal-popup/section/div[3]/check-expand/div/div/div[1]/section[2]/div/div[1]/div/img').get_attribute('src')
                    front_img_name = os.path.join(
                        ROOT_DIR, f'images_{self.username}', f'{check_no}_1.jpg')
                    urllib.request.urlretrieve(front_image, front_img_name)
                    back_img_name = os.path.join(
                        ROOT_DIR, f'images_{self.username}', f'{check_no}_2.jpg')
                    urllib.request.urlretrieve(back_image, back_img_name)
                    time.sleep(2)
                    try:
                        self.browser.find_element(
                            By.XPATH, '/html/body/div[*]/div/div/div/button').click()
                    except:
                        self.browser.find_element(
                            By.XPATH, '/html/body/ngb-modal-window/div/div/expanded-view-horizontal-popup/section/button').click()
                    print('Front Image:', front_img_name)
                    print('Back Image:', back_img_name)
                    row_data.insert(8, front_img_name)
                    row_data.insert(9, back_img_name)
                    row_data.insert(
                        0, datetime.now().date().strftime('%d/%m/%Y'))
                    self.dep_checks_data.append(row_data)
                row_count += 1
            # if row_count == len(data_rows):
            #     all_records_processed = True
            return row_count
        except Exception as err:
            print("loop failed due to :", err)
            return row_count

    def get_check_image(self, data):
        front_img_li = []
        back_img_li = []
        row = 0
        MAX_RETRY = 2
        while MAX_RETRY > 0:
            try:
                data_records = self.browser.find_elements(
                    By.XPATH, '//*[@id="main-content"]/div[2]/feature-flag/div/flag-off-component/div/div/div/div[2]/div[1]/div[2]/div/div/section/table/tbody/tr')
                print(f'\n\tTotal records: {len(data_records)}\n')
                for row_idx in range(len(data_records)):
                    time.sleep(3)
                    tr = WebDriverWait(self.browser, 20).until(EC.visibility_of_all_elements_located(
                        (By.XPATH, f'//*[@id="main-content"]/div[2]/feature-flag/div/flag-off-component/div/div/div/div[2]/div[1]/div[2]/div/div/section/table/tbody/tr[{row_idx+1}]')))
                    for data in tr:
                        data_row = data.text.split(' ')
                    if not data_row:
                        front_img_li.append('Failed to Load')
                        back_img_li.append('Failed to Load')
                        print(
                            '\n\tProcessing Data for Check No: Failed to Load Row Data')
                        print('Front Image:', front_img_li[-1])
                        print('Back Image:', back_img_li[-1])
                        continue
                    check_number = data_row[10]
                    print('\n\tProcessing Data for Check No: ', check_number)
                    print(data_row)
                    WebDriverWait(self.browser, 15).until(EC.element_to_be_clickable(
                        (By.XPATH, f'//*[@id="main-content"]/div[2]/feature-flag/div/flag-off-component/div/div/div/div[2]/div[1]/div[2]/div/div/section/table/tbody/tr[{row_idx+1}]'))).click()
                    time.sleep(3)
                    front_image = self.browser.find_element(
                        By.CSS_SELECTOR, 'body > div.modal.discountBiz-modal-general.cs-spa-sme-content.topbar-modal.checksExpand.fade.ng-scope.ng-isolate-scope.ng-animate.ng-enter.ng-enter-active.in > div > div > div > div.containerOsh.container-fluid > div.contentOsh.row > section.col-sm-6.col-print-9 > div > div > img').get_attribute('src')
                    WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, 'body > div.modal.discountBiz-modal-general.cs-spa-sme-content.topbar-modal.checksExpand.fade.ng-scope.ng-isolate-scope.ng-animate.ng-enter.ng-enter-active.in > div > div > div > div.containerOsh.container-fluid > div.contentOsh.row > section.col-sm-6.col-print-9 > button > img'))).click()
                    time.sleep(2)
                    back_image = self.browser.find_element(
                        By.CSS_SELECTOR, 'body > div.modal.discountBiz-modal-general.cs-spa-sme-content.topbar-modal.checksExpand.fade.ng-scope.ng-isolate-scope.ng-animate.ng-enter.ng-enter-active.in > div > div > div > div.containerOsh.container-fluid > div.contentOsh.row > section.col-sm-6.col-print-9 > div > div > img').get_attribute('src')
                    front_img_name = os.path.join(
                        ROOT_DIR, f'images_{self.username}', f'{check_number.replace("/", "-")}_1.jpg')
                    urllib.request.urlretrieve(front_image, front_img_name)
                    front_img_li.append(front_img_name)
                    back_img_name = os.path.join(
                        ROOT_DIR, f'images_{self.username}', f'{check_number.replace("/", "-")}_2.jpg')
                    urllib.request.urlretrieve(back_image, back_img_name)
                    back_img_li.append(back_img_name)
                    time.sleep(2)
                    self.browser.find_element(
                        By.CSS_SELECTOR, 'button[type="button"]').click()
                    row += 1
                    print('Front Image:', front_img_li[-1])
                    print('Back Image:', back_img_li[-1])
                return front_img_li, back_img_li, row
            except WebDriverException:
                MAX_RETRY -= 1
                if MAX_RETRY == 0:
                    break
                print("\n\tCouldn't find the page [RETRYING]\n")
                self.browser.refresh()
                time.sleep(15)
                self.get_check_image(data)

    def get_reference_index(self, ref, data):
        print('\n\tGetting last Saved Index\n')
        count = 0
        print('ref:', ref)
        try:
            old_calendar = True
            while True:
                if data == 'Checks':
                    refs = self.browser.find_element(
                        By.XPATH, f'//*[@id="main-content"]/div[2]/feature-flag/div/flag-off-component/div/div/div/div[2]/div[1]/div[2]/div/div/section/table/tbody/tr[{count+1}]/td[3]')
                if data == 'Transactions':
                    if not old_calendar:
                        refs = self.browser.find_element(
                            By.ID, f'rc-table-row-{count}')
                        print(refs.text.split('\n')[3])
                    else:
                        try:
                            refs = self.browser.find_element(
                                By.XPATH, f'//*[@id="lastTransactionTable-cell-{count}-3"]')
                            print('ref :', refs.text)
                        except NoSuchElementException:
                            old_calendar = False
                            print('old CAlenedar False')
                            continue
                    if old_calendar:
                        if refs.text.replace(' ', '').split('/')[0].isnumeric() and int(refs.text.split('/')[0].split()[0]) == ref:
                            break
                    else:
                        if refs.text.split('\n')[3].split('/')[0].split()[0].isnumeric() and int(refs.text.split('\n')[3].split('/')[0].split()[0]) == ref:
                            break
                count += 1
        except NoSuchElementException or WebDriverException as err:
            print(f"{err} Occured!")
            count = 0
        return count+1, old_calendar

    def is_txns_left(self):
        if self.recent_transactions.upper() == 'NO':
            print('\n\tSkipping Transactions Data\n')
            return False
        date, refs_from_g_drive = utils.get_last_sheet_record_txns(
            self.username)
        print("date:", date)
        print("refs_from_g_drive:", refs_from_g_drive)

        print('\n\tGetting Image Data from Recent Transactions\n')
        time.sleep(2)
        self.browser.execute_script("document.body.style.zoom='80%'")
        self.browser.get(
            'https://start.telebank.co.il/apollo/business/#/OSH_LENTRIES_ALTAMIRA')
        self.browser.refresh()
        time.sleep(6)
        self.browser.implicitly_wait(20)

        if self.transaction_date_diff >= 360:
            WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.ID, "input-osh-transaction"))).click()
            WebDriverWait(self.browser, 20).until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="lobby-osh-filter-item-7"]/a'))).click()
        else:
            self.filter_data_for_recent_transactions(
                self.start_date_transactions)
        time.sleep(7)
        self.browser.implicitly_wait(20)
        last_row_idx = 0
        old_calendar = True
        if refs_from_g_drive and refs_from_g_drive[0] != 0:
            last_row_idx, old_calendar = self.get_reference_index(
                refs_from_g_drive[-1], 'Transactions')
        else:
            refs_from_g_drive = [0]
            try:
                refs = self.browser.find_element(
                    By.XPATH, f'//*[@id="lastTransactionTable-cell-2-3"]')
                print('element found!')
            except NoSuchElementException:
                old_calendar = False

        if last_row_idx == 0 and date and refs_from_g_drive[0] != 0:
            print('using special case!')
            filter_date = WebDriverWait(self.browser, 8).until(EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="lastTransactionTable-cell-0-1"]/div/ng-include/div'))).text
            filter_date = utils.str_to_date(filter_date)
            date_diff = abs((date - filter_date.date()).days)
            print('date:', date)
            print('filter_date:', filter_date.date())
            if date_diff > 1:
                print('using timedelta')
                date = date - timedelta(days=18-date_diff)
                self.filter_data_for_recent_transactions(date)
                time.sleep(5)
                last_row_idx, old_calendar = self.get_reference_index(
                    refs_from_g_drive[-1], 'Transactions')

        print('Last saved Index:', last_row_idx)
        print('Please Wait! Skipping to the Last Saved Index......')
        try:
            print('\n\t Getting Data\n')
            time.sleep(5)
            idx = 0
            while True:
                try:
                    data_records = self.browser.find_elements(
                        By.CSS_SELECTOR, '.rc-table-row-content')
                except:
                    data_records = WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located(
                        (By.XPATH, '/html/body/div[2]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-on-component/lobby-osh2/db-module-container/div[2]/div/div/div[1]/div/div/last-transactions/div/div/ev-table/div/div/div[1]/div[2]/div/div')))
                if len(data_records) > 0:
                    break
            print('Total Records:', len(data_records))
            while idx < len(data_records):
                for data_row in data_records:
                    if idx < last_row_idx:
                        idx += 1
                        continue
                    if (not data_row) or (not data_row.text.strip()):
                        print(
                            f'ids:{idx} - data_row not found hance trying again to cover missing one!')
                        self.search_for_date_range_again()
                        break

                    row_date, row_ref = data_row.text.split(
                        '\n')[0], data_row.text.split('\n')[3]
                    row_ref = row_ref.split('/')[0].split()[0]
                    if int(row_ref) == 0:
                        row_ref = data_row.text.split(
                            '\n')[3].split('/')[0].split()[1]

                    check_no = utils.get_check_no(data_row.text.split()[3])
                    data_row_text = data_row.text
                    print("\n\tProcess row data: ref:", row_ref)
                    print('SCRAP DATA:\n', data_row.text.split('\n'))
                    if int(row_ref) not in refs_from_g_drive or int(row_ref) > int(refs_from_g_drive[-1]):
                        if old_calendar:
                            WebDriverWait(self.browser, 8).until(EC.element_to_be_clickable(
                                (By.ID, f"lastTransactionTable-row-{idx}"))).click()
                        else:
                            WebDriverWait(self.browser, 8).until(
                                EC.element_to_be_clickable((By.ID, f'rc-table-row-{idx}'))).click()
                        self.browser.implicitly_wait(10)
                        self.unique_reference = row_ref
                        if old_calendar:
                            img_element = utils.verify_element(
                                browser=self.browser, by_selector=By.XPATH, path='.//*[@id="single-check-view-con"]/div/div[1]/img[1]')
                        else:
                            img_element = utils.verify_element(
                                browser=self.browser, by_selector=By.XPATH, path='//*[@id="single-check-view-con"]/div/div[1]/img')
                        time.sleep(3)
                        new_pdf_name = ''
                        try:
                            max_retry = 0
                            while max_retry < 2:
                                print('"שיק" in row_text:',
                                      "שיק" in data_row_text)
                                print('sum > 1 & "העברה" not in row_text:', float(data_row_text.split(
                                    '\n')[4].replace(',', '')) > 1 and "העברה" not in data_row_text)
                                # if 'tools7.png' in self.browser.find_element(By.XPATH, '//*[@id="expanded-view-popup"]/div[4]/div[1]/div/div/div/ul/li[2]/a/span[1]/img').get_attribute('src'):
                                if "שיק" in data_row_text or (float(data_row_text.split('\n')[4].replace(',', '')) > 1 and "העברה" not in data_row_text):
                                    try:
                                        try:
                                            self.browser.find_element(
                                                By.CSS_SELECTOR, '#iban-popup > section > section.ip-actions > extra-actions-button2 > button.SAVE.icon.ip-button.ng-star-inserted').click()
                                        except:
                                            self.browser.find_element(
                                                By.XPATH, '//*[@id="expanded-view-popup"]/div[4]/div[1]/div/div/div/ul/li[2]/a').click()
                                    except:
                                        self.browser.find_element(
                                            By.XPATH, '//*[@id="iban-popup"]/section/section[3]/extra-actions-button2/button[2]').click()

                                    print('\tPDF Downloading')
                                    time.sleep(15)
                                    self.browser.implicitly_wait(17)
                                    pdfs = os.listdir(os.path.join(
                                        ROOT_DIR, 'pdf', 'tmp', ''))
                                    pdf_ref = row_ref.split('/')[0]
                                    new_pdf_name = f'{pdf_ref}_{self.username}_{check_no}.pdf'
                                    if len(pdfs) == 0:
                                        print(
                                            "\tPDF not downloaded properly. Retrying")
                                        time.sleep(5)
                                        max_retry += 1
                                        if max_retry == 2:
                                            print(
                                                '\tPDF Download has failed After two trys!')
                                            break
                                    else:
                                        print("\tPDF Downloaded Successfully")
                                        print('\tPDF Name:', pdfs[0])
                                        if os.path.exists(os.path.join(ROOT_DIR, 'pdf', 'tmp', f'{pdfs[0]}')) and 'pdf' in pdfs[0]:
                                            utils.rename_file(os.path.join(
                                                ROOT_DIR, 'pdf', 'tmp', ''), pdfs[0], new_pdf_name)  # Renaming pdf file
                                            shutil.move(os.path.join(
                                                ROOT_DIR, 'pdf', 'tmp', '')+new_pdf_name, os.path.join(ROOT_DIR, 'pdf', ''))
                                            # Storing the PDF file in Archives Folder
                                            if not os.path.exists(os.path.join(ROOT_DIR, 'Archives', 'pdfs')):
                                                os.makedirs(os.path.join(
                                                    ROOT_DIR, 'Archives', 'pdfs', ''))

                                            if not os.path.exists(os.path.join(ROOT_DIR, 'Archives', 'pdfs', f'{new_pdf_name}')):
                                                shutil.copy(os.path.join(
                                                    ROOT_DIR, 'pdf', '')+new_pdf_name, os.path.join(ROOT_DIR, 'Archives', 'pdfs', ''))
                                                break
                                            else:
                                                print(
                                                    "\tPDF File already exists in Archive")
                                                break
                                        else:
                                            print(
                                                "\tCould Not Find PDF in the tmp folder or the file may be of different extension..")
                                            break
                                else:
                                    break

                        except NoSuchElementException or WebDriverException:
                            print('\t No PDF Found!')
                            pass

                        '''Checking for technical issues'''
                        # technical_issue = self.check_tehnical_issue(idx)
                        technical_issue = ''

                        if img_element and "שיק" in data_row_text:
                            print('\tImg found!')
                            self.get_image_table_data(data_row_text.split(
                                '\n'), check_no, new_pdf_name, old_calendar)
                        else:
                            if 'הפקדת 0' in data_row_text and not technical_issue:
                                print('\tImg found!')
                                self.get_multiple_txns_checks_data(
                                    data_row_text.split('\n'), new_pdf_name)
                            else:
                                if not technical_issue:
                                    print("\t No Img Found!")
                                    self.get_no_image_table_data(
                                        data_row_text.split('\n'), new_pdf_name)

                        try:
                            if old_calendar:
                                self.browser.find_element(
                                    By.CSS_SELECTOR, 'button[type="button"]').click()
                                time.sleep(1.5)
                            else:
                                self.browser.find_element(
                                    By.XPATH, '/html/body/ngb-modal-window/div/div/expanded-view-popup/general-popup/div/div/div[1]/button').click()
                                time.sleep(1.5)
                        except ElementNotInteractableException or StaleElementReferenceException:
                            print('Not Interactable Image: [IGNORE]')
                            pass
                        idx += 1

                    else:
                        print(f'Data Already Exists!')
                        idx += 1
                        if idx+1 == len(data_records):
                            break
                        continue
            if old_calendar:
                flag = utils.verify_element(
                    browser=browser, by_selector=By.XPATH, path=f'//*[@id="lastTransactionTable-cell-{idx}-0"]')
            else:
                flag = utils.verify_element(
                    browser=browser, by_selector=By.ID, path=f'rc-table-row-{idx}')

        except WebDriverException:
            if old_calendar:
                flag = utils.verify_element(
                    browser=browser, by_selector=By.XPATH, path=f'//*[@id="lastTransactionTable-cell-{idx}-0"]')
            else:
                flag = utils.verify_element(
                    browser=browser, by_selector=By.ID, path=f'rc-table-row-{idx}')
            print(f"\t\n Error Occured Due to: {WebDriverException} ")
            print("\t\n\n ** ** ** ** ** Uploading the extracted imgs & pdf to gdrive and Pushing data to sheet till now  ** ** ** **")

        return flag

    def check_tehnical_issue(self, idx):
        retry = 2
        while retry > 0:
            technical_issue = utils.verify_element(browser=self.browser, by_selector=By.XPATH,
                                                   path='//*[@id="expanded-view-popup"]/div[4]/div[2]/div[2]/div/div[2]/section/div[3]/rc-global-error/div/div/h2/div')
            if technical_issue:
                print('Image not Found! Due to some Technical Issues...')
                self.browser.find_element(
                    By.CSS_SELECTOR, 'button[type="button"]').click()
                print('Retrying After 10 Seconds')
                retry -= 1
                print(f'Retry Left: {retry}')
                time.sleep(10)
                WebDriverWait(self.browser, 8).until(EC.element_to_be_clickable(
                    (By.ID, f"lastTransactionTable-row-{idx}"))).click()
                img_element = utils.verify_element(
                    browser=self.browser, by_selector=By.XPATH, path='.//*[@id="single-check-view-con"]/div/div[1]/img[1]')
                if img_element:
                    break
                if retry == 0:
                    print('\n\tSkipping this Record')
            else:
                break
        return technical_issue

    def download_image(self, check_no, old_calendar):
        print('downloading images')
        try:
            front_image = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="single-check-view-con"]/div/div[2]/img[1]'))
            ).get_attribute('src')
            back_image = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="single-check-view-con"]/div/div[2]/img[2]'))
            ).get_attribute('src')
        except:
            try:
                front_image = WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="single-check-view-con"]/div/div[1]/img[1]'))
                ).get_attribute('src')
                back_image = WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="single-check-view-con"]/div/div[1]/img[2]'))
                ).get_attribute('src')
            except:
                front_image = WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="single-check-view-con"]/div/div[1]/img'))
                ).get_attribute('src')
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="single-check-view-con"]/div/div[3]/rc-tooltip2/span/span/span/button'))).click()
                back_image = WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="single-check-view-con"]/div/div[1]/img'))
                ).get_attribute('src')
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="single-check-view-con"]/div/div[3]/rc-tooltip2/span/span/span/button'))).click()
        front_img_name = os.path.join(
            ROOT_DIR, f'images_{self.username}', f'{self.unique_reference.replace("/", "-")}_{self.username}_{check_no}_1.jpg')
        urllib.request.urlretrieve(front_image, front_img_name)
        # Creating Archives Folder for the user
        if not os.path.exists(os.path.join(ROOT_DIR, 'Archives', 'Images', f'images_{self.username}')):
            os.makedirs(os.path.join(ROOT_DIR, 'Archives',
                        'Images', f'images_{self.username}', ''))

        # Retriving and Storing the Front Image in Archive
        if not os.path.exists(os.path.join(ROOT_DIR, 'Archives', 'Images', f'images_{self.username}', f'{front_img_name}')):
            shutil.copy(front_img_name, os.path.join(
                ROOT_DIR, 'Archives', 'Images', f'images_{self.username}'))
            print("\tStored Front Image in Archive")
        else:
            print("\tFront Image Already Exists in Archive")

        back_img_name = os.path.join(
            ROOT_DIR, f'images_{self.username}', f'{self.unique_reference.replace("/", "-")}_{self.username}_{check_no}_2.jpg')
        urllib.request.urlretrieve(back_image, back_img_name)

        # Retriving and Storing the Back Image in Archive
        if not os.path.exists(os.path.join(ROOT_DIR, 'Archives', 'Images', f'images_{self.username}', f'{back_img_name}')):
            shutil.copy(back_img_name, os.path.join(
                ROOT_DIR, 'Archives', 'Images', f'images_{self.username}'))
            print("\tStored Back Images in Archive")
        else:
            print("\tBack Image Already Exists in Archive")

        return front_img_name, back_img_name

    def get_image_table_data(self, data_row, check_no, pdf_name, old_calendar):
        time.sleep(5)
        self.browser.implicitly_wait(10)
        if old_calendar:
            channel_name = self.browser.find_element(
                By.XPATH, '//*[@id="expanded-view-popup"]/div[4]/div[2]/div[2]/div/div[1]/div/ng-include/div/div[2]/span[2]/span[2]').text
        else:
            channel_name = WebDriverWait(self.browser, 5).until(EC.presence_of_element_located(
                (By.XPATH, '/html/body/ngb-modal-window/div/div/expanded-view-popup/general-popup/div/div/div[2]/section/osh-popups-title/osh-popups-titles-checks/div/osh-popups-titles-general/div/h2/span[5]'))).text
        self.browser.implicitly_wait(10)
        bank_number = self.browser.find_element(
            By.XPATH, '//*[@id="single-check-view-con"]/table/tbody/tr[1]/td[2]').text
        self.browser.implicitly_wait(10)
        branch_number = self.browser.find_element(
            By.XPATH, '//*[@id="single-check-view-con"]/table/tbody/tr[2]/td[2]').text
        account_number = self.browser.find_element(
            By.XPATH, '//*[@id="single-check-view-con"]/table/tbody/tr[3]/td[2]').text
        check_number = self.browser.find_element(
            By.XPATH, '//*[@id="single-check-view-con"]/table/tbody/tr[4]/td[2]').text
        sum = self.browser.find_element(
            By.XPATH, '//*[@id="single-check-view-con"]/table/tbody/tr[5]/td[2]').text
        front_img_name, back_img_name = self.download_image(
            check_no, old_calendar)
        self.image_name[self.unique_reference] = [
            front_img_name, back_img_name, pdf_name]
        self.recent_transactions_data.append([datetime.now().strftime("%d/%m/%Y")] + data_row + [
                                             channel_name] + [bank_number, branch_number, account_number, check_number, sum] + ["", "", ""])
        print('PROCESSED DATA:\n', self.recent_transactions_data[-1])
        print("\n")

    def get_multiple_txns_checks_data(self, data_row, pdf_name):
        channel_name = self.browser.find_element(
            By.XPATH, '//*[@id="expanded-view-popup"]/div[4]/div[2]/div[2]/div/div[1]/div/ng-include/div/div[2]/span[2]/span[2]').text
        no_of_checks = self.browser.find_element(
            By.XPATH, '//*[@id="expanded-view-popup"]/div[4]/div[2]/div[2]/div/div[2]/section/div[1]/div/div/div/div/div/div/div[1]/div/div/span[1]/span[2]').text
        print(no_of_checks)
        try:
            for i in range(int(no_of_checks)):
                if i >= 3:
                    ele = WebDriverWait(self.browser, 5).until(EC.presence_of_element_located(
                        (By.XPATH, f'//*[@id="checksTableScroll-cell-{i}-3"]')))
                    self.browser.execute_script(
                        "arguments[0].scrollIntoView()", ele)

                element = WebDriverWait(self.browser, 5).until(EC.presence_of_element_located(
                    (By.XPATH, f'//*[@id="checksTableScroll-cell-{i}-3"]')))
                element.click()
                self.browser.execute_script(
                    "arguments[0].scrollIntoView()", element)
                time.sleep(2)
                branch_no = WebDriverWait(self.browser, 5).until(EC.presence_of_element_located(
                    (By.XPATH, f'//*[@id="rc-table-row-{i}"]/ng-include/ng-include/div/div[2]/div[1]/div[1]/span[2]'))).text
                account_no = WebDriverWait(self.browser, 5).until(EC.presence_of_element_located(
                    (By.XPATH, f'//*[@id="rc-table-row-{i}"]/ng-include/ng-include/div/div[2]/div[1]/div[2]/span[2]'))).text
                check_no = WebDriverWait(self.browser, 5).until(EC.presence_of_element_located(
                    (By.XPATH, f'//*[@id="checksTableScroll-cell-{i}-0"]/div/ng-include/div'))).text
                sum = WebDriverWait(self.browser, 5).until(EC.presence_of_element_located(
                    (By.XPATH, f'//*[@id="checksTableScroll-cell-{i}-2"]/div/ng-include/div/span'))).text
                bank_no = WebDriverWait(self.browser, 5).until(EC.presence_of_element_located(
                    (By.XPATH, f'//*[@id="checksTableScroll-cell-{i}-1"]/div/ng-include/div'))).text
                all_details = [bank_no, branch_no, account_no, check_no, sum]
                print('[bank_no, branch_no, account_no, check_no, sum]')
                print(all_details)
                self.browser.find_element(
                    By.XPATH, f'//*[@id="rc-table-row-{i}"]/ng-include/ng-include/div/div[2]/div[2]/div/button').click()
                front_img_name, back_img_name = self.download_multiple_txn_check_img(
                    check_no)
                self.image_name[self.unique_reference +
                                f'_{i}'] = [front_img_name, back_img_name, pdf_name]
                print(self.image_name[self.unique_reference+f'_{i}'])
                self.recent_transactions_data.append([datetime.now().strftime(
                    "%d/%m/%Y")] + data_row + [channel_name] + all_details + ["", "", ""])
                print('PROCESSED DATA:\n', self.recent_transactions_data[-1])
                print("\n")
                self.browser.find_element(
                    By.XPATH, f'//*[@id="expanded-view-popup"]/div[4]/div[2]/div[2]/div/div[2]/section/div[1]/div/div/div/div/div/div/div[2]/div[1]/a').click()

        except WebDriverException:
            print('Skipping this record! Due to Technical Issues.')

    def is_multi_txns_left(self):
        if self.multi_txns.upper() == 'NO':
            print('Skipping yearly multiple check txns data..')
            return False, self.start_date_multi_txn
        date, refs_from_g_drive = utils.get_last_sheet_record_multiple_check_txns(
            self.username)
        print('\n\tGetting Multiple Check Txns Data from Recent Transactions\n')
        self.browser.get(
            'https://start.telebank.co.il/apollo/business/#/OSH_LENTRIES_ALTAMIRA')
        self.browser.refresh()
        time.sleep(6)
        self.browser.implicitly_wait(20)

        if self.start_date_multi_txn != date:
            date = self.start_date_multi_txn

        if date:
            try:
                multi_txn_date_diff = (datetime.now().date() - date).days
            except:
                multi_txn_date_diff = (datetime.now() - date).days

        print('\n\t date:', date)
        if not date or multi_txn_date_diff >= 350:
            WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.ID, "input-osh-transaction"))).click()
            WebDriverWait(self.browser, 20).until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="lobby-osh-filter-item-7"]/a'))).click()
        else:
            self.filter_data_for_recent_transactions(date)

        time.sleep(7)
        self.browser.implicitly_wait(20)

        data_records = self.browser.find_elements(
            By.CSS_SELECTOR, '.rc-table-row-content')
        idx = 0
        new_date = ''
        try:
            while idx < len(data_records):
                for data_row in data_records:

                    row_date, row_ref = data_row.text.split(
                        '\n')[0], data_row.text.split('\n')[3]
                    row_ref = row_ref.split('/')[0]
                    check_no = utils.get_check_no(data_row.text.split()[3])
                    data_row_text = data_row.text
                    print("\n\tProcess row data: ref:", row_ref, '\tidx:', idx)
                    print('SCRAP DATA:\n', data_row.text.split('\n'))
                    new_date = data_row_text.split('\n')[0]
                    print("'הפקדת 0' in data_row_text:",
                          'הפקדת 0' in data_row_text)
                    self.browser.implicitly_wait(10)
                    if 'הפקדת 0' in data_row_text and (row_ref not in refs_from_g_drive):
                        WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(
                            (By.ID, f"lastTransactionTable-row-{idx}"))).click()
                        self.browser.implicitly_wait(10)
                        self.unique_reference = row_ref
                        img_element = utils.verify_element(
                            browser=self.browser, by_selector=By.XPATH, path='.//*[@id="single-check-view-con"]/div/div[1]/img[1]')
                        time.sleep(3)
                        new_pdf_name = ''
                        try:
                            max_retry = 0
                            while max_retry < 2:
                                self.browser.find_element(
                                    By.XPATH, '//*[@id="expanded-view-popup"]/div[4]/div[1]/div/div/div/ul/li[2]/a').click()
                                print('\tPDF Downloading')
                                time.sleep(15)
                                self.browser.implicitly_wait(17)
                                pdfs = os.listdir(os.path.join(
                                    ROOT_DIR, 'pdf', 'tmp', ''))
                                pdf_ref = row_ref.split('/')[0]
                                new_pdf_name = f'{pdf_ref}_{self.username}_{check_no}.pdf'
                                if len(pdfs) == 0:
                                    print(
                                        "\tPDF not downloaded properly. Retrying")
                                    time.sleep(5)
                                    max_retry += 1
                                    if max_retry == 2:
                                        print(
                                            '\tPDF Download has failed After two trys!')
                                        break
                                else:
                                    print("\tPDF Downloaded Successfully")

                                    if os.path.exists(os.path.join(ROOT_DIR, 'pdf', 'tmp', f'{pdfs[0]}')):
                                        utils.rename_file(os.path.join(
                                            ROOT_DIR, 'pdf', 'tmp', ''), pdfs[0], new_pdf_name)  # Renaming pdf file
                                        shutil.move(os.path.join(
                                            ROOT_DIR, 'pdf', 'tmp', '')+new_pdf_name, os.path.join(ROOT_DIR, 'pdf', ''))
                                        # Storing the PDF file in Archives Folder
                                        if not os.path.exists(os.path.join(ROOT_DIR, 'Archives', 'pdfs')):
                                            os.makedirs(os.path.join(
                                                ROOT_DIR, 'Archives', 'pdfs', ''))

                                        if not os.path.exists(os.path.join(ROOT_DIR, 'Archives', 'pdfs', f'{new_pdf_name}')):
                                            shutil.copy(os.path.join(
                                                ROOT_DIR, 'pdf', '')+new_pdf_name, os.path.join(ROOT_DIR, 'Archives', 'pdfs', ''))
                                            break
                                        else:
                                            print(
                                                "\tPDF File already exists in Archive")
                                            break
                                    else:
                                        print(
                                            "\tCould Not Find PDF in the tmp folder")
                                        break

                        except NoSuchElementException or WebDriverException:
                            print('\t No PDF Found!')
                            pass

                        '''Checking for technical issues'''

                        self.get_multiple_txns_checks_data(
                            data_row_text.split('\n'), new_pdf_name)

                        try:
                            self.browser.find_element(
                                By.CSS_SELECTOR, 'button[type="button"]').click()
                            time.sleep(1.5)
                        except ElementNotInteractableException or StaleElementReferenceException:
                            print('Not Interactable Image: [IGNORE]')
                            pass
                        idx += 1

                    else:
                        self.browser.find_element(
                            By.XPATH, f'//*[@id="lastTransactionTable-cell-{idx}-6"]/div/ng-include/div').click()
                        print(f'Data Already Exists!')
                        idx += 1
                        if idx+1 == len(data_records):
                            break
                        continue

            flag = utils.verify_element(
                browser=browser, by_selector=By.XPATH, path=f'//*[@id="lastTransactionTable-cell-{idx}-0"]')
            if new_date:
                new_date = utils.str_to_date(new_date)

        except WebDriverException:
            flag = utils.verify_element(
                browser=browser, by_selector=By.XPATH, path=f'//*[@id="lastTransactionTable-cell-{idx}-0"]')
            if new_date:
                new_date = utils.str_to_date(new_date)
            print(f"\t\n Error Occured Due to: {WebDriverException} ")
            print("\t\n\n ** ** ** ** ** Uploading the extracted imgs & pdf to gdrive and Pushing data to sheet till now  ** ** ** **")

        return flag, new_date

    def download_multiple_txn_check_img(self, check_no):
        front_image = WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="expanded-view-popup"]/div[4]/div[2]/div[2]/div/div[2]/section/div[1]/div/div/div/div/div/div/div[2]/div[2]/div[1]/img'))
        ).get_attribute('src')
        front_img_name = os.path.join(
            ROOT_DIR, f'images_{self.username}', f'{self.unique_reference.replace("/", "-")}_{self.username}_{check_no}_1.jpg')
        urllib.request.urlretrieve(front_image, front_img_name)
        # Creating Archives Folder for the user
        if not os.path.exists(os.path.join(ROOT_DIR, 'Archives', 'Images', f'images_{self.username}')):
            os.makedirs(os.path.join(ROOT_DIR, 'Archives',
                        'Images', f'images_{self.username}', ''))

        # Retriving and Storing the Front Image in Archive
        if not os.path.exists(os.path.join(ROOT_DIR, 'Archives', 'Images', f'images_{self.username}', f'{front_img_name}')):
            shutil.copy(front_img_name, os.path.join(
                ROOT_DIR, 'Archives', 'Images', f'images_{self.username}'))
            print("\tStored Front Image in Archive")
        else:
            print("\tFront Image Already Exists in Archive")

        back_image = WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="expanded-view-popup"]/div[4]/div[2]/div[2]/div/div[2]/section/div[1]/div/div/div/div/div/div/div[2]/div[2]/div[2]/img'))
        ).get_attribute('src')
        back_img_name = os.path.join(
            ROOT_DIR, f'images_{self.username}', f'{self.unique_reference.replace("/", "-")}_{self.username}_{check_no}_2.jpg')
        urllib.request.urlretrieve(back_image, back_img_name)

        # Retriving and Storing the Back Image in Archive
        if not os.path.exists(os.path.join(ROOT_DIR, 'Archives', 'Images', f'images_{self.username}', f'{back_img_name}')):
            shutil.copy(back_img_name, os.path.join(
                ROOT_DIR, 'Archives', 'Images', f'images_{self.username}'))
            print("\tStored Back Images in Archive")
        else:
            print("\tBack Image Already Exists in Archive")

        print('front_img_name:', front_img_name)
        print('back_img_name:', back_img_name)

        if not (front_img_name or back_img_name):
            front_img_name, back_img_name = '', ''
        return front_img_name, back_img_name

    def get_no_image_table_data(self, data_row, pdf_name):
        self.image_name[self.unique_reference] = ['', '', pdf_name]

        MAX_RETRY = 2
        while MAX_RETRY > 0:
            try:
                comment = ''
                try:
                    channel_name = self.browser.find_element(
                        By.XPATH, '//*[@id="expanded-view-popup"]/div[4]/div[2]/div[2]/div/div[1]/div/div[2]/span[2]/span[2]').text
                except NoSuchElementException:
                    channel_name = ''

                try:
                    all_details = utils.get_check_table_df(
                        self.browser.page_source, 'מספר בנק מחויב')
                    comment = self.browser.find_element(
                        By.XPATH, '//*[@id="expanded-view-popup"]/div[4]/div[2]/div[2]/div/div[2]/section/div[1]/div/div/div/div/span').text
                except NoSuchElementException:
                    all_details = utils.get_check_table_df(
                        self.browser.page_source, 'מספר בנק מחויב')
                self.recent_transactions_data.append([datetime.now().strftime("%d/%m/%Y")] + data_row + [
                                                     channel_name] + all_details.iloc[:3][1].values.tolist() + ["", ""] + all_details.iloc[4:][1].values.tolist() + [comment])
                print("\t[img not found!]\n")
                print('PROCESSED DATA:\n', self.recent_transactions_data[-1])
                break
            except WebDriverException:
                MAX_RETRY -= 1
                if MAX_RETRY == 0:
                    break
                print("\n\tCouldn't find the page [retrying]\n")
                self.browser().refresh()
                self.get_no_image_table_data(data_row)

    def search_for_date_range_again(self):
        print("\n\tSearch and send request for_date_range_again...\n")
        WebDriverWait(self.browser, 20).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#advanced-search-window-btn > button"))).click()
        time.sleep(3)
        WebDriverWait(self.browser, 20).until(EC.element_to_be_clickable(
            (By.XPATH, '/html/body/div[2]/main/section/div[4]/div[3]/div/div/div[2]/div/div[2]/div[1]/div/div[1]/advanced-search/div/div[2]/form/div[2]/button'))).click()
        time.sleep(3)

    def filter_data_for_recent_transactions(self, txn_date):
        try:
            print("\n\n\t\t* * * * * * * * * * * * * Using Date Filter for Recent Transanctions * * * * * * * * * * * * *")
            WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#advanced-search-window-btn > button"))).click()
            WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="fromDate"]'))).click()
            old_calendar = True
            try:
                from_month, from_year = self.browser.find_element(
                    By.XPATH, '/html/body/div[2]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div[2]/div[1]/div/div[1]/advanced-search/div/div[2]/form/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/ul/li/div/div/div/table/thead/tr[1]/th[2]').text.split()
            except NoSuchElementException:
                try:
                    from_year = WebDriverWait(self.browser, 5).until(EC.visibility_of_element_located(
                        (By.XPATH, "/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[1]/bs-datepicker-navigation-view/button[3]/span"))).text
                    from_month = WebDriverWait(self.browser, 5).until(EC.visibility_of_element_located(
                        (By.XPATH, "/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[1]/bs-datepicker-navigation-view/button[2]/span"))).text
                    old_calendar = False
                except TimeoutException:
                    from_month, from_year = self.browser.find_element(
                        By.XPATH, '/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div[2]/div[1]/div/div[1]/advanced-search/div/div[2]/form/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/ul/li/div/div/div/table/thead/tr[1]/th[2]').text.split()

            calendar_month_year = utils.get_calendar_selected_date(
                from_month, from_year)

            if calendar_month_year:
                diff_in_year = (calendar_month_year.year - txn_date.year) * 12
                diff_in_from_month = calendar_month_year.month - txn_date.month + diff_in_year
                print('\tCALENDER MONTH OF YEAR:', from_month)
                print('\n\tDIFFERENCE IN MONTHS:', diff_in_from_month)
                self.select_transaction_date_from_calendar(
                    diff_in_from_month, txn_date, old_calendar)
                time.sleep(4)
            else:
                print("Error::: from_month is not found!!")
                print("TODO: need to handle this case!!")

            print("hitting submit button......")

            try:
                WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(
                    (By.XPATH, '/html/body/div[2]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div[2]/div[1]/div/div[1]/advanced-search/div/div[2]/form/div[2]/button'))).click()
            except TimeoutException or WebDriverException:
                try:
                    WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(
                        (By.XPATH, '//*[@id="oshTransferAdvanced"]/div[2]/form/div[2]/button'))).click()
                except TimeoutException or WebDriverException:
                    WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(
                        (By.XPATH, '/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div[2]/div[1]/div/div[1]/advanced-search/div/div[2]/form/div[2]/button'))).click()
            time.sleep(5)
            return old_calendar


        except WebDriverException:
            print(WebDriverException, 'Error occurred!\nRetrying!!')
            self.browser.refresh()
            time.sleep(15)
            self.filter_data_for_recent_transactions(txn_date)
            

    def filter_data_for_dep_checks(self):
        calendar_failed = False
        try:
            print("\n\n\t\t* * * * * * * * * * * * * Using Date Filter for Deposit Checks * * * * * * * * * * * * *")
            time.sleep(2)
            WebDriverWait(self.browser, 20).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#osh-checks-advanced-search-window-btn"))).click()
            time.sleep(2)
            WebDriverWait(self.browser, 20).until(EC.element_to_be_clickable(
                (By.XPATH, "//*[@id='oshChecksAdvancedSearchFromDate']"))).click()
            old_calendar = True

            if calendar_failed:
                input(
                    '\n\n\t""Please Enter the Date Manually and click on the submit button, after that hit Enter Key!!""\n')

            if not calendar_failed:
                try:
                    from_month, from_year = WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located(
                        (By.XPATH, "/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/thead/tr[1]/th[2]"))).text.split()
                except:
                    try:
                        from_year = WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located(
                            (By.XPATH, "/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[1]/bs-datepicker-navigation-view/button[3]/span"))).text
                        from_month = WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located(
                            (By.XPATH, "/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[1]/bs-datepicker-navigation-view/button[2]/span"))).text
                        old_calendar = False
                    except TimeoutException:
                        from_month, from_year = WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located(
                            (By.XPATH, "/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/thead/tr[1]/th[2]"))).text.split()

                calendar_month_year = utils.get_calendar_selected_date(
                    from_month, from_year)
                print('calendar_month_year:', calendar_month_year)
                if calendar_month_year:
                    diff_in_year = (calendar_month_year.year -
                                    self.start_date_checks.year) * 12
                    diff_in_from_month = calendar_month_year.month - \
                        self.start_date_checks.month + diff_in_year
                    print('\tCALENDER MONTH OF YEAR:', from_month)
                    print('\n\tDIFFERENCE IN MONTHS:', diff_in_from_month)
                    self.select_check_date_from_calendar(
                        diff_in_from_month, self.start_date_checks, old_calendar)
                    time.sleep(4)
                else:
                    print("Error::: from_month is not found!!")
                    print("TODO: need to handle this case!!")

                print("hitting submit button......")
                try:
                    try:
                        WebDriverWait(self.browser, 8).until(EC.element_to_be_clickable(
                            (By.XPATH, '//*[@id="main-content"]/div[2]/feature-flag/div/flag-on-component/lobby-checks/common-lobby-checks/db-module-container/div[2]/div/div/div/div[1]/div[2]/checks-advanced-search/section/section/div[3]/button'))).click()
                    except:
                        WebDriverWait(self.browser, 8).until(EC.element_to_be_clickable(
                            (By.XPATH, '//*[@id="main-content"]/div[2]/feature-flag/div/flag-on-component/lobby-checks2/db-module-container/div[2]/div/div/div/div[1]/div[2]/checks-advanced-search/section/section/div[3]/button'))).click()
                except:
                    WebDriverWait(self.browser, 8).until(EC.element_to_be_clickable(
                        (By.XPATH, '//*[@id="main-content"]/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[1]/div[2]/section/section/div[3]/button'))).click()

        except WebDriverException:
            print(WebDriverException, 'Error Occured!\nRetrying!!')
            calendar_failed = True
            self.browser.refresh()
            time.sleep(15)
            self.filter_data_for_dep_checks()

    def select_check_date_from_calendar(self, diff, sheet_date, old_calendar):
        print("sheet_date-> date:", sheet_date.day)
        try:
            try:
                date_row = self.browser.find_elements(
                    
                    By.XPATH, '//*[@id="main-content"]/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/tbody/tr')
                # //*[@id="main-content"]/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/tbody/tr[1]
                if len(date_row) == 0:
                    raise Exception
                print('Old Calendar')
            except:
                date_row = self.browser.find_elements(
                            #    /html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[2]/table/tbody/tr[2]
                    By.XPATH, "/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[2]/table/tbody/tr")
                print('New Calendar')
        except NoSuchElementException or WebDriverException:
            date_row = self.browser.find_elements(
                By.XPATH, "/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/tbody/tr")
            print('old calendar2')
        print(len(date_row))
        for _ in range(abs(diff)):
            time.sleep(4)
            if diff < 0:
                try:
                    WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                        (By.XPATH, f"/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/thead/tr[1]/th[3]"))).click()
                except TimeoutException:
                    try:
                        WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                            (By.XPATH, f"/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[1]/bs-datepicker-navigation-view/button[4]"))).click()
                    except TimeoutException:
                        WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                            (By.XPATH, f"/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/thead/tr[1]/th[3]"))).click()
            else:
                try:
                    WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                        (By.XPATH, f"/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/thead/tr[1]/th[1]"))).click()
                except TimeoutException:
                    try:
                        WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                            (By.XPATH, f"/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[1]/bs-datepicker-navigation-view/button[1]"))).click()
                    except TimeoutException:
                        WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                            (By.XPATH, f"/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/thead/tr[1]/th[1]"))).click()

        try:
            for ridx, rows in enumerate(date_row):
                # try:
                try:
                    rows = rows.text.split()
                except:
                    try:
                        dates = self.browser.find_elements(
                            By.XPATH, f"/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[2]/table/tbody/tr[{ridx+1}]/td")
                    except:
                        dates = self.browser.find_elements(
                            By.XPATH, f"/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/tbody/tr[{ridx+1}]/td[1]")

                    rows = dates
                print('rows:', rows)
                print('len(rows):', len(rows))

                # except NoSuchElementException:
                if ridx == 0 and sheet_date.day > 7:
                    continue

                for cidx, td in enumerate(rows):
                    print(td)
                    try:
                        if int(td.text) == sheet_date.day:
                            time.sleep(4)
                            try:
                                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                                                # /html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[2]/table/tbody/tr[2]/td[1]/span
                                    (By.XPATH, f"/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[2]/table/tbody/tr[{ridx+1}]/td[{cidx+1}]"))).click()
                            except TimeoutException:
                                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                                    (By.XPATH, f"/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/tbody/tr[{ridx+1}]/td[{cidx+1}]/button"))).click()
                                pass
                            except:
                                pass
                            break
                    except:
                        if int(td) == sheet_date.day:
                            try:
                                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                                    (By.XPATH, f"/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[2]/table/tbody/tr[{ridx+1}]/td[{cidx+1}]"))).click()
                            except TimeoutException:
                                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(
                                    (By.XPATH, f"/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/tbody/tr[{ridx+1}]/td[{cidx+1}]/button"))).click()
                            break

        except StaleElementReferenceException:
            print(StaleElementReferenceException, 'Occured!! [IGNORE]')
            pass

    def select_transaction_date_from_calendar(self, diff, sheet_date, old_calendar):
        print("sheet_date-> date:", sheet_date.day)
        try:
            try:
                date_row = self.browser.find_elements(
                    By.XPATH, '//*[@id="componentId"]/div[2]/form/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/ul/li/div/div/div/table/tbody/tr')
                if not date_row:
                    raise Exception
                print('Old Calendar')
            except:
                date_row = self.browser.find_elements(
                     By.XPATH, "/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[2]/table/tbody/tr")
                print('New Calendar')
        except NoSuchElementException or WebDriverException:
            date_row = self.browser.find_elements(
                By.XPATH, "/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div[2]/div[1]/div/div[1]/advanced-search/div/div[2]/form/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/ul/li/div/div/div/table/tbody/tr")
            print('old calendar2')

        for _ in range(abs(diff)):
            time.sleep(4)
            if diff < 0:
                try:
                    WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(
                        (By.XPATH, f'//*[@id="componentId"]/div[2]/form/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/ul/li/div/div/div/table/thead/tr[1]/th[3]/button'))).click()

                except TimeoutException or WebDriverException:
                    try:
                        WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(
                            (By.XPATH, f"/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[1]/bs-datepicker-navigation-view/button[4]"))).click()
                    except TimeoutException or WebDriverException:
                        WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(
                            (By.XPATH, f"/html/body/div[2]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/thead/tr[1]/th[3]"))).click()
            else:
                try:
                    WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(
                        (By.XPATH, f"/html/body/div[2]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/thead/tr[1]/th[1]"))).click()
                except TimeoutException or WebDriverException:
                    try:
                        WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(
                            (By.XPATH, f"/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[1]/bs-datepicker-navigation-view/button[1]"))).click()
                    except TimeoutException or WebDriverException:
                        WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(
                            (By.XPATH, f'//*[@id="componentId"]/div[2]/form/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/ul/li/div/div/div/table/thead/tr[1]/th[1]/button'))).click()

        try:
            # print("Date Row",date_row)
            for ridx, rows in enumerate(date_row):
                if old_calendar:
                    rows = rows.text.split()
                else:
                    dates = self.browser.find_elements(
                        By.XPATH, f"/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[2]/table/tbody/tr[{ridx+1}]/td")
                    rows = dates
                # print("Rows",rows)
                if ridx == 0 and sheet_date.day > 7:
                    continue
                for cidx, td in enumerate(rows):
                    print(td)
                    if not old_calendar:
                        if int(td.text) == sheet_date.day:
                            time.sleep(4)
                            try:
                                WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(
                                    (By.XPATH, f"/html/body/bs-datepicker-container/div/div/div/div/bs-days-calendar-view/bs-calendar-layout/div[2]/table/tbody/tr[{ridx+1}]/td[{cidx+1}]"))).click()
                            except TimeoutException:
                                print('No Date element Found')
                                pass
                            break
                    else:
                        if int(td) == sheet_date.day:
                            x = 0
                            try:
                                try:
                                    fxpath = f"/html/body/div[2]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div[2]/div[1]/div/div[1]/advanced-search/div/div[2]/form/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/ul/li/div/div/div/table/tbody/tr[{ridx+1}]/td[{cidx+1}]/button/span"
                                    ele = WebDriverWait(self.browser, 8).until(
                                        EC.presence_of_element_located((By.XPATH, fxpath)))
                                    ele.click()
                                except TimeoutException or WebDriverException:
                                    # print('2nd try')
                                    ele = WebDriverWait(self.browser, 5).until(EC.presence_of_element_located(
                                        (By.XPATH, f"/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div[2]/div[1]/div/div[1]/advanced-search/div/div[2]/form/div[1]/div[1]/div/div[1]/div[1]/div[2]/div/div/ul/li/div/div/div/table/tbody/tr[{ridx+1}]/td[{cidx+1}]/button")))
                                    ele.click()
                            except TimeoutException or WebDriverException:
                                # print('3rd try')
                                WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(
                                    (By.XPATH, f"/html/body/div[*]/main/section/div[4]/div[3]/div/div/div[2]/feature-flag/div/flag-off-component/div/div/div/div[1]/div[2]/section/section/div[1]/div[1]/div/div/div/ul/li/div/div/div/table/tbody/tr[{ridx+1}]/td[{cidx+1}]/button"))).click()
                            break

        except StaleElementReferenceException:
            print(StaleElementReferenceException, 'Occured!! [IGNORE]')
            pass

    def upload_to_gdrive(self):
        print(' ---------------- UPLOAD IMAGE TO DRIVE ---------------- ')
        while True:
            access_token = utils.get_access_token()
            if utils.verify_token(access_token):
                break
            else:
                print('Invalid token, Retrying.')

        self.check_data_upload(access_token, self.gdrive_folder_id)
        # self.multi_txn_data_upload(access_token, self.gdrive_folder_id)
        self.transaction_data_upload(access_token, self.gdrive_folder_id)

    def transaction_data_upload(self, access_token, folder_id):
        processed_data = []
        try:
            pdf_dir = os.listdir(os.path.join(ROOT_DIR, 'pdf'))
            print('\n\t FILES IN PDF FOLDER:\n', pdf_dir)
            for (idx, (ref, (front_img_path, back_img_path, pdf_name))), row in zip(enumerate(self.image_name.items()), self.recent_transactions_data):
                print(f'\n\nREF: {ref}, ROW: {row}\n')
                max_retry = 0
                row.insert(5, 'no image')
                row.insert(6, 'no image')
                row.insert(7, 'no pdf')
                time.sleep(2)
                if idx % 20 == 0:
                    self.browser.refresh()
                if pdf_name and 'pdf' in pdf_name:
                    if os.path.exists(os.path.join(ROOT_DIR, 'pdf', pdf_name)):
                        print('\tPDF Found! in directory')
                        print(pdf_name)
                        pdf_link = utils.upload_file_to_drive(
                            pdf_name, access_token, folder_id)
                        print('pdf_link:', pdf_link)
                        row[7] = pdf_link
                    else:
                        print('\tPDF [NOT] Found! in Directory..')
                if front_img_path and back_img_path:
                    print('\tImage Found!\n')
                    while max_retry < 2:
                        try:
                            front_img_link = utils.upload_file_to_drive(
                                front_img_path, access_token, folder_id)
                            back_img_link = utils.upload_file_to_drive(
                                back_img_path, access_token, folder_id)
                            print('front_img_link:', front_img_link)
                            print('back_img_link:', back_img_link)
                            break
                        except:
                            max_retry += 1
                            print('retry_n0:', max_retry)
                            print('Failed to get link for file, Retrying!')
                            time.sleep(5)
                            if max_retry == 2:
                                print(
                                    'Setting [Failed] as default, unable to get link')
                                front_img_link = 'Failed'
                                back_img_link = 'Failed'
                                break

                    if row[4].split("/")[0] == ref.split('_')[0]:
                        row[5] = front_img_link
                        row[6] = back_img_link
                print('final row:', row)
                processed_data.append(row)
            print('Recent Transactions Data\n', self.recent_transactions_data)
            df = pd.DataFrame(processed_data)
            path = os.path.join(
                ROOT_DIR, f'csv_{self.username}', f'{self.all_data_map["recent_transactions_data"]}_{datetime.now().strftime("%d-%m-%Y_%H%M%S")}.csv')
            df.to_csv(path, encoding='utf-8-sig', index=False)
            print('\n\t CSV saved for Txns Data')

        except Exception as err:
            print(f'{err} Occured!\nSaving Current Txns Data into CSV')
            df = pd.DataFrame(processed_data)
            path = os.path.join(
                ROOT_DIR, f'csv_{self.username}', f'{self.all_data_map["recent_transactions_data"]}_{datetime.now().strftime("%d-%m-%Y_%H%M%S")}.csv')
            df.to_csv(path, encoding='utf-8-sig', index=False)
            print('\n\t CSV saved for Txns Data')

    def multi_txn_data_upload(self, access_token, folder_id):
        processed_data = []
        try:
            pdf_dir = os.listdir(os.path.join(ROOT_DIR, 'pdf'))
            print('\n\t FILES IN PDF FOLDER:\n', pdf_dir)
            for (idx, (ref, (front_img_path, back_img_path, pdf_name))), row in zip(enumerate(self.image_name.items()), self.multi_txns_data):
                print(f'\n\nREF: {ref}, ROW: {row}\n')
                max_retry = 0
                row.insert(5, 'no image')
                row.insert(6, 'no image')
                row.insert(7, 'no pdf')
                time.sleep(2)
                if idx % 20 == 0:
                    self.browser.refresh()
                if pdf_name:
                    if os.path.exists(os.path.join(ROOT_DIR, 'pdf', pdf_name)):
                        print('\tPDF Found! in directory')
                        print(pdf_name)
                        pdf_link = utils.upload_file_to_drive(
                            pdf_name, access_token, folder_id)
                        print('pdf_link:', pdf_link)
                        row[7] = pdf_link
                    else:
                        print('\tPDF [NOT] Found! in Directory..')
                if front_img_path and back_img_path:
                    print('\tImage Found!\n')
                    while max_retry < 2:
                        try:
                            front_img_link = utils.upload_file_to_drive(
                                front_img_path, access_token, folder_id)
                            back_img_link = utils.upload_file_to_drive(
                                back_img_path, access_token, folder_id)
                            print('front_img_link:', front_img_link)
                            print('back_img_link:', back_img_link)
                            break
                        except:
                            max_retry += 1
                            print('retry_n0:', max_retry)
                            print('Failed to get link for file, Retrying!')
                            time.sleep(5)
                            if max_retry == 2:
                                print(
                                    'Setting [Failed] as default, unable to get link')
                                front_img_link = 'Failed'
                                back_img_link = 'Failed'
                                break

                    if row[4].split("/")[0] == ref.split('_')[0]:
                        row[5] = front_img_link
                        row[6] = back_img_link
                print('final row:', row)
                processed_data.append(row)
            print('Recent Transactions Data\n', self.multi_txns_data)
            df = pd.DataFrame(processed_data)
            path = os.path.join(
                ROOT_DIR, f'csv_{self.username}', f'{self.all_data_map["Multi_txn_data"]}_{datetime.now().strftime("%d-%m-%Y_%H%M%S")}.csv')
            df.to_csv(path, encoding='utf-8-sig', index=False)
            print('\n\t CSV saved for Txns Data')

        except Exception as err:
            print(f'{err} Occured!\nSaving Current Txns Data into CSV')
            df = pd.DataFrame(processed_data)
            path = os.path.join(
                ROOT_DIR, f'csv_{self.username}', f'{self.all_data_map["Multi_txn_data"]}_{datetime.now().strftime("%d-%m-%Y_%H%M%S")}.csv')
            df.to_csv(path, encoding='utf-8-sig', index=False)
            print('\n\t CSV saved for Txns Data')

    def check_data_upload(self, access_token, folder_id):
        processed_data = []
        try:
            for idx, row in enumerate(self.dep_checks_data):
                max_retry = 0
                time.sleep(2)
                if idx % 10 == 0:
                    self.browser.refresh()
                if row[9] and row[10]:
                    while max_retry < 2:
                        try:
                            front_img_link = utils.upload_file_to_drive(
                                row[9], access_token, folder_id)
                            back_img_link = utils.upload_file_to_drive(
                                row[10], access_token, folder_id)
                            break
                        except:
                            max_retry += 1
                            print('Failed to get link for file, Retrying!')
                            time.sleep(5)
                            if max_retry == 2:
                                print(
                                    'Setting [Failed] as default, unable to get link')
                                front_img_link = 'Failed'
                                back_img_link = 'Failed'
                                break
                    row.pop(9)
                    row.insert(9, front_img_link)
                    row.pop(10)
                    row.insert(10, back_img_link)
                processed_data.append(row)
            print('Deposit Checks Data\n', self.dep_checks_data)
            df = pd.DataFrame(processed_data)
            path = os.path.join(
                ROOT_DIR, f'csv_{self.username}', f'{self.all_data_map["dep_checks_data"]}_{datetime.now().strftime("%d-%m-%Y_%H%M%S")}.csv')
            df.to_csv(path, encoding='utf-8-sig', index=False)
            print('\n\t CSV saved for Checks Data')

        except Exception as err:
            print(f'{err} Occured!\nSaving Current Checks Data into CSV')
            df = pd.DataFrame(processed_data)
            path = os.path.join(
                ROOT_DIR, f'csv_{self.username}', f'{self.all_data_map["dep_checks_data"]}_{datetime.now().strftime("%d-%m-%Y_%H%M%S")}.csv')
            df.to_csv(path, encoding='utf-8-sig', index=False)
            print('\n\t CSV saved for Checks Data')

    def push_data_to_drive(self):
        print(f"\n\t[Pushing data to drive for user - {self.username}]")

        print("\n\t\tPushing data for sheet:",
              self.all_data_map["dep_checks_data"])
        GoogleSheetHandler(data=self.dep_checks_data,
                           sheet_name=self.all_data_map["dep_checks_data"]).appendsheet_records()

        print("\n\t\tPushing data for sheet:",
              self.all_data_map["recent_transactions_data"])
        GoogleSheetHandler(data=self.recent_transactions_data,
                           sheet_name=self.all_data_map["recent_transactions_data"]).appendsheet_records()

        # print("\n\t\tPushing data for sheet:", self.all_data_map["Multi_txn_data"])
        # GoogleSheetHandler(data=self.multi_txns_data, sheet_name=self.all_data_map["Multi_txn_data"]).appendsheet_records()


if __name__ == '__main__':
    args = len(sys.argv)
    options = Options()

    if args > 1 and sys.argv[1].lower() == '--headless_mode=on':
        print('sys.argv:', sys.argv)
        """ Custom options for browser """
        prefs = {"download.default_directory": os.path.join(
            ROOT_DIR, 'pdf', 'tmp', '')}
        options.add_experimental_option("prefs", prefs)
        options.add_argument("--start-maximized")  # maximized window
        options.headless = True
        browser = webdriver.Chrome(
            executable_path=config.DRIVER_PATH, options=options)
    else:
        prefs = {"download.default_directory": os.path.join(
            ROOT_DIR, 'pdf', 'tmp', '')}
        options.add_experimental_option("prefs", prefs)
        options.add_argument("--start-maximized")  # maximized window

        browser = webdriver.Chrome(
            executable_path=config.DRIVER_PATH, options=options)

    print("\n\t\t* *  * *  * *  * *  * *  * * START  * *  * *  * *  * *  * * *")
    action = ActionChains(browser)
    users = GoogleSheetHandler(
        sheet_name=config.SHEET_USERS_TAB_NAME).getsheet_records()

    for user in users[1:]:
        if not user:
            break
        # if len(user) == 0 or len(user) <= 9:
        #     print("User doesn't exist.")
        #     continue
        # print("details of user : ", user)
        gdrive_folder_id = user[9]
        username, password = user[0], user[1]

        is_process_user = user[2]
        if is_process_user.upper() == 'NO':
            print(
                f'\n\t PROCESS USER {username}: {is_process_user.upper()}\n\n')
            print('\n\t SKIPPING USER\n\n')
            continue
        print(f'\n\t PROCESS USER {username}: {is_process_user.upper()}\n\n')

        recent_transactions = user[3]
        start_date_transactions = user[6]

        dep_checks = user[4]
        start_date_checks = user[7]

        start_date_multi_txn = user[8]
        multi_txns = user[5]

        print("\n\t START SCRAPPING FOR USER: %s\n\n" % username)
        current_date = datetime.now().date()

        start_date_transactions = datetime.strptime(
            start_date_transactions, '%d/%m/%Y').date()
        start_date_checks = datetime.strptime(
            start_date_checks, '%d/%m/%Y').date()
        start_date_multi_txn = datetime.strptime(
            start_date_multi_txn, '%d/%m/%Y').date()

        print(f'\n\t GDRIVE FOLDER ID: {gdrive_folder_id}\n\n')

        check_date_diff = (current_date - start_date_checks).days
        transaction_date_diff = (current_date - start_date_transactions).days
        multi_txn_date_diff = (current_date - start_date_multi_txn).days

        txn_flag = True
        check_flag = True
        multi_txn_flag = False
        while txn_flag or check_flag or True:
            if not (txn_flag or check_flag or multi_txn_flag):
                print(f'\n\t ALL DATA ARE PROCESSED FOR USER: {username}\n\n')
                break

            print('*'*100)
            print(f'\n\t CURRENT DATE: {current_date}\t\n')
            print(
                f'\n\t START TRANSACTIONS DATE: {start_date_transactions}\t\n')
            if check_date_diff >= 360 and dep_checks.upper() == 'YES':
                print(
                    f'\n\t YOU HAVE SELECTED CHECK DATE FOR 360+ DAYS!!\n\t SELECTING LAST 12 MONTHS CHECK DATA!\n')
            else:
                print(f'\n\t LAST CHECK DATE: {start_date_checks}\t\n')

            if transaction_date_diff >= 360 and recent_transactions.upper() == 'YES':
                print(
                    f'\n\t YOU HAVE SELECTED TRANSACTION DATE FOR 360+ DAYS!!\n\t SELECTING LAST 12 MONTHS TRANSACTION DATA!\n')
            else:
                print(
                    f'\n\t LAST TRANSACTION DATE: {start_date_transactions}\t\n\n')

            # if multi_txn_date_diff >= 360 and multi_txns.upper() == 'YES':
            #     print(f'\n\t YOU HAVE SELECTED TRANSACTION DATE FOR 360+ DAYS!!\n\t SELECTING LAST 12 MONTHS TRANSACTION DATA!\n')
            # else: print(f'\n\t LAST MULTI TRANSACTION DATE: {start_date_multi_txn}\t\n\n')
            print('*'*100)

            scrapper = DataScrapping(
                browser, username, password, recent_transactions, dep_checks, multi_txns, check_date_diff, transaction_date_diff,
                start_date_transactions, start_date_checks, start_date_multi_txn, gdrive_folder_id, multi_txn_date_diff
            )
            scrapper.login_to_site()
            if scrapper.user_login:
                try:
                    scrapper.create_directories()
                    check_flag = scrapper.is_checks_left()
                    # multi_txn_flag, multi_txn_date = scrapper.is_multi_txns_left()
                    txn_flag = scrapper.is_txns_left()

                    # if multi_txn_date:
                    #     start_date_multi_txn = multi_txn_date

                except Exception as err:
                    print(f"Error in : {traceback.format_exc()}")

                shutil.rmtree('pdf/tmp')
                shutil.rmtree(f'images_{username}/tmp')
                scrapper.upload_to_gdrive()
                scrapper.push_data_to_drive()
                scrapper.logout()

                # check_flag, txn_flag = False, False
                print(
                    f'\n\t All Checks Data [NOT] processed for {username}: {check_flag}\n\n')
                print(
                    f'\n\t All Transaction Data [NOT] processed for {username}: {txn_flag}\n\n')
                # print(f'\n\t All Multiple Transaction Data [NOT] processed for {username}: {multi_txn_flag}\n\n')

            transaction_date, txn_ref = utils.get_last_sheet_record_txns(
                username)
            check_date, check_ref = utils.get_last_sheet_record_checks(
                username)
            # multi_txn_date, multi_txn_ref = utils.get_last_sheet_record_multiple_check_txns(username)
            print('Check Date:', check_date)

            if transaction_date:
                start_date_transactions = transaction_date
            if check_date:
                start_date_checks = check_date

        print("\n\tEnd activity for user!\n\n")
    browser.close()
