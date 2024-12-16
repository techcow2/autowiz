# AppWiz

<img src="https://github.com/user-attachments/assets/badbf49d-9ded-43c7-bcba-5929b2ffd5fc" alt="Resized Banner" width="600">

<p>&nbsp;</p>

iz is a powerful and user-friendly automation tool designed to record and playback your keyboard and mouse actions with precision and ease. Whether you're looking to automate repetitive tasks, create macros, or streamline your workflow, iz has got you covered.

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Hotkeys](#hotkeys)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Record Keyboard and Mouse Actions:** Capture all your keyboard presses and mouse movements, clicks, and scrolls.
- **Playback with Adjustable Speed:** Play back your recordings at your preferred speed, from half-speed to double-speed.
- **Loop Playback:** Enable continuous playback of your recordings until you decide to stop.
- **Save and Manage Recordings:** Easily save your recordings, load existing ones, and delete unwanted recordings.
- **Compact and Regular Modes:** Toggle between a detailed interface and a streamlined compact mode for convenience.
- **Always on Top:** Keep iz visible on your screen by enabling the "Always on Top" feature.
- **Visual Status Indicators:** Stay informed about the current state of iz with color-coded status indicators and progress bars.
- **Help and About Sections:** Access comprehensive help documentation and information about AppWiz directly within the application.
- **Disclaimer Agreement:** A built-in disclaimer ensures users are informed about responsible usage.

## Demo
(coming soon)

## Installation

### Prerequisites

- **Python 3.7 or higher**: Ensure you have Python installed on your system. You can download it from [python.org](https://www.python.org/downloads/).

### Steps

1. **Clone the Repository**

   Navigate to your desired directory and clone the AppWiz repository:

   ```bash
   git clone https://github.com/techcow2/appwiz.git
   ```

2. **Navigate to the Directory**

   ```bash
   cd AppWiz
   ```

3. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv venv
   ```

4. **Activate the Virtual Environment**

   - **Windows:**

     ```bash
     venv\Scripts\activate
     ```

   - **macOS and Linux:**

     ```bash
     source venv/bin/activate
     ```

5. **Install Required Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run iz**

   ```bash
   python iz.py
   ```

2. **Recording Actions**

   - Click the **Record** button or press the **R** key to start recording your keyboard and mouse actions.
   - Perform the actions you wish to automate.
   - Press the **ESC** key to stop recording.

3. **Playing Back Actions**

   - Select a saved recording from the dropdown menu.
   - Click the **Play** button to start playback.
   - Adjust the **Playback Speed** slider to your desired speed.
   - Enable or disable **Loop Playback** as needed.
   - Click the **Stop** button or press the **ESC** key to halt playback.

4. **Managing Recordings**

   - **Save Recording:** After recording, click **Save Recording** to name and store your actions.
   - **Load Recording:** Select a recording from the dropdown and click **Load Recording** to prepare it for playback.
   - **Delete Recording:** Remove unwanted recordings by selecting them and clicking **Delete Recording**.

5. **Additional Features**

   - **Compact Mode:** Toggle between regular and compact interfaces for a streamlined experience.
   - **Always on Top:** Keep iz visible above other windows by enabling this feature.
   - **Help and About:** Access detailed help documentation and information about iz through the respective buttons.

## Configuration

iz stores its configurations and recordings in the following directories:

- **Recordings Directory:** `recordings/`
- **Configuration File:** `config.json`

Ensure these files and directories are present in the root directory of the application. The application will automatically create the `recordings` directory if it doesn't exist.

## Hotkeys

iz supports global hotkeys for enhanced convenience:

- **Start Recording:** Press **R**
- **Stop Recording or Playback:** Press **ESC**

*Note:* Ensure that iz is running and has the necessary permissions to capture global hotkeys.

## Screenshots

### Regular Mode

<img src="https://github.com/user-attachments/assets/84ca5533-2f70-4809-b5bb-7bd08e11a693" alt="Regular Mode" width="600">


### Compact Mode


<img src="https://github.com/user-attachments/assets/4aa83bdf-a490-47af-879a-a58d1ac1f3d8" alt="Compact Mode" width="600">


### Recording Status

<img src="https://github.com/user-attachments/assets/ed99db79-e1f4-4d85-944a-6e0c5e9e5a95" alt="Recording Status" width="600">


## Contributing

Contributions are what make the open-source community thrive! We appreciate any contributions you make to iz.

### Steps to Contribute

1. **Fork the Repository**

   Click the **Fork** button at the top right of this page.

2. **Clone Your Fork**

   ```bash
   git clone https://github.com/techcow2/appwiz.git
   ```

3. **Create a New Branch**

   ```bash
   git checkout -b feature/YourFeatureName
   ```

4. **Make Your Changes**

   Implement your feature or bug fix.

5. **Commit Your Changes**

   ```bash
   git commit -m "Add Your Feature"
   ```

6. **Push to Your Fork**

   ```bash
   git push origin feature/YourFeatureName
   ```

7. **Open a Pull Request**

   Navigate to the original repository and click **New Pull Request**.

### Guidelines

- Follow the existing code style and conventions.
- Ensure that your code is well-documented.
- Test your changes thoroughly before submitting.

## License

Distributed under the [MIT License](https://opensource.org/licenses/MIT). See `LICENSE` for more information.

## Contact

Have questions or need support? Open an issue!

- **Website:** [www.techray.dev](https://www.techray.dev)


---

*© 2024 TechRayApps LLC. All rights reserved.*

---

**Disclaimer:** iz is intended for legitimate and ethical use only. Users are responsible for ensuring that their use of iz complies with all applicable laws and regulations. The developers are not liable for any misuse or damages resulting from the use of this software.
