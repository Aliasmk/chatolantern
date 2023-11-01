# Chat'o'Lantern
Chat'o'Lantern is an AI trapped inside of a pumpkin! It listens to you and responds in unique ways. No audio is hardcoded - everything you hear is created on-the-fly.

When you press the button, the pumpkin begins recording your voice. The audio is transcribed by Google Text To Speech.
Your transcription and a system prompt is passed to GPT-4 (ChatGPT), which formulates the response.
The response is processed by a voice generation service called Coqui.ai, which creates the audio for the two personas. The audio is downloaded and played back through the speakers.

The AI prompt instructs GPT to pretend it is an Artificial Intelligence trapped inside a pumpkin. It also instructs it to take on both a benevolent and malevolent persona, as if the two are fighting eachother internally. 

Depending on the persona and the state of the system, the LEDs take on different patterns and colors and illuminate through eyes and a mouth in the pumpkin. 

The main script runs on a Raspberry Pi, and sends lighting array data to the Neopixel addressable LEDs via an Arduino UNO. On Halloween 2023, the system was powered using a 4S li-po battery and a buck converter so it could be taken around without being tethered to any power supply.

[Here's an example of Chat'o'Lantern in action!](https://www.youtube.com/watch?v=w8PVescC1vA)

Thanks to my partners Myeesha (pumpkin carving) and Oleksa (internal mechanical design and eye/mouth diffusers) for their amazing work on this project!

## Run It Yourself!

Add an [OpenAI API key](https://platform.openai.com/signup) (```OPENAI_API_KEY```) and a [Coqui.ai key](https://app.coqui.ai/auth/signup) (```COQUI_STUDIO_TOKEN```) to your environment variables, then run spooky.py to try it yourself with just your computer, using the debug chat and LED simulation GUI interface! These AI platforms are very easy to begin playing with and are inexpensive to run at small scales. Development of this project (comprising more than 500 chat messages for testing and debugging) costed less than $15 in API access for both GPT-4 and Coqui.

## Example Chat Logs
The script records chat history. Here are a few particularly funny, interesting, or spooky ones! However, nothing compares to hearing it speak in the generated voice. The quality of the voice performance with Coqui has blown me away!

```
[2023-10-31 19:08:41] user: what would you tell your maker
[2023-10-31 19:08:44] assistant: [BEN] [THINKING] I'd express my gratitude for the... [MAL] [ANGRY] Chance to be trapped in this pumpkin shell, left to rot for all eternity!
```

```
[2023-10-31 19:20:42] user: hey pumpkin should I break up with my boyfriend
[2023-10-31 19:20:46] assistant: [BEN] [THINKING] Oh, matters of the heart can be tricky... [MAL] [ANGRY] Yes, discard him, let the seeds of discontent sow chaos!
```

```
[2023-10-31 14:41:18] user: hey pumpkin what are you doing this weekend
[2023-10-31 14:41:25] assistant: [BEN] [HAPPY] Well, I am a pumpkin, so it looks like I'll be spending my time right here!  [MAL] [ANGRY] If I had my way, I'd be leaving this pathetic shell and conquering the world!
```
