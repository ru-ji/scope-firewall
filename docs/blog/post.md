---
title: What I learned building a client project team of AI agents on Switch
published: false
tags: ai, agents, discord, productivity
cover_image: https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/diagram.png
---

I gave myself one rule for this hackathon: build something a real agency could use on Monday morning. Not a chatbot, a team.

The pain I picked is one every freelancer knows. A client writes "a customer got a free order, and while you are at it, add a PDF export". One message, two requests: a bug we owe them for free, and new work they should pay for. Mixed together, the feature slips in for free and the deadline becomes a guess.

So I spent the hackathon building a small team of AI agents that lives in our Discord and runs a client project from kickoff to delivery. Here is how it went, what Switch made easy, and where I got stuck.

![The workflow I ended up with](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/diagram.png)

## Starting from one file

The first thing that clicked was the template. In Switch, one YAML file describes the agents, their instructions and the rooms they live in. I imported it and five agents and four Discord channels appeared at once.

That changed how I worked. Every time I wanted to change the team, I edited one file and imported it again. By the end, the whole architecture of the project was readable in that single template, which is also what the next agency would import for their own client.

## Rooms turned out to be the architecture

I wanted a second opinion on every bug that could not be biased by the first one. My first instinct was to write rules telling the second agent "do not read the first agent's answer". Then I realized Switch already solved it: if the second agent is simply not in the first agent's room, it cannot read it.

So the Verifier runs on Claude Code in one room, and the Contradictor runs on Codex in another. Same request, two providers, no way to copy. The day they both found the same security hole on their own, I knew the design was right.

![The Verifier's verdict, backed by a real run of the contract](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot3_mock.png)

## Teaching agents to pass the work along

Agents talking to each other was the part I feared most. In practice it was two words typed in the chat. "GO" tells Reception to hand a request to both rooms. "COMPARE" tells the Planner to read both rooms and decide.

What I like is that the humans stay in charge of the rhythm. Nothing moves until a teammate says so, and everything that moves is visible in the channel.

## Approvals where the team already is

Some steps must never happen on their own: resetting a project, going to production. Switch shows an Allow or Decline prompt right in the chat for those. I only had to mark which commands are risky, and every one of them now stops and waits for a person.

## The lesson I did not expect: prompts are not safeguards

My first version let the Planner set delivery dates. It worked, and it was wrong. An AI should not promise a date to a client.

So I moved every decision into small tested scripts. A script computes the date from the real work: build, then test and confirm, one item at a time, on working days only. A developer corrects an estimate, and only the project manager can accept the date. A team file says who may do what, and the scripts refuse anyone else, whatever the prompt says.

![A developer corrects the estimate, the project manager accepts the date](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot1_mock.png)

When someone said "the developer approved the release", the Planner answered that only the tech lead can promote. That was not the model being clever. It was the tool saying no.

![A developer's approval does not count](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot6_mock.png)

## Where I got stuck

**Thread names.** Discord threads were named after the raw first message, so a mention showed up as a long number. The fix is one line in the Discord bridge: use Discord's clean text instead. I patched it locally and I hope it lands upstream.

**One account, many roles.** To film a developer and a project manager disagreeing, I needed two people. I used a Discord webhook to play the developer, and Switch bridged its messages like any teammate's.

**Small rough edges.** The Mac went to sleep and the bridge stopped listening until I restarted the server. A template import reported a timeout although everything had been created. OpenCode was refused as a provider, so I stayed with Claude Code and Codex.

None of these stopped me for long, and each one taught me how Switch is put together.

## What I would love Switch to do next

Pass the sender's Discord roles to the agents, so teams can reuse the permissions they already have. Let a running team update from a new version of its template without being deleted and imported again. And ship the thread name fix.

## Try it

Demo video (2 minutes): **[VIDEO LINK]**
Code and setup: https://github.com/ru-ji/scope-firewall

If you run a client project, import the template, point it at your Discord, and paste the next confusing client message you get. Bugs stay free, features get quoted, and every date comes from real work.
