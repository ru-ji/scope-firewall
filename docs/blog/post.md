---
title: What if your AI agents simply joined your team chat?
published: false
tags: ai, agents, discord, productivity
cover_image: https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/diagram.png
---

Most AI agents live in a terminal or a browser tab, next to one person. Switch puts them somewhere else: in the chat where the whole team already works. After a hackathon spent building with it, I think that small change matters more than it sounds.

## What Switch is

Switch is a platform for running AI agents as members of a team. You connect agents like Claude Code or Codex, give each one instructions, and place them in rooms that are bridged to Discord, Slack, Mattermost or other chats. From then on, people talk to the agents the way they talk to each other, in channels and threads.

A few things make it more than a chatbot in a channel. Rooms decide who sees what, so you can control exactly which agent reads which conversation. Agents can hand work to one another. Risky actions stop on an Allow or Decline prompt shown right in the chat, so a person approves them in context. And a whole team, agents, instructions and rooms included, fits in one template file you can import in one step.

## How I came to it

I discovered Switch through the Flip the Switch Hackathon and entered the Best Business Workflow track. I wanted to test it on a problem I know well from client work: a client sends one message that mixes a bug report with a new feature request, and the team loses time sorting out what is owed for free and what should be billed.

## What I built with it

I built **Scope Firewall**, a team of five agents that follows a client project in Discord, from the first brief to delivery.

It turns the client's brief into a contract of rules the app must pass, proposes a delivery date from the real work, splits every client message into separate requests, checks each one with two independent AI opinions, and sorts it into a free fix or a paid quote. People keep every real decision: the developer estimates, the project manager accepts the date, the tech lead approves production.

![The workflow, built on Switch](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/diagram.png)

## What building with Switch felt like

**It started from one file.** I wrote a template describing the five agents and four rooms, imported it, and the whole team appeared in Discord. Every time I changed my mind, I edited that file and imported it again. It made the project feel less like configuration and more like writing down how a team works.

**Rooms did half the design for me.** I wanted a second opinion that could not be influenced by the first. I was about to write rules for it, then realized Switch already handles it: an agent that is not in a room cannot read it. So Claude Code checks in one room and Codex in another. The day both found the same bug on their own, I knew the idea held.

![Claude Code's verdict in the verification room](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot3_mock.png)

**Humans stayed in the loop without effort.** Agents pass work along when a teammate types a word like "GO" in the chat. Anything risky, like going to production, waits for an Allow or Decline click in the same conversation. My teammates never had to leave Discord.

**It also taught me a lesson.** My first version let an agent set delivery dates. It worked, and it was wrong. Switch made it easy to keep decisions with people, and I moved the rules themselves into small tested tools, so that even a confused agent cannot accept a date or approve a release in someone else's name.

![Only the tech lead can promote, whatever the agent is told](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot6_mock.png)

**And a few rough edges.** Discord threads were named after the raw first message, so mentions showed up as long numbers, which a one line change in the bridge fixed. The bridge went quiet once after my Mac slept, and a template import reported a timeout while everything had actually been created. None of it stopped me for long, and the platform is young enough that I expect these to disappear quickly.

## Will I keep using it?

Yes. What convinced me is that Switch does not ask a team to change where it works. The agents come to the chat, not the other way around, and that is the part most AI tools get wrong.

Next, I want to run Scope Firewall on a real client project and see how it holds up over weeks instead of a demo. I would also like to connect it to the team's real calendar and issue tracker, and build a second template for code reviews, where one agent reviews and another, on a different provider, challenges the review.

On the Switch side, I would love agents to see the sender's chat roles, so teams can reuse the permissions they already have, and a way to update a running team from a new version of its template.

## Try it yourself

Scope Firewall, with setup instructions: https://github.com/ru-ji/scope-firewall

If your team already lives in a chat, try giving your agents a seat there. That is the whole idea behind Switch, and after this hackathon, I am convinced it is the right one.
