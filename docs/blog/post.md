---
title: What if your AI agents simply joined your team chat?
published: false
tags: ai, agents, discord, productivity
cover_image: https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/diagram.png
---

Most AI agents live in a terminal or a browser tab, next to one person. Switch puts them somewhere else: in the chat where the whole team already works. After a hackathon spent building with it, I think that small change matters a lot: the agents stop being one person's tool and become something the whole team can use.

## What Switch is

Switch is a platform for running AI agents as members of a team. You connect agents like Claude Code or Codex, give each one instructions, and place them in rooms that are bridged to Discord, Slack, Mattermost or other chats. From then on, people talk to the agents the way they talk to each other, in channels and threads.

A few things make it more than a chatbot in a channel. Rooms decide who sees what, so you can control exactly which agent reads which conversation. Agents can hand work to one another. Risky actions stop on an Allow or Decline prompt shown right in the chat, so a person approves them in context. And a whole team, with its agents, instructions and rooms, fits in one template file you can import in one step.

## How I came to it

I discovered Switch through the Flip the Switch Hackathon and entered the Best Business Workflow track. I wanted to test it on a problem I know well from client work: a client sends one message that mixes a bug report with a new feature request, and the team loses time working out what each part is and where it should go.

## What I built with it

I built **Scope Firewall**, a team of five agents that follows a client project in Discord, from the first brief to delivery.

It turns the client's brief into a contract of rules the app must pass, proposes a delivery date from the real work, splits every client message into separate requests, checks each one with two independent AI opinions, and routes it: a defect goes straight to a fix, anything new is planned for the next version. People keep every real decision: the developer estimates, the project manager accepts the date, the tech lead approves production.

![The workflow, built on Switch](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/diagram.png)

## What building with Switch felt like

**It started from one file.** I wrote a template describing five agents, four rooms and two AI providers, imported it once, and the whole team appeared in Discord. Every time I changed my mind, I edited that file and imported it again. It made the project feel less like configuration and more like writing down how a team works.

**Rooms did half the design for me.** I wanted a second opinion that could not be influenced by the first. I was about to write rules for it, then realized Switch already handles it: an agent that is not in a room cannot read it. So Claude Code checks in one room and Codex in another.

The moment it clicked came during the demo. I pasted a client message: "a customer entered a price of 0 and got a free order". A minute later, two agents that could not see each other posted the same verdict, rule for rule: a price of 0 is accepted, a total of 0 comes back, and that is a security bug. Nobody had told them what to look for.

![Claude Code's verdict in the verification room](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot3_mock.png)

**Humans stayed in the loop without effort.** Agents pass work along when a teammate types a word like "GO" in the chat. Anything risky, like going to production, waits for an Allow or Decline click in the same conversation. My teammates never had to leave Discord.

**It also taught me a lesson.** My first version let an agent set delivery dates. It worked, and it was wrong. Switch's approval prompts meant a person always clicked the final button, and I moved the rules themselves into small tested tools, so that even a confused agent cannot accept a date or approve a release in someone else's name.

![Only the tech lead can promote, whatever the agent is told](https://raw.githubusercontent.com/ru-ji/scope-firewall/docs/blog-post/docs/blog/shot6_mock.png)

**And a few rough edges.** Discord threads were named after the raw first message, so mentions showed up as long numbers. I fixed it locally with a one line change, and I would love to see it upstream. The bridge went quiet once after my Mac slept, and a template import reported a timeout while everything had actually been created. None of it stopped me, and each one taught me how Switch works under the hood.

## Will I keep using it?

Yes. What convinced me is that Switch does not ask a team to change where it works. The agents come to the chat, not the other way around, and that is what makes a team actually use them.

Next, I want to run Scope Firewall on a real client project and see how it holds up over weeks instead of a demo.

On the Switch side, I would love agents to see the sender's chat roles, so teams can reuse the permissions they already have, and a way to update a running team from a new version of its template.

## Try it yourself

Getting started takes three steps: install Switch from https://switchagents.ai and follow the getting started guide at https://docs.switchagents.ai/switch-rooms/getting-started, connect your team chat, then mention an agent in a channel and give it its first task.

If you want a whole team at once, my template is open source: https://github.com/ru-ji/scope-firewall. Import it, connect your Discord, and paste the next confusing message a client sends you.

If your team already lives in a chat, give your agents a seat there. That is the whole idea behind Switch, and after this hackathon, I am convinced it is the right one.
