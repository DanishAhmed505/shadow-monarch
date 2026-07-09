Title: Chaining Leaks to Unauthenticated Database Access: A Collaborative Bug Hunt
Subtitle: How a rejected metrics leak turned into unauthenticated access to a production MongoDB
Date: 2025-09-24
Tags: auth bypass, information disclosure, bug bounty
Reward: 200 EUR
Banner: images/db-access-200-reward.webp

So... guess what?

We actually got access to a production MongoDB instance.

(Yeah, my heart dropped too when I realized it 😅)

But hold up. This wasn't one of those flashy, overnight hacker stories where you find a critical in 2 clicks. Nah.

This was a journey of rejections, persistence, and teamwork.

And here's the story of how me (Danish Ahmed 👋) and Ayesha Attaria turned a "meh" report into a valid medium severity finding.

## The Initial Discovery: A Leaky Metrics Endpoint

Our hunt began with a simple observation, an exposed endpoint at:

`/actuator/prometheus`

This endpoint was leaking critical system metrics, including:

- Heap and memory addresses
- Internal hostnames and configurations
- Other sensitive runtime data

While these kinds of leaks can aid in memory corruption exploits or infrastructure mapping, the program's policy on YesWeHack was clear: pure information disclosures were out of scope unless chained into something more impactful.

We submitted the report on July 28, 2025, but it was marked **Rejected, Read the Fine Scope (RFS)**. Instead of walking away, we decided to dig deeper.

## Chaining the Leak: Uncovering an Internal Subdomain

Among the metrics exposed, we spotted an internal subdomain mention: `prod-db00.[target].io`. Importantly, this subdomain fell within the program's in scope assets, making it fair game for further testing.

A quick browser check over HTTP and HTTPS yielded nothing, no web servers were listening. Time to probe further.

Using Nmap, we scanned the host and saw two familiar ports wide open:

- `27019` &rarr; MongoDB primary replica
- `27018` &rarr; MongoDB secondary replica

Could this be an exposed database?

## Proof of Concept: Unauthenticated MongoDB Access

**1. Connect to the primary instance (port 27019):**

```
mongo "mongodb://prod-db00.[target].io:27019"
```

Success. Connected to MongoDB 4.4.11 without credentials. We switched to the admin database and ran a few checks:

```
use admin
show dbs
db.runCommand({ connectionStatus: 1 })
db.runCommand({ buildInfo: 1 })
```

The output confirmed no authentication was enforced and the full server build info was exposed:

```
rs01:PRIMARY> db.runCommand({ connectionStatus: 1 })
{
  "authInfo": {
    "authenticatedUsers": [],
    "authenticatedUserRoles": []
  },
  "ok": 1
}
```

**2. Connect to the secondary instance (port 27018):**

```
mongo "mongodb://prod-db00.[target].io:27018"
```

Again, unauthenticated access. Some commands (like `buildInfo`) were blocked by replica restrictions, but the connection itself was proof of exposure:

```
rs01:SECONDARY> db.runCommand({ connectionStatus: 1 })
{
  "authInfo": {
    "authenticatedUsers": [],
    "authenticatedUserRoles": []
  },
  "ok": 1
}
```

## The Outcome

We reported the chained finding as **critical**. After 14 days, they downgraded it from critical to medium and rewarded us a **200 € bounty**.

![YesWeHack 200 EUR medium severity reward for improper authentication (CWE-287)](images/db-access-200-reward.webp)

## Final Thoughts

Bug bounty isn't easy. Behind every accepted report are many rejections, duplicates, and dead ends that nobody sees. From the outside, people only notice the success, not the hard work and failures behind it.

In this case, what looked like a small metrics leak turned into something much bigger: unauthenticated access to a database. The only reason we got there was because we didn't stop after the first rejection.

The lesson? Always stay curious, keep digging, and don't give up too early. Sometimes the real bounty is just one step further.

📌 Connect with us on LinkedIn: [Danish Ahmed](https://www.linkedin.com/in/danish-ahmed-61927b265/) &middot; [Ayesha Attaria](https://www.linkedin.com/in/ayeshaattaria-penetrationtester/)
