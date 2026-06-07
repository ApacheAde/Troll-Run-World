================================================================================
                           TROLL RUN WORLD
================================================================================

A Mario-style endless runner game built in pure Python with Pygame.

Jump over mushrooms, collect coins, and run as far as you can with a cute troll!

--------------------------------------------------------------------------------
HOW TO PLAY
--------------------------------------------------------------------------------

Troll Run World is a side-scrolling endless runner.

- The troll runs forward automatically at all times.
- Mushrooms appear on the ground. You must jump over them to avoid getting hit.
- Gold coins appear in the air and on the ground — collect them for points.
- The game gets faster the longer you survive.
- If you hit a mushroom, the run ends.
- Your goal is to achieve the highest score possible.

Scoring:
- You earn points continuously based on distance traveled.
- Each coin collected adds a large bonus (80 points per coin).
- Final score = Distance points + (Coins × 80)

--------------------------------------------------------------------------------
CONTROLS
--------------------------------------------------------------------------------

JUMP
  - SPACEBAR
  - UP ARROW
  - W key

  You can perform a DOUBLE JUMP while in the air (press jump again before landing).

VARIABLE JUMP HEIGHT
  - Hold the jump button longer for a higher jump.
  - Release early for a shorter hop.

FAST FALL (while in the air)
  - DOWN ARROW or S key (optional — makes you fall faster)

OTHER CONTROLS
  - P          : Pause the game (during a run)
  - SPACE      : Start game from title screen / Restart after game over
  - Left Click : Also works for jump / start / restart
  - ESC        : Quit the game

--------------------------------------------------------------------------------
INSTALLATION INSTRUCTIONS
--------------------------------------------------------------------------------

Step 1: Make sure Python is installed
  - You need Python 3.8 or newer.
  - Check with: python --version   or   python3 --version

Step 2: Install Pygame (the only required library)

  Open a terminal / command prompt and run:

    pip install pygame

  If you get a "permission denied" or "externally-managed-environment" error on Linux, use:

    pip install --break-system-packages pygame

Step 3: Navigate to the game folder

    cd troll-run-world

Step 4: Run the game

    python troll_run_world.py

    or

    python3 troll_run_world.py

That's it! The game requires no additional assets, images, or sound files. Everything is generated in code.

--------------------------------------------------------------------------------
GAME FEATURES
--------------------------------------------------------------------------------

- Classic side-scrolling endless runner gameplay (Mario Run style)
- Smooth jumping with single jump + double jump support
- Variable jump height (hold vs tap)
- Procedurally generated mushrooms in three sizes (small, medium, tall)
- Collectible gold coins with spinning animation and particle effects
- Cute troll character with running and jumping animations
- Parallax scrolling background with hills, bushes, and clouds
- Progressive difficulty — the world speeds up over time
- Distance-based scoring + coin bonuses
- Persistent high score (saved automatically between sessions)
- Built-in sound effects (no external audio files needed)
- Clean title screen, pause screen, and game over screen
- Fully self-contained single Python file

--------------------------------------------------------------------------------
DETAILED GAMEPLAY INSTRUCTIONS
--------------------------------------------------------------------------------

Starting the Game:
- Launch the game.
- On the title screen, press SPACE, UP, W, or click the mouse to begin.

During a Run:
- The troll is always moving right.
- Time your jumps to clear mushrooms.
- Mushrooms come in singles and groups — learn the rhythm.
- Coins are often placed right after difficult sections. Try to grab them.
- Use your double jump wisely for tight gaps or to reach high coins.
- The longer you last, the faster the scrolling becomes.

When You Crash:
- The game ends when you touch a mushroom.
- Your final score and coin count are displayed.
- If you beat the high score, it will be saved automatically.
- Press SPACE or click to start a new run immediately.

Pausing:
- Press P at any time during a run to pause.
- Press P again to resume.

High Score:
- Your best score is saved in a file called:
    ~/.troll_run_highscore.json
- This file is created automatically the first time you beat a score.

--------------------------------------------------------------------------------
TIPS FOR HIGH SCORES
--------------------------------------------------------------------------------

1. Master the double jump — it is essential for surviving later sections.
2. Don't always jump at the last second. Sometimes jumping early gives you better positioning for the next obstacle.
3. Coins are worth a lot of points. It is often worth taking a small risk to collect a group of coins.
4. Groups of mushrooms require good timing. Try jumping for the first one and using the double jump for the second.
5. Stay calm when the speed increases. Small, controlled jumps are better than big panicked ones.
6. Use fast-fall (Down/S) only when you need to get back to the ground quickly after a high jump.

--------------------------------------------------------------------------------
PROJECT STRUCTURE
--------------------------------------------------------------------------------

troll-run-world/
│
├── troll_run_world.py    ← The complete game (single Python file)
├── requirements.txt      ← Lists the pygame dependency
├── README.txt            ← This file (full instructions)
│
└── (no other files needed)

The entire game is contained in one .py file. There are no image files, sound files, or additional folders required.

--------------------------------------------------------------------------------
REQUIREMENTS
--------------------------------------------------------------------------------

- Python 3.8 or higher
- Pygame 2.5 or higher

To install the required library:

    pip install pygame

On some systems:

    pip install --break-system-packages pygame

--------------------------------------------------------------------------------
TROUBLESHOOTING
--------------------------------------------------------------------------------

"ModuleNotFoundError: No module named 'pygame'"
  → Run: pip install pygame

"externally-managed-environment" error (Linux)
  → Run: pip install --break-system-packages pygame

Game window does not appear
  → Make sure you are running the command from inside the troll-run-world folder.

Sound is not working
  → Sound is optional. The game will still run without audio.

High score not saving
  → The game needs permission to write a small file in your home folder.

--------------------------------------------------------------------------------
CONTROLS QUICK REFERENCE
--------------------------------------------------------------------------------

Title Screen:
  SPACE / UP / W / Mouse Click  → Start game

In-Game:
  SPACE / UP / W                → Jump (and Double Jump)
  DOWN / S                      → Fast fall (in air)
  P                             → Pause / Unpause

Game Over Screen:
  SPACE / Mouse Click           → Restart run

Anytime:
  ESC                           → Quit game

--------------------------------------------------------------------------------
CREDITS & LICENSE
--------------------------------------------------------------------------------

Troll Run World
A standalone Python game project.

Made for fun and learning. You are free to play, modify, and share this game.

Run far. Jump high. Watch out for the mushrooms!

                                        🧌  🍄  🪙  🧌

================================================================================
