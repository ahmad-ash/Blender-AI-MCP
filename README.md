````markdown
# Blender Claude MCP

A MCP server add-on for Blender that enables programmatic control of Blender via AI agents (such as Claude Desktop) by accepting structured JSON commands.

Created by [Ahmad Ashfaq](www.linkedin.com/in/ahmad-ashfaq1), this tool acts as a **Model Context Protocol (MCP)** bridge between Blender and external AI models for 3D Model generation.

✨ Features

- 🚀 Start/Stop MCP server inside Blender
- 📦 Create 3D primitives: cubes, spheres, cylinders
- 🧼 Clean entire scene or any specific Model with one command
- 🔎 Query scene info including objects and active scene

🧰 Tech Stack

- Blender
- **bpy API**
- AI client tested with **Claude (Anthropic)

🧪 Installation

1. Download this Blendermcp1.py file.
2. Open Blender.
3. Go to `Edit > Preferences > Add-ons`.
4. Click "Install from disk", and select the downloaded `.py` file.
5. Enable the add-on: “Ahmad's Claude MCP”. from the side panel
6. Access it in the 3D Viewport: **Sidebar > BlenderMCP**.


🧠 How It Works

Once activated, the plugin starts a minimal MCP server on `localhost:9876`. AI models (like Claude or GPT) can be prompted to Build models in blender


📽️ Demo

A full demo of Claude building objects in Blender using just natural language has been recorded. [**Watch here**](#) *(Link to be added once uploaded)*


🧑‍💻 Commands Supported

| Command Type      | Description                      |
| ----------------- | -------------------------------- |
| `get_scene_info`  | Returns scene name & object list |
| `create_cube`     | Adds a cube                      |
| `create_sphere`   | Adds a UV sphere                 |
| `create_cylinder` | Adds a cylinder                  |
| `clean_scene`     | Deletes all objects              |
| `execute_code`    | Runs Python code safely          |
