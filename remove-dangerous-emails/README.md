# validol - mail validation script (get_safe_mails.py).
![image](https://user-images.githubusercontent.com/1212294/197357350-69b0d660-a2e0-44e2-9a91-61ea89650de1.png)

It's intented to remove from your mail list all emails which are hosted or are managed by security-related companies, such as __perimeterwatch__, __proofpoint__, __fireeye__ and so on (total ~50 vendors).
Checks are performed by looking at:
- mx records of email domain
- subnet name of server of mx records
- reverse ptr of email host
- title of host's website

*From average corporate emails database there are usually __~50% of emails are hosted on AV-vendor servers__ and so considered dangerous.

Also emails like `staff@`, `admin@`, `support@` and so on are removed by default.
Emails which are hosted on _edu_, _gov_ and _mil_ domains are also removed.
This script __do not checks for and do not remove__ non-existent emails, cuz in my opinion it's not that dangerous to send email to nowhere. Also all big email providers effectively supress ability to check mailbox existance by returning "exist" responces after few checks.
## Setup
- you need __python3__ installed, and some modules (script will try to install missing modules by itself, but it's better to help him):
```
pip3 install psutil requests dnspython IP2Location
```
- _Optionaly_ you can download `get_safe_mails.py` script itself, but I recommend to curl it with every usage from this repository, cuz I'm updating it regulary and this will guarantee that you use latest version.
- All done, we can go.
## Usage
```
python3 <(curl -fskSL gg.gg/email-validator) /path/to/mail_list.txt
```
Script will produce two new files: __mail\_list\_dangerous.txt__ with dangerous mails and reasons of each, and __mail\_list\_safe.txt__ which is your source file with dangerous lines removed.
__mail\_list.txt__ file itself can by any format with any data. Only requirement - better it to contain some emails to check. They will be excracted with RegExp, leaving other data untouched,
so basically strings like
```
April,Rdson,Data Entry Specialist- Sustainabilty,arichardson@hobokenumc.com,2014181000
Abby,Minnick,General Laborer,abby_minnick@hamiltoncityschools.com,5138875000
Angel,Pellot,Director - Sourcing and Vendor Management,angel.pellot@wellcare.com,8132906200
Ann,Hatchell,Copywriter,ann.hatchell@gadoe.org,4046562800
Ana,Diaz,"Producer, Good Morning America",adiaz@justdesserts.com,5105672900
```
or
```
mail@ofukuwake.net:kouhei0729
osnet@osnet.net:special
goctavo@arrangerconsulting.it:arranger1
management@meltblue.com:kousukenagata
```
are OK.
## Speed. It's fast.
Script can check ~1,000,000 emails per hour. Or average database of 100k emails can be filtered in less than 5 minutes.

# validol.php - deprecated in favor of much faster get_safe_mails.py.
<img width="909" alt="image" src="https://user-images.githubusercontent.com/1212294/177665014-4fd269f3-0911-41a6-aa3f-2da2c38d74fa.png">

## Setup
- go to empty directory, where geo-ip database and packages will be located
- download ip2location php classes with composer:
```
composer require ip2location/ip2location-php
```
- download _ip2location.bin_ database itself from url https://github.com/aels/mailtools/releases/download/ip2location/ip2location.bin and put it into the same folder.
This database contains required subnet names data.
- _Optionaly_ you can download `validol.php` script itself, but I recommend to curl it with every usage from this repository.
- All done, we can go.
## Usage
Ofc you need __php installed__, if so, example command is:
```
php <(curl -fskSL bit.ly/va1idol) email-file1,maillist2,/path/to/maillist3
```
Script will produce two new files: _mails_bad.txt_ with dangerous mails and reasons of each, and _mails_validated.txt_ which is your source file with dangerous lines removed.
