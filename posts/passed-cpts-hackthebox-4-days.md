Title: Alhamdulillah! I Passed CPTS on HackTheBox in Just 4 Days
Subtitle: My CPTS preparation, the mistakes that cost me time, and the reporting tips that matter
Date: 2026-05-01
Tags: cpts, hackthebox, certification
Banner: images/cpts-certificate.jpeg

Hey everyone, I recently cleared the **HTB Certified Penetration Testing Specialist (CPTS)** exam in only 4 days. I'm writing this blog to share my preparation journey, the mistakes I made, and some tips that might help you.

CPTS is one of the hardest and most respected offensive security certifications. It includes both Linux and Active Directory machines. To pass, you need to submit **12 flags** (you can submit up to 14 if you want). I submitted exactly 12 because I was busy with other things.

## Preparation

Before attempting the exam, you **must** complete the 28 prerequisite modules on HackTheBox Academy:

[HTB CPTS Prerequisites](https://academy.hackthebox.com/preview/certifications/htb-certified-penetration-testing-specialist/prerequisites)

For extra practice, I highly recommend these Pro Labs:

- **Dante** &rarr; best for Linux practice
- **Zephyr** &rarr; excellent for Active Directory
- **Offshore** &rarr; great for both Linux and Active Directory

![HackTheBox Pro Labs overview: Zephyr, Dante, and Offshore](images/htb-prolabs.jpg)

If you can solve these labs without write ups, you'll be in a strong position.

I also suggest using a timer to track how long it takes you to complete a full Pro Lab. It's not mandatory but it really helps you understand your pace.

## My Experience and Mistakes

I was super excited on exam day and jumped in with almost zero fresh preparation. That overconfidence cost me time.

One major issue came on my 4th machine. I discovered another network interface and realized I needed **double pivoting**. I had been using an old version of Ligolo for years and didn't know the new Ligolo-ng supports double pivoting easily. It took me almost a full day to figure it out and learn the proper method.

If you're not comfortable with double pivoting using Ligolo-ng, check out this article:

[Pivot and Double Pivot with Ligolo-ng](https://medium.com/@alt123/pivot-double-pivot-with-ligolo-ng-df532bf213ea)

Another headache was **RDP connections**. If you don't use RDP often, you might face random errors. In one case, it was pulling credentials from `/etc/krb5.conf`. I spent hours troubleshooting it. I won't spoil the solution here, better you figure it out yourself during practice.

## Exam Reporting

For reporting, I used **SysReptor**, it's excellent and supports Markdown:

[SysReptor HTB Signup](https://htb.sysreptor.com/htb/signup)

If you want to learn how to use it, watch this video:

[SysReptor Tutorial](https://www.youtube.com/watch?v=kz8KIMagk8c)

**Important reporting tips:**

One of my friends failed CPTS even after submitting enough flags. His mistake was the **severity order** in the report. He listed findings randomly (Medium, Low, Critical, High).

Always structure your findings in this order:

**Critical &rarr; High &rarr; Medium &rarr; Low**

Another common mistake is taking weak flag screenshots. Don't just screenshot `cat flag.txt`. Follow the official guidelines, run these commands, and include them in your screenshots:

```bash
whoami
hostname
date
cat flag.txt
```

This shows context: which user, which machine, and when.

## Final Thoughts

That's pretty much my CPTS journey. It was challenging but extremely rewarding. If you have your own tips, experiences, or questions, drop them in the comments, let's help each other grow.

If you liked this blog, please give it claps, reactions, or leave a comment. It really motivates me to write more.

You can also connect with me:

- HackTheBox: [app.hackthebox.com/users/1443864](https://app.hackthebox.com/users/1443864)
- LinkedIn: [Danish Ahmed](https://www.linkedin.com/in/danish-ahmed-61927b265/)

See you in the next one. Stay hacking!

![HTB CPTS certificate, Danish Ahmed, earned 01 May 2026](images/cpts-certificate.jpeg)
