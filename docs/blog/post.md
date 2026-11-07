---
title: How I built an AI team that runs client projects from Discord, with Switch
published: false
tags: ai, agents, discord, productivity
cover_image: https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/diagram.png
---

Every freelancer has received this message:

> "A customer entered a price of 0 and got a free order. And while you are at it, please add a PDF export of our orders."

One message, two very different requests. The first is a bug: the app breaks what we agreed on, so we owe the fix, for free. The second is new work: it deserves a quote. When they arrive mixed, the new feature slips in for free, the real bug waits behind it, and the delivery date quietly becomes a guess.

For the Flip the Switch Hackathon, I built something to stop that.

## What Scope Firewall is

Scope Firewall is a small team of AI agents that lives in the team's Discord and follows a client project from kickoff to delivery.

At kickoff, it turns the client's brief into a contract of rules the app must pass, and proposes a delivery date based on the real work. Then, every time the client writes, it splits the message into separate requests, checks each one against the contract with two independent AI opinions, and sorts it: a free fix if we broke a rule, a paid quote if it is new. Dates move only with a reason, and the client gets a clear update.

The important part is who decides. The agents do the legwork, but every decision that matters belongs to a named person: the developer estimates, the project manager accepts the date, the tech lead approves production.

![The whole workflow](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/diagram.png)

## What it looks like in practice

In the demo, the client brief comes in, the Planner turns it into rules and proposes a date. The developer replies that one item is bigger than expected, the date moves past a public holiday, and the project manager accepts it.

![A developer corrects the estimate, the project manager accepts the date](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot1_mock.png)

Then the client sends the mixed message above. Two agents running on two different AI providers check it separately, and both find the same thing: the free order is a security bug. It becomes a hotfix, the PDF export becomes a quote, and the release date moves by one day, with the reason written down.

None of this needed a new app. It all happens in Discord, and that is where Switch comes in.

## How I built it with Switch

Switch lets AI agents like Claude Code and Codex work inside a team chat, with rooms, permissions and approvals. Four of its features ended up shaping the whole design.

**One template for the whole team.** A single YAML file describes the five agents, their instructions and the four rooms they work in. One import, and the team appears in Discord. Whenever I changed the design, I edited that file and imported it again, and the next agency can reuse it as is.

**Rooms as a wall.** I wanted the second opinion to be truly independent. My first idea was to tell the second agent not to read the first one's answer. Then I realized I did not need to: if the Contradictor is not in the Verifier's room, it simply cannot see it. Claude Code verifies in one room, Codex checks in another, and the day they found the same bug on their own, I knew the design worked.

![The Verifier's verdict, backed by a real run of the contract](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot3_mock.png)

**Handoffs in plain words.** I expected agents talking to each other to be the hard part. It turned out to be two words typed by a teammate: "GO" sends a request to both rooms, "COMPARE" asks the Planner to read both verdicts. Nothing moves until a person says so.

**Approvals in the chat.** Resetting a project or going to production must never happen on its own. Switch shows an Allow or Decline prompt right in the conversation, so the person who approves is looking at the same context as the agents.

## The lesson I did not expect

Building this, my biggest lesson was not about agents at all. My first version let the Planner set delivery dates, and it worked. It was still wrong: an AI should not promise a date to a client.

So I moved every real decision out of the prompts and into small tested scripts. One computes dates from the work, counting build, tests and confirmation, one item at a time, on working days only. Another checks who is allowed to do what. When someone claimed "the developer approved the release", the Planner refused, because only the tech lead can promote. That was not the model being clever. It was the tool saying no.

![A developer's approval does not count](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot6_mock.png)

## Where I got stuck

Not everything went smoothly, and each problem taught me something about how Switch works.

Discord threads were named after the raw first message, so mentions showed up as long numbers. The fix was a single line in the Discord bridge, which I patched locally. To film a developer and a project manager disagreeing with only one account, I used a Discord webhook to play the developer, and Switch treated it like any teammate. The bridge also stopped listening once after my Mac went to sleep, a template import reported a timeout although everything had been created, and OpenCode was refused as a provider, so I stayed with Claude Code and Codex.

## What I would love Switch to do next

Pass the sender's Discord roles to the agents, so teams can reuse the permissions they already have. Let a running team update from a new version of its template without starting over. And ship that thread name fix.

## Try it

Demo video (2 minutes): **[VIDEO LINK]**
Code and setup: https://github.com/ru-ji/scope-firewall

Import the template, connect your Discord, and paste the next confusing message a client sends you. Bugs stay free, features get quoted, and every date comes from real work.
