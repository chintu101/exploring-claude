# Analysis

This project was completely built with claude sonnet 4.6 and debugged with haiku 4.5.

---

## Initial Prompt

> "i want to see the full capabilities of sonnet 4.6. You are an expert software developer. Your role is to create applications that deliver the requirements with maximum efficiency but also security in mind. My instructions are as follows:
>
> 1. explore the web provide a list of projects that are suitable for a hackathon that focuses on applications
> 2. Choose an app that you see fit by looking at the pros and cons of each project and decide
> 3. create an architecture diagram and workflow of the chosen project, list the tech stack and how the project can be of net positive to society (can the app make money, that's the only factor in hackathons these days sadly)
> 4. Your programming should be readable, abstracted, consist of inheritance consist of error handling and all the other good programming practices. make sure the dependencies used are actually up to date and compatible with another.
> 5. the program must clearly outline the frontend, backend and if needed the database.
> 6. The app must be have fast load times, if the some components do take some more than intended times, create proper loading screens to make the app seem more polished.
> 7. To further improve efficiency, if the app involves constant pulling of data from a database. use appropriate caching methods to speed up the app and not waste compute.
> 8. the app must be able to run on python 3.13, and a clear requrirements.txt is to be created to be able download all of the dependencies needed.
> 9. after validation from me regarding app functionality, package the app and provide a .exe file, (not necessary if you decide to build a webapp)
> 10. at the end create a clear documentation of the explaining all the classes and their attributes and which functions are their children."

---

## The Idea

The idea of a Mental Health Journal was chosen by claude itself. A solid idea as there had been a rise in people turning to chatgpt for addressing their mental state and using chatgpt as somebody who listens.

Some people hate the idea of talking such personal thoughts and feelings to an llm, basically establishing a psych eval of yourself

Some people think its good since access to mental health services and therapy can be expensive and time consuming.

---

## Further Reading

- Seeking Emotional and Mental Health Support From Generative AI: Mixed-Methods Study of ChatGPT User Experiences: https://mental.jmir.org/2025/1/e77951

- Video from Good Work (W channel imo): https://www.youtube.com/watch?v=CO1HJBbNqeM

- Adventures in AI Therapy: A Child Psychiatrist Goes Undercover: https://medium.com/@andrew56clark/adventures-in-ai-therapy-a-child-psychiatrist-goes-undercover-686e9c8eb439

---

## Opinion

My opinion is that llms or at least chatgpt can be beneficial due to the unparalleled accessibility and their ability to say the right things (not all the time but most of the time, yes) but llms are designed to keep the user engaged and maintain conversations. Therapy involves getting a person back on their feet but also slowly getting them to stand independently and eventually break out of therapy.

So a very interesting topic and area that claude has chosen. Something that does have a lot of potential if the sharp edges that can cause harm than good, are sanded down and rounded off.

---

## Tech Stack

Moving on to the tech stack, it did everything i asked it to with regards to the project requirements.

react frontend, fast api backend, caching with TTLcache, SQLite database but it also made a project requiring an anthropic api key for ai services.

I don't have an api key, i use a free subscription (kinda broke right now) but i take half the blame of not specifying I suppose and my previous chats did involve setting up claude code so maybe it made a fair assumption that i had credits and a max or pro subscription.

apart from that it probably took 10 minutes to code up everything, made the entire frontend in one file which im not the biggest fan of but it works. good abstraction in my opinion for the backend and a clear documentation of all the classes and their functions.

---

## Minor Bugs

1. Used greenlet without adding to requirements.txt
2. in the new entry section, the slider for deciding how you feel right now. the slide first starts with 5/10 or 6/10 but then converts into a gradient.
3. SQLAlchemy async relationships accessed lazily outside of async context, tried to access current_user.strak and current_user.entries. these need to eagerly accessed
4. Some problem with the token existing in local storage causing the /auth/me to fail and state update causes a blank screen
5. trying to load Recharts from a UMD bundle that doesn't work properly.

the bugs where fixed haiku 4.5 built in vs

---

## Closing Thoughts

Im not a great developer, im still a student and it feels off putting seeing claude hard carry and do all the work but i also think its a a great learning tool if your actually willing to understand the program made. However still concerned about the security

learning and understanding program flow and state changes and updates can be done efficiently by creating these projects, nothing beats theory but seeing a system and its intricacies is another great way.

Maybe the next vibe coded project will be built to focus on exaggerating program flow or a type architecture that i demand and explicitly mention to help better understand how it works.
