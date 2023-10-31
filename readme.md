# Chat'o'Lantern
Chat'o'Lantern is an AI trapped inside of a pumpkin! It listens to you and responds in unique ways. No audio is hardcoded - everything you hear is created on-the-fly.

When you press the button, the pumpkin begins recording your voice. The audio is transcribed by Google Text To Speech.
Your transcription and a system prompt is passed to GPT-4 (ChatGPT), which formulates the response.
The response is processed by a voice generation service called Coqui.ai, which creates the audio for the two personas. The audio is downloaded and played back through the speakers.

The AI prompt instructs GPT to pretend it is an Artificial Intelligence trapped inside a pumpkin. It also instructs it to take on both a benevolent and malevolent persona, as if the two are fighting eachother internally. 

Depending on the persona and the state of the system, the LEDs take on different patterns and colors and illuminate through eyes and a mouth in the pumpkin.