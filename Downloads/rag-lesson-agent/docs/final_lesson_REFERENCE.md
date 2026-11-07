# RAG for Beginners: How an AI Looks Things Up Before It Answers

## What is RAG?

RAG stands for Retrieval-Augmented Generation. These are big words, so let us break them into three small parts.

- **Retrieval** means finding. The system finds useful information.
- **Augmented** means added. The information is added to your question.
- **Generation** means writing. The AI writes the answer.

So RAG is a simple idea. First, the AI looks up facts. Then it writes an answer using those facts.

Think about two kinds of exams. In a closed-book exam, you answer from memory only. In an open-book exam, you can look inside your book first. RAG gives the AI an open-book exam.

A chatbot like ChatGPT or Claude is built on an LLM. LLM means Large Language Model. It is a computer program that learned to write by reading a huge amount of text.

## Why does RAG matter?

An LLM has three problems. RAG helps with all three.

First, its knowledge is old. It only knows what it read before its training ended. Training means teaching the program with a lot of text. It takes a long time and costs a lot of money. So the LLM does not know yesterday's news.

Second, it does not know your private documents. It has never seen your college rules, your company policy, or your notes.

Third, it sometimes makes up answers. This is called a hallucination. A hallucination means the AI says something false, but sounds very sure.

RAG fixes these problems in a simple way. It gives the AI the right pages at the time of the question. This brings four benefits:

- The AI can use fresh information.
- The AI can use your private documents.
- The AI makes up fewer answers, because it has real text to read.
- The AI can show which document it used, so you can check it.

To update the knowledge, you only change the documents. You do not need to teach the AI again.

## How does RAG work?

RAG has two parts. The first part is done once, before any question. The second part runs every time someone asks.

**Part 1: Prepare the knowledge (once)**

1. Collect your documents. These can be PDFs, web pages, or notes.
2. Cut each document into small pieces. A chunk means one small piece of a document, for example one paragraph.
3. Turn each chunk into numbers. A list of numbers that shows the meaning of a text is called an embedding. Chunks with similar meaning get similar numbers.
4. Save all chunks and their numbers in one place. We call this place the knowledge base.

**Part 2: Answer a question (every time)**

1. **Question.** The user asks something.
2. **Retrieve.** The system turns the question into numbers too. Then it finds the few chunks with the closest meaning.
3. **Augment.** It builds a prompt. A prompt means the message we send to the AI. Here the prompt has the question and the found chunks together.
4. **Generate.** The AI reads the prompt and writes an answer using the chunks. It can also tell you which chunk it used.

Notice one thing. The AI itself does not change. RAG does not teach the AI new things. It only puts the right pages in front of the AI at the right time.

## Example: A college helpdesk chatbot

Imagine a college wants a chatbot for students. The college has a notice that says: "Exam fee can be paid online until 15 December. After this date, a fine of 200 rupees is added." This is an imaginary notice, made for this lesson.

A student asks: "Till when can I pay my exam fee?"

**Without RAG.** The AI has never seen this notice. It may guess a date. The guess can be wrong, and the student may miss the last date.

**With RAG.** The steps are:

1. The notice was cut into chunks and saved in the knowledge base earlier.
2. The student asks the question.
3. The system finds the chunk about the exam fee, because its meaning is close to the question.
4. The system sends the question and this chunk to the AI.
5. The AI answers: "You can pay online until 15 December. After that, you must pay a fine of 200 rupees."

The answer is correct because the AI read the real notice first.

## What are the limits of RAG?

RAG is helpful, but it is not perfect.

- If the system finds the wrong chunk, the answer can be wrong.
- If the documents are wrong or old, the answer will also be wrong.
- The AI can still misread the text.
- Sending more text to the AI takes more time and money.

So for important matters, always check the source.

## Recap and quick check

- RAG means the AI looks up information first and then writes the answer.
- It helps with old knowledge, private documents, and made-up answers.
- The steps are: prepare chunks, retrieve, augment the prompt, generate.
- RAG does not change the AI. It only gives the AI the right text.

**Try yourself:**

1. In the open-book exam idea, what is the "book"? *(Answer: the knowledge base, your documents.)*
2. Which step builds the prompt? *(Answer: Augment.)*
3. A student's chatbot gives a wrong date. Name one reason. *(Answer: it found the wrong chunk, or the document was old.)*
