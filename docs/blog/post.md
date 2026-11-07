---
title: Bugs stay free, features get quoted: running a client project from the team chat
published: false
tags: ai, agents, productivity, devops
cover_image: https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/diagram.png
---

Every agency has received this message:

> "A customer entered a price of 0 and got a free order. And while you are at it, please add a PDF export of our orders."

Two requests in one breath. The first one is our bug: the app breaks a rule we agreed on, so we fix it for free, and fast. The second one is new work: it was never in the contract, so it deserves a quote and a place in the next version.

When the two arrive together, teams lose twice. The feature slips in for free while the real bug waits. Then the delivery date turns out to be a guess, nobody counted the testing time, and when something unexpected happens the client hears about it last.

So for the Flip the Switch Hackathon I built **Scope Firewall**: a small team of AI agents on Switch that runs a client project from kickoff to delivery, right inside the team's Discord. The agents do the legwork. People make the decisions.

![How Scope Firewall works](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/diagram.png)

## The team

One Switch template creates five agents and four rooms.

**Reception** reads client messages. It has no access to the code, on purpose: a client's words can never steer an agent that holds the repository.
**The Verifier** runs on Claude Code and checks each request against the signed contract.
**The Contradictor** runs on Codex and does the same check, blind, in another room.
**The Planner** turns confirmed verdicts into a plan, quotes and dates.
**The Fixer** builds the fixes through pull requests.

## One project, start to finish

### 1. The contract comes first

A teammate pastes the client brief. The Planner turns it into rules the app must pass, like "a price of 0 or less is refused". It asks about anything the brief leaves open, then a named person signs. From that moment the contract is frozen, and it settles every future argument about what is a bug and what is new work.

### 2. Dates come from real work

This is the part I care about most. The Planner never invents a date. A small tool proposes one: each item is built, then tested and confirmed working before the next one starts, counting working days only.

Then the developer steps in: "F5 is bigger than you think, it touches the validation and its tests." The date moves from November 10 to November 13, skipping the November 11 holiday. The project manager accepts, and only then does it become a promise to the client.

![The developer corrects an estimate, the project manager accepts the date](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot1.png)

### 3. One message becomes two requests

Reception splits the client's message into two sheets, one for the free order and one for the PDF export, and drafts the questions to send back.

![Reception splits the message](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot2.png)

### 4. Two opinions that cannot copy each other

On "GO", each sheet goes to the Verifier and the Contradictor, in separate rooms. Neither can read the other's reasoning. Both run the contract against the real app and reach the same answer on their own: a price of 0 gives a total of 0, and a price of minus 10 gives a negative total. That is a security bug.

![The Verifier's verdict, backed by the contract run](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot3.png)

### 5. The plan, the quote and an honest delay

On "COMPARE", the Planner reads both rooms. They agree, so the free order becomes a hotfix and the PDF export becomes a quote for version 1.1. The hotfix pulls the developer away from the main release, so the Planner proposes a one day delay and waits. Only the project manager can accept it.

![Hotfix, quote and a proposed delay](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot4.png)

### 6. When the unexpected happens

The payment provider's sandbox goes down until Wednesday. The project manager types one line, the date moves two working days, and the client update says it plainly: what is free, what is billed, and every date with the reason it moved.

![The client update carries every date and its reason](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot5.png)

### 7. Delivery with the right people

Staging gets deployed. Someone says the developer approved going to production. The Planner refuses: only the tech lead can do that. When the tech lead insists, Switch shows an Allow or Decline prompt in the chat. We decline, because a security rule still fails, and production stays untouched.

![A developer's approval does not count](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot6.png)

## Humans decide, tools check

One rule guided the whole build: **an AI never makes a decision that belongs to a person, and a prompt is never the only safeguard.**

Every decision goes through a small tested script, not a model's opinion. One script runs the contract against the app. One compares the two verdicts. One computes dates. A simple team file says who may do what, so if an agent tries to accept a date in the developer's name, the tool says no, whatever the prompt said.

## Why Switch made this easy

Most of this design is Switch, not code I had to write.

**Rooms** made the second opinion truly blind: the Contradictor is simply not in the Verifier's room.
**Two providers in one team** means Claude Code and Codex do not share the same blind spots.
**Addressing rules** let anyone talk to Reception while the other agents answer only their owner.
**Handoffs between agents** carry each sheet into both rooms and bring both verdicts back.
**Approvals in the chat** stop every risky command until a person clicks Allow.
**Templates** recreate the whole team for the next client in one import.

## What I would love Switch to do next

Discord threads are named from the raw first message, so a mention shows up as a long number. Discord already offers a clean version of the text, and using it is a one line change. I patched it locally for the demo.

Agents cannot see the sender's Discord roles yet, so I enforce roles in my own tools. Passing them along would let teams reuse the permissions they already have.

Updating a running team from a new version of its template still means deleting it and importing it again.

## Try it

The demo video (2 minutes): **[VIDEO LINK]**
The code, with setup in the README: https://github.com/ru-ji/scope-firewall

You can run the core in two minutes with nothing but Python, then import the template into Switch and point it at your own Discord or Mattermost.

Bugs stay free, features get quoted, every date comes from real work, and the chat keeps the record.
