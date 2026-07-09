Title: How a Simple SSTI Turned Into $1,000 and RCE
Subtitle: Turning a template placeholder in email settings into remote code execution
Date: 2025-12-15
Tags: ssti, rce, bug bounty
Reward: 1000 USD
Banner: images/ssti-bug-bounty-email.webp

Hey everyone! What started as routine reconnaissance on a web application turned into a critical find: a **Server Side Template Injection (SSTI)** that I escalated to **Remote Code Execution (RCE)**. The reward? A cool $1,000 wired straight to my PayPal. If you're into bug hunting, this story might give you some inspiration for your next recon session.

## The Target: A Feature Rich Platform

The site in question is a versatile platform where users can create custom subdomains, manage customers, generate invoices, send emails, and even set up products for sale. It's got way more functionality than meets the eye at first, like a mini ecommerce and CRM rolled into one. Interestingly, this is the same site where I previously uncovered an XSS vulnerability.

(You can check out the writeup for that bug [here](https://infosecwriteups.com/how-i-found-a-250-xss-bug-after-losing-hope-in-bug-bounty-8ab557df4d1d).)

After that XSS find, I decided to dig deeper. I spent time on thorough reconnaissance: enumerating endpoints, checking for common misconfigurations, and poking around every nook and cranny. I uncovered a few low hanging fruits, minor issues like weak headers or info leaks, but nothing screamed "critical" yet. Patience is key in bug bounties, right?

## The Discovery: Spotting SSTI in Email Templates

Everything changed when I navigated to the **Settings** page. There was an option to create custom email templates for personalizing messages to customers. What caught my eye were the prefilled tags like `{{fname}}` and `{{email}}`. These looked suspiciously like template variables, which screamed potential for injection.

To test my hunch, I created a new email template and replaced one of the tags with a simple math expression: `{{7*7}}`. I saved it, headed over to the Customers section, selected the new template, and sent a test email. Boom, there it was: **"49"** rendered in the email preview. Classic Server Side Template Injection confirmed! The app was evaluating user supplied input as code in its templating engine.

## Escalating to RCE: From Injection to Command Execution

SSTI is powerful, but I wanted to see if I could push it further to Remote Code Execution. I grabbed a solid list of payloads from this GitHub repo: [payloadbox/ssti-payloads](https://github.com/payloadbox/ssti-payloads). It's a goldmine for testing various templating engines.

After a bit of trial and error, I found a working payload that hinted at PHP under the hood:

```
{php}echo `id`;{/php}
```

This rendered `web` in the output, likely the username of the web server process. Jackpot! Now I knew code execution was possible.

To read sensitive files, I crafted this payload:

```
{{['cat\x20/etc/passwd']|filter('system')}}
```

And sure enough, it dumped the contents of `/etc/passwd`. At this point, I had full proof of concept for RCE. I stopped short of deeper exploitation to avoid any unintended damage, ethical hacking rules!

## Reporting the Bug

Reporting bugs can be tedious, especially when you're excited about the find but dread writing the detailed steps. I used AI tools to help generate a polished report. I fed in the details: steps to reproduce, payloads, impact assessment (arbitrary code execution leading to data breaches or server takeover), and remediation suggestions (like sanitizing user input in templates).

The result was a professional writeup in minutes. I tweaked it a bit for my voice, attached screenshots of the PoC, and submitted it through the platform's bug bounty program.

Then came the wait, four long weeks of radio silence. Finally, an email popped up: "Nice job, buddy! Here's your $1,000. Send us your PayPal details." Sweet victory!

## Lessons Learned and Final Thoughts

This bug reinforces a few key takeaways for aspiring bug hunters:

- Don't rush, explore all features, especially those involving user input like templates.
- SSTI can hide in plain sight, especially in customizable areas.
- Repos like payloadbox save hours of manual crafting.
- A clear, well structured report matters as much as the find itself.
- That $1,000 came after persistent digging and a solid report.

If you're in the bug bounty game, keep grinding! Who knows what your next recon will uncover? Drop a comment if you've had similar finds, and feel free to connect on Medium, X or LinkedIn. Happy hunting! :)

![Bug bounty support email confirming the SSTI report, marked severity Critical](images/ssti-bug-bounty-email.webp)

📌 Connect on LinkedIn: [Danish Ahmed](https://www.linkedin.com/in/danish-ahmed-61927b265/)
