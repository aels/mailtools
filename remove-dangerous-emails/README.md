# validol - mail validation script (get_safe_mails.py)
![image](https://user-images.githubusercontent.com/1212294/197357350-69b0d660-a2e0-44e2-9a91-61ea89650de1.png)

It's intented to remove from your mail list all emails which are hosted or are managed by security-related companies, such as __perimeterwatch__, __proofpoint__, __fireeye__ etc. (total 50+ vendors).
Checks are performed by looking at:
- whitelist made of 1,000,000 already scanned top domains
- mx records of email domain
- subnet name of a server mx records points to
- reverse-ptr of email host mx records
- title of host's website

__*__ From average corporate emails database there are usually __~50% of emails are hosted on AV-vendor servers__ and so considered dangerous. Validol filters out __all known threats__ and most of unknown security companies hosted emails, ensuring that you mail campaign will not fire your ass.

Emails like `staff@`, `admin@`, `support@` or hosted on `.edu`, `.gov` and `.mil` domains are removed by default.
This script __do not checks for and do not remove__ non-existent emails, cuz in my opinion it's not that dangerous to send email to nowhere. Also all big email providers effectively supress ability to check mailbox existance by returning "exist" responces after few checks.
## Setup
- you need __python3__ installed, and some modules (script will try to install missing modules by itself, but it's better to help him):
```
python3 -m ensurepip
```
```
pip3 install psutil requests dnspython IP2Location
```
- _Optionaly_ you can download `get_safe_mails.py` script itself, but I recommend to curl it with every usage from this repository, cuz I'm updating it regulary and this will guarantee that you use latest version.
- All done, we can go.
## Usage
```
python3 <(curl -fskSL gg.gg/email-validator)
```
and validol will ask you for path to database you want to validate and desired email providers you want to leave in this list (if you want only "outlook" emails, for example).

Or you can supply path to mail list as parameter:
```
python3 <(curl -fskSL gg.gg/email-validator) /path/to/mail_list.txt
```
Script will produce two new files: __mail\_list\_dangerous.txt__ with dangerous mails and reasons of each, and __mail\_list\_safe.txt__ which is your source file with dangerous lines removed.
__mail\_list.txt__ file itself can by any format with any data. Only requirement - better it to contain some emails to check. They will be excracted with RegExp, leaving other data untouched,
so basically strings like
```
April,Rdson,Data Entry Specialist- Sustainabilty,arichardson@hobokenumc.com,2014181000
```
or
```
mail@ofukuwake.net:kouhei0729
```
are OK.
## Speed. It's fast.
Validol can check __~1,500,000 emails per hour__. Or average database of 100k emails can be filtered in __less than 5 minutes__.



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
php <(curl -fskSL bit.ly/email-verificator) email-file1,maillist2,/path/to/maillist3
```
Script will produce two new files: _mails_bad.txt_ with dangerous mails and reasons of each, and _mails_validated.txt_ which is your source file with dangerous lines removed.
