# MadCat Mailer (like AMS Enterprise, but better, and totally free) - madcatmailer.py
<img width="905" alt="image" src="https://github.com/user-attachments/assets/2685d500-3c30-4dc7-9de1-d5cc3019e279" />


Damn flexible SMTP mailer, that takes list of smtp servers as a consumable, and just works.
## Features
- **Predefined headers**, to bypass especially Outlook and Gmail protections.
- Many low-level tweaks to bypass Gmail antispam.
- Have 0% chance that you will shoot yourself in the leg using it. All important triggers are hard-coded.
- Supports SMTP servers cracked by [MadCat smtp-checker](https://github.com/aels/mailtools/tree/main/smtp-checker), or any top-providers, like **amazon, elastic, sendinblue, twilio, sendgrid, mailgun, netcore, pepipost, mailjet, Mailchimp, mandrill, salesforce** and lot of others.
- Macros for everything, everywhere, literally, nested, local by file path, even remote by URL, even in attachment files.
- **Built-in phone number obfuscator (keeps numbers diallable)**.
- **Built-in zero-font support, that works, and will not ruin your inbox**.
- Built-in html params and style properties randomization.
- Support of "random file from folder" for letters and attachements.
- Support of remote letter/attachments from url.
- Slow start for warming-up smtps and slow-mode for gmail.
- Intelligent smtp management.
- Flexible config management for each campaing.
- "Test run" before every campaign start. And multiple verification emails support.
- Automatic ip blacklist checking.
- ... and many other small perks.

## Setup
No need to download anything. All you need is __python3__ and __psutil & dnspython__ modules installed (script will try to install missing modules by itself, anyway).
## Usage
You need python3 installed. Just run this command on you linux vps (or inside WSL console on Windows)
```
python3 <(curl -slkSL vo.la/MAkwGFf)
```
and mailer will download it's config file to the current directory under the name "dummy.config"



## Legal Notices
You are ONLY allowed to use the following code for educational purposes!

This script shall not be used for any kind of illegal activity nor law enforcement at any time. This restriction applies to all cases of usage, no matter whether the code as a whole or only parts of it are being used.

By downloading and/or using any part of the code and/or any file of this repository, you agree to this restriction without remarks.
