# Read marks from CSV and submit it to the University of Alberta DoC's DB.
#
# Developed by Mohammad-Reza Daliri (daliri@ualberta.ca) to make the job of TAs and instructors easier.
#
# Copyright (C) 2019 Mohammad-Reza Daliri
# Licensed under GNU General Public License 3 (GPL-3.0)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__version__ = '1.0.0'

import csv
import re
import sys
from getpass import getpass

import requests
from bs4 import BeautifulSoup
import argparse


def dict_to_multipart_data(data):
    output = {}
    for key, value in data.items():
        output[key] = (None, value)
    return output


def send_request(url, data):
    response = requests.post(url, files=dict_to_multipart_data(data))
    if response.status_code != 200:
        raise ConnectionError('Connection failed.')
    return str(response.content)


def make_marks(username, password, season, year, course_abbr, course_num, csv_path, csv_ccid_column='CCID',
               csv_score_column='Score'):
    docsdb_url = 'https://docsdb.cs.ualberta.ca/Prod/classlist2.cgi'
    data = {
        'oracle.login': username,
        'oracle.password': password,
        'season': season,
        'year': year,
        'abbrev': course_abbr,
        'coursenum': course_num,
        'secttype': 'All Lectures',
        'sectnum': '',
        'sectpre': '',

        'list_type': 'Registered Students Only',
        'order_by': 'Student ID',
        'id': 'on',
        'ccid': 'on'
    }

    response = send_request(docsdb_url, data)
    soup = BeautifulSoup(response, 'lxml')

    students = {}
    students_table = soup.find_all('table')[1]
    for row in students_table.find_all('tr'):
        try:
            student_id, ccid = row.find_all('td')
        except ValueError:  # Jump over the first row which contains headers (th)
            continue
        ccid = ccid.text.strip()[:-12]  # Remove @ualberta.ca from CCID
        students[ccid] = student_id.text.strip()

    marks = {}
    with open(csv_path, newline='') as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            ccid = row[csv_ccid_column]
            score = row[csv_score_column]
            student_id = int(students[ccid])

            marks[student_id] = score
    return marks


def login_to_docsdb(username, password):
    docsdb_url = 'https://docsdb.cs.ualberta.ca/Prod/login.cgi'
    data = {
        'oracle.login': username,
        'oracle.password': password
    }

    response = send_request(docsdb_url, data)
    if response.find('Unable to login.') != -1:
        raise Exception('Cannot login to DoC\'s DB.')

    soup = BeautifulSoup(response, 'lxml')
    return (soup.find('input', {'name': 'oracle.login'}).get('value', username),
            soup.find('input', {'name': 'oracle.password'}).get('value', None))


def get_marksheet(username, password, season, year, course_abbr, course_num, assignment):
    docsdb_url = 'https://docsdb.cs.ualberta.ca/Prod/entersection2.cgi'

    data = {
        'order_by': 'Student ID',
        '.submit': 'Get List',
        'oracle.login': username,
        'oracle.password': password,
        'season': season,
        'year': year,
        'abbrev': course_abbr,
        'coursenum': course_num,
        'secttype': 'All Sections',
        'sectnum': '',
        'sectpre': '',
        'type': '',
        'num': '',
    }

    response = send_request(docsdb_url, data)
    soup = BeautifulSoup(response, 'lxml')

    # Course ID in DoC's DB
    course_id = soup.find('input', {'name': 'term'}).get('value')

    data = {
        'term': course_id,
        'order_by': 'Student ID',
        'assignment': assignment.replace(' ', ';'),
        '.submit': 'Get List',
        'oracle.login': username,
        'oracle.password': password,
        'season': season,
        'year': year,
        'abbrev': course_abbr,
        'coursenum': course_num,
        'secttype': 'All Sections',
        'sectnum': ''
    }

    response = send_request(docsdb_url, data)

    marksheet = {}
    soup = BeautifulSoup(response, 'lxml')
    id_inputs = soup.find_all('input', {'name': re.compile('^id[0-9]+')})
    mark_inputs = soup.find_all('input', {'name': re.compile('^mark[0-9]+')})
    old_mark_inputs = soup.find_all('input', {'name': re.compile('^oldmark[0-9]+')})
    ea_flag_inputs = soup.find_all('input', {'name': re.compile('^eaflag[0-9]+')})
    old_ea_flag_inputs = soup.find_all('input', {'name': re.compile('^oldeaflag[0-9]+')})

    # Due to performance issues, we assume inputs are in order.
    # It means all inputs related to one student come before inputs related to another person.
    # This assumption has been proven to be correct in the development time.
    for (id_input, mark_input, old_mark_input, ea_flag_input, old_ea_flag_input) in zip(id_inputs, mark_inputs,
                                                                                        old_mark_inputs, ea_flag_inputs,
                                                                                        old_ea_flag_inputs):
        index = int(re.compile('[0-9]+').search(id_input['name']).group())
        student_id = int(id_input['value'])
        mark = mark_input.get('value', '')
        old_mark = old_mark_input.get('value', '')
        ea_flag = ea_flag_input['value'] if ea_flag_input.get('checked', None) else ''
        old_ea_flag = old_ea_flag_input.get('value', '')
        marksheet[student_id] = {'index': index, 'mark': mark, 'old_mark': old_mark, 'ea_flag': ea_flag,
                                 'old_ea_flag': old_ea_flag}

    misc_inputs = {}
    for form_input in soup.find('input', {'name': ['earole', 'maxmark', 'dbarole', 'secretnum', 'bonus']}):
        misc_inputs[form_input['name']] = form_input['value']

    return {'inputs': misc_inputs, 'marks': marksheet}


def submit_to_docsdb(username, password, season, year, course_abbr, course_num, marks, marksheet, store):
    docsdb_url = 'https://docsdb.cs.ualberta.ca/Prod/entersection3.cgi'

    data = {
        '.submit': 'Enter Marks',
        'oracle.login': username,
        'oracle.password': password,
        'season': season,
        'year': year,
        'abbrev': course_abbr,
        'coursenum': course_num,
        'secttype': 'All Sections',
        'sectnum': ''
    }
    data.update(marksheet['inputs'])

    if not store:
        print(
            """
    NO CHANGES WILL SUBMITTED TO THE SERVER!
    Please review and confirm submission data and the re-run the script with same arguments in addition to -s.
            """)

    print("\nProcessed marks:\n----------------------")
    i = 0
    for student_id, score in marks.items():
        if student_id not in marksheet['marks']:
            continue
        marksheet['marks'][student_id]['mark'] = score

        print("{0}. Update student #{1} [New mark: '{2}', Old mark: '{3}']".format(
            i + 1, student_id, score, marksheet['marks'][student_id].get('old_mark', '')))
        i = i + 1

    print("\n\nSubmission full dump:\n----------------------")
    for student_id, details in marksheet['marks'].items():
        i = details['index']
        data.update({
            'id%d' % i: student_id,
            'mark%d' % i: details.get('mark', ''),
            'oldmark%d' % i: details.get('old_mark', ''),
            'eaflag%d' % i: details.get('ea_flag', ''),
            'oldeaflag%d' % i: details.get('old_ea_flag', '')
        })

        print("{0}. Student #{1} [Submitted mark: '{2}', Old mark: '{3}', EA flag: '{4}', Old EA flag: '{5}']".format(
            i + 1, student_id, details.get('mark', ''), details.get('old_mark', ''), details.get('ea_flag', ''),
            details.get('old_ea_flag', '')))

    if store:
        response = send_request(docsdb_url, data)
        return response.find('Entering Marks Complete') != -1
    else:
        print(
            """
    NOTHING HAS BEEN SUBMITTED!
    Please review and confirm submission data and the re-run the script with same arguments in addition to -s.
            """)
        return True


def submit_marks(username, password, course, term, assignment, csv_path, csv_ccid, csv_score, submit=False):
    username, password = login_to_docsdb(username, password)
    course_abbr, course_num = course.split(' ')
    season, year = term.split(' ')
    season = season.title()

    marks = make_marks(username=username, password=password, course_abbr=course_abbr, course_num=course_num,
                       season=season, year=year, csv_path=csv_path, csv_ccid_column=csv_ccid,
                       csv_score_column=csv_score)
    marksheet = get_marksheet(username=username, password=password, course_abbr=course_abbr, course_num=course_num,
                              season=season, year=year, assignment=assignment)

    return submit_to_docsdb(username=username, password=password, course_abbr=course_abbr, course_num=course_num,
                            season=season, year=year, marks=marks, marksheet=marksheet, store=submit)


def print_statement():
    print('Developed by Mohammad-Reza Daliri (daliri@ualberta.ca) to make the job of TAs and instructors easier.')
    print('Licensed under GNU General Public License 3 (GPL-3.0)')
    print('''
Copyright (C) 2019 Mohammad-Reza Daliri
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
    ''')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read marks from CSV and submit it to the University of Alberta DoC\'s DB. Developed by Mohammad-Reza Daliri (daliri@ualberta.ca) to make the job of TAs and instructors easier. IT COMES WITHOUT ANY WARRANTY under GNU GPL-3.0 License.')
    parser.add_argument('--version', action='version', version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument('-u', '--username', help='Your DoC\'s DB username.', required=True)
    parser.add_argument('-p', '--password', action='store_true',
                        help='Do NOT enter your password here. It will be asked.', required=True)
    parser.add_argument('-c', '--course', help='Course full name in form of "CMPUT 123".', required=True)
    parser.add_argument('-t', '--term', help='Specify semester, e.g. Fall 2019.', required=True)
    parser.add_argument('-a', '--assignment', required=True,
                        help='The assignment name and number. Please enter what you see in the \'Enter Section Marks\' menu of DoC\'s DB. For instance, "Assignment 1".')
    parser.add_argument('-f', '--csv', help='Path to the marks CSV file.', required=True)
    parser.add_argument('--csv-ccid', dest='csv_ccid', help='CCID column name in the CSV file. (default: CCID)', default='CCID')
    parser.add_argument('--csv-score', dest='csv_score', help='Score column name in the CSV file. (default: Score)', default='Score')
    parser.add_argument('-s', '--submit', action='store_true',
                        help='When supplied, the scores will be uploaded to DoC\'s DB. Otherwise, it will just process data and print them for confirmation.',
                        default=False)
    args = parser.parse_args()

    if args.password:
        password = getpass('DoC\'s DB password: ')
    else:
        sys.exit('Password is required.')

    print_statement()
    result = submit_marks(course=args.course, term=args.term, username=args.username, password=password,
                          assignment=args.assignment, csv_path=args.csv, csv_ccid=args.csv_ccid,
                          csv_score=args.csv_score, submit=args.submit)

    if not result:
        sys.exit("An error has occurred. Please try again or contact the developer.")
