The Idea:
    The Robot consists of an ESP32P4 dev Kit as the main controller, and another ESP32 for the movement.
    A laptop or another PC should run software to detect faces from the Robot's webcam stream, and use AI Agents (based on OLLAMA) to make decisions and talk to persons. The video feed from the webcam stream is continuously analyzed for objects and faces. The Agent should use this information to interact like a human.

Features:
    The Robot is 2-wheeled and balances the whole time. It has two arms with small grippers to grab tiny things. The arms are connected to two servos each in the shoulder. It has many sensors, like pressure sensors inside the arms, an IMU sensor for balancing, a camera, and maybe NFC. Some distance sensors should be added too, such as lidar.

    It gets a display inside its head (which can be rotated and moved up/down) and a few tiny WS2812 LEDs to indicate thinking processes, etc. It should be used with a changeable battery from a powertool. The robot has a built-in speaker, which can play files sent over by the laptop.


Modes:
    Play:
        The robot should search for people and wants to play. It looks for things lying around to give them, and likes to make jokes.
    Assist:
        The robot asks to help people, makes notes, sets timers, etc. It can do research too.
    Explore:
        The robot drives around and searches for new things. It makes a gallery of beautiful things, which can be shown on the PC.
    Auto:
        The robot is completely free in its decisions and can behave how it wants to, experimental.
    Idle:
        The robot waits for something to do. The mode can be set via WebSocket, and it is listening and looking for people to get further information.


PC:
    The PC / Laptop should be able to save images from the video stream. The Agent can be adjusted every time and gets a mind. The Agent has to be as intelligent as possible. The Agent has some tools, which it should / can use. For example Research, Motion, etc.
    It should be able to add tasks or timers to be executed in the future, and should handle tasks itself. It should have the Mode as the main goal, but decides the next actions depending on the short tasks.

    The Laptop should run all these things offline, so it can be used with the robot without an Ethernet connection. Of course Research is not possible without it, but overall everything beside that should work offline. Even the LLM and tools.

    The PC is connected with the ESP32P4 via WIFI. It can be a direct connection, or via an existing Wifi, to increase the distance, so it can run inside bigger homes, for example.


AI Agent:
    Tools:
        Movements:
            Should control the direction the Robot is moving, as well as its speed.
            It can control the arms and the head joints as well.
        Research:
            If it has a connection to the Internet, it can do some research. It can use the whole Internet, but some websites are preferred, for example Wikipedia, or Wetter.de, etc.
        Tasks:
            It can make a list of short- and long-term tasks, which should be completed. Tasks like timers / reminders should be global, but some are local per mode.
        Mood:
            The Agent should provide a mood every prompt, so it can interact with the User thoughtfully, happy, sad, etc.
            The Mood should be sent to the ESP32P4 to illuminate the LEDs accordingly.
            The Mood tool should decide which preset of animations should be used, so that the eye positions, displayed on the Robot's screen in the head can move to the person's direction etc. There are some presets saved on the ESP32P4's internal SD card.
        Vision:
            The AI gets a list of objects with positions proportional to the frame, every time it runs. So it can react to the current situation fast enough. Person names such as the face position are transmitted to the Agent as well.
        Audio Input:
            The audio input provides a situation awareness for people talking to the Robot. This audio is transcribed throughout the whole time, and is delivered to the AI Agent.
        Audio Output:
            The AI can use a tool to create sound files. This will be text to speech files for the most part, but it can also overwrite the file with files from the Internet. The sound engine is flexible and can handle multiple formats it can convert, to send over to the Robot.
    LLM:
        As LLM I want to use OLLAMA right now, but it should be easy to change in the future.

    Memory:
        The AI Agent uses multiple memory files, to remember tasks, make short and longterm tasks. It should remember interactions with different people as well.
