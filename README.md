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

# Image Attachments

You can include images in your questions and answers. To add an image, use the following syntax in your question or answer text:

```
[IMAGE_WORD](image_filename.jpg)
```

The `image_filename.jpg` should be the name of the image file located anywhere within the `images` folder or its subdirectories in your question set. The system will search for the image file, attach it to the email, and replace the tag with an inline image in the email content.

For example, if you have an image file `question_sets/machine_learning/images/diagrams/decision_boundary.png`, you can reference it in your question or answer like this:

```
What is a decision boundary in machine learning?

A decision boundary is the line or surface that separates different classes in a classification problem. Here's an example:

[IMAGE_WORD](decision_boundary.png)

As you can see in the image, the decision boundary (red line) separates the two classes (blue and green points).
```

Make sure that the image files exist somewhere within the `images` folder or its subdirectories in your question set. If an image is not found, a warning will be printed, and the email will be sent without that image.