Title: How I Bypassed Voucher Limits Using a Race Condition Vulnerability
Subtitle: A CTF web challenge, FLAG SHOP 2.0, and how parallel requests broke a one voucher per user check
Date: 2025-12-15
Tags: race condition, ctf, bug bounty
Banner: images/race-01-interface.webp

So last night I played a CTF. Of course, it was free and with no prize. I know you are not here to listen to my bla bla bla about my CTF journey, but wait brooo, I'll share.

Actually, there is a web challenge named **FLAG SHOP 2.0**. This challenge was HARD level for those who don't know about this vulnerability, but let me tell you how it looks.

## Challenge Overview

In this challenge, the application allows users to:

- Grab Voucher
- Check Voucher
- Buy Flag

![The FLAG SHOP 2.0 challenge interface](images/race-01-interface.webp)

When you enter a name such as `shadow_monarch` and click on **Buy Flag**, the application tells you that you must collect 5 vouchers with the same name.

![Grabbing a voucher for shadowMonarch](images/race-02-voucher-acquired.webp)

## Normal Behavior

First, enter the name `shadow_monarch` and click on **Grab Voucher**. You will receive one voucher code.

If you try grabbing another voucher using the same name, you get an error, because the backend restricts this action to a single voucher per user.

![A second grab attempt returns an error](images/race-03-tickets-sold.webp)

## The Hint

This behavior hints at a **race condition** vulnerability.

The server performs the "only allow one voucher" check incorrectly when multiple requests hit simultaneously.

Whenever you see an operation that is supposed to be performed only once, or a limited number of times, you can try testing it for a race condition vulnerability.

## Exploitation (Race Condition)

To exploit it:

1. Enter `shadow_monarch` and click **Grab Voucher**.

![Intercepting the request in Burp Suite](images/race-04-burp-intercept.webp)

2. Intercept the request in Burp Suite.
3. Send the request to Repeater and duplicate it 10 times.
4. Select all duplicate requests and group them.

![Grouping the duplicated requests in Burp Repeater](images/race-05-burp-group.webp)

![Ten duplicated requests in a Burp Repeater group](images/race-06-burp-10tabs.webp)

5. Change the request sending mode to **Send in parallel**.
6. Send all requests at once.

![Switching the group send mode to Send in parallel](images/race-07-send-parallel.webp)

Because of the race condition, the server fails to properly enforce the single voucher check, and you receive multiple vouchers for the same user.

![Sending all requests in parallel](images/race-08-parallel-response.webp)

## Getting the Flag

After collecting at least 5 valid vouchers, click on **Buy Flag** using the same name:

👉 The flag is successfully returned.

![The flag returned after the race condition](images/race-09-flag.webp)

## Final Thoughts

I know it's a simple vulnerability, nothing interesting, I agree. But I saw many bug bounty hunters not hunting this vulnerability many times. Also, if they do hunt it, they don't know properly where and when to use it.

That's why I wrote this writeup: to let you guys know about this vulnerability. And not just this, if anybody reading this is good at race condition hunting, drop your tips in the comments.

Do claps and follow me on Medium and LinkedIn to connect with me, and I'll share more writeups in the future.

📌 Connect on LinkedIn: [Danish Ahmed](https://www.linkedin.com/in/danish-ahmed-61927b265/)
