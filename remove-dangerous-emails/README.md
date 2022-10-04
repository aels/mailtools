# validol.php - mail validation script.
<img width="909" alt="image" src="https://user-images.githubusercontent.com/1212294/177665014-4fd269f3-0911-41a6-aa3f-2da2c38d74fa.png">

It's intented to remove from your mail list all emails which are hosted or are managed by security-related companies, such as __perimeterwatch__, __proofpoint__, __fireeye__ and so on (total ~50 vendors).
Checks are performed by looking at:
- mx records of email domain
- subnet name of server of mx records
- reverse ptr of email host
- title of host's website

Also emails like `staff@`, `admin@`, `support@` and so on are removed by default.
Emails which are hosted on _edu_, _gov_ and _mil_ domains are also removed.
This script __do not checks for and do not remove__ non-existent emails, cuz in my opinion it's not that dangerous to send email to nowhere. Also all big email providers effectively supress ability to check mailbox existance by returning "exist" responces after few checks.
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
mail_list file itself can by any format with any data. Only requirement - better it to contain some emails to check. They will be excracted with RegExp, leaving other data untouched,
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
Script can check ~50k-200k emails per hour. It is single-threaded, cuz i'm too lazy to rewrite it in python. But if you wish to do so, pull requests are welcome.
