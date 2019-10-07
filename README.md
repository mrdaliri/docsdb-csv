# DoC's DB CSV Import Tool

Read marks from CSV file and submit it to the University of Alberta DoC's DB.

Developed by Mohammad-Reza Daliri (daliri@ualberta.ca) to make the job of TAs and instructors easier. It is a not-for-profit personal project and is not affiliated with UAlberta officials.


> Copyright (C) 2019 Mohammad-Reza Daliri
>
> This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
>
> This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
>
> You should have received a copy of the GNU General Public
> License   along with this program.  If not, see
> <https://www.gnu.org/licenses/>.

# Getting Started

It is a python program which has some package dependencies. Required packages are listed in `requirements.txt`. You may install them by `pip` in your environment:

```
pip install -r requirements.txt
```
Then run program with following arguments:
```
 submit_marks.py [-h] -u USERNAME -p -c COURSE -t TERM -a ASSIGNMENT -f CSV [--csv-ccid CSV_CCID] [--csv-score CSV_SCORE] [-s]
```
Please note that to provide more safety, unless you supply the `-s` flag, no modifications will get submitted to the server.
So it is advised to first run the program without `-s` flag (default behaviour) to review and confirm results; and then re-run it with that flag to save and submit changes to the server.

# Options
Following guide is available with `--help` argument:

    usage: submit_marks.py [-h] -u USERNAME -p -c COURSE -t TERM -a ASSIGNMENT -f
                           CSV [--csv-ccid CSV_CCID] [--csv-score CSV_SCORE] [-s]

    Read marks from CSV and submit it to the University of Alberta DoC's DB.
    Developed by Mohammad-Reza Daliri (daliri@ualberta.ca) to make the job of TAs
    and instructors easier. IT COMES WITHOUT ANY WARRANTY under GNU GPL-3.0
    License.

    optional arguments:
      -h, --help            show this help message and exit
      -u USERNAME, --username USERNAME
                            Your DoC's DB username.
      -p, --password        Do NOT enter your password here. It will be asked.
      -c COURSE, --course COURSE
                            Course full name in form of "CMPUT 123".
      -t TERM, --term TERM  Specify semester, e.g. Fall 2019.
      -a ASSIGNMENT, --assignment ASSIGNMENT
                            The assignment name and number. Please enter what you
                            see in the 'Enter Section Marks' menu of DoC's DB. For
                            instance, "Assignment 1".
      -f CSV, --csv CSV     Path to the marks CSV file.
      --csv-ccid CSV_CCID   CCID column name in the CSV file. (default: CCID)
      --csv-score CSV_SCORE
                            Score column name in the CSV file. (default: Score)
      -s, --submit          When supplied, the scores will be uploaded to DoC's
                            DB. Otherwise, it will just process data and print
                            them for confirmation.


# Version
Current version is **1.0.0**.