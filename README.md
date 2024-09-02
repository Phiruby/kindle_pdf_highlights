# What is this?
This is a program that reads your kindle highlights, generates questions and answers based on the highlights and emails few questions and answers to you.

# How to use?

1. Clone the repository
2. Install the dependencies
3. Run the program

# Setting up the environment variables
Checkout .env.example and create a new file .env with the required variables.

If you are planning to run a CRON job, modify ```config.py``` so that the paths are exact

# Running the program

First, run the question generation pipeline to extract highlights from your kindle (make sure your kindle is connected via USB):
```
python generate_questions.py
```

This will generate a file called ```highlight_cache.json``` and ```processed_highlights.json``` in the same directory as ```config.py```

Now, generate the questions with the OpenAI API (gpt-4o-mini in this case):
```
python question_generation.py
```

This will generate a file called ```generated_questions.json``` in the same directory as ```config.py```

Finally, you can run the following command to send the questions to your email (if you want to run a cron job, this is the command you should run):
```
python pick_and_email_questions.py
```

This will send an email to the address specified in the .env file with the questions and answers.
