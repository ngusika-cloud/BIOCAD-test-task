i want to make some refinfer to the service
1. write in the prompt to write shorter responses
2. The planning agent exceeded its tool-call limit – i want this problem to disappear. if many tool calls needed than solve it with better way.
3. also it should be possible and mentioned in prompts that we can add or delete the prticular people from the task executors, so nopt onloy one person can execute the task

The “Roadmap to Production” document outlines what needs to be improved to bring the solution to a production‑ready state: technical debt deliberately left behind, what is missing for production, risks, and the order of closure.
Ideas for what to add:
1. This is a prototype. We cannot add new team members; we have a limited data schema; we don’t have personalization for worked hours — any employee is considered to work 8 hours a day, and so on.
2. For the finished product, it is necessary to consider scalability across many of the company’s projects — for example, so that there is no need to repeatedly generate the creation of similar tasks, and so on.
3. For the finished product, it is necessary to address the issue of solution security. On the one hand, there are currently no strict checks on user interaction with agents. An additional safety layer is needed. On the other hand, the company’s data security, including the use of external AI models, must be ensured.
4. The solution must be optimal.
We are using the qwen/qwen3.7-flash model, but it would be better to collect data for our own benchmark and select the best model based on the price‑to‑quality ratio for our tasks and data. It’s better to use a non‑React agent.

You can also review the thoughts you’ve already written in the Roadmap to production file.
You also need to think through the closure procedure: the economics, planned costs, and so on. Imagine you’re a product owner and you’re writing a closure plan for the company’s CFO.

i want to make some refinfer to the Roadmap to Production
1. Biocad is russian company, they more than 3000 workers. So you should write salary in rubles, write in dollars only cost for services like price of token, render adn so on
2. write also that render is fast instrument to make this tech task, if we speak about prod we should change thos service to biocad hosting
3. About safety write that we should integrte companys way to sign in and follow rules that the copmany is using to defend of risks in safety
4. The numbers of salary and cost of making something is too big, also comand that you write we need is too big. Make it smaller we need product manager, full stack AI native developer - for all time and designer, devops and maybe QA only in some episod
