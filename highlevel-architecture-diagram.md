+-----------------------------+
|        User Browser         |
|  (Flask HTML UI + JS)       |
+-------------+---------------+
              |
              v
+-----------------------------+
|         Flask Server        |
|  - Routes                   |
|  - Renders UI               |
|  - Calls AI Agent           |
+-------------+---------------+
              |
              v
+-----------------------------+
|     AI Agent (Google ADK)   |
|  - Gemini model             |
|  - SQL Generator Tool       |
|  - POM API Tool             |
|  - Safety Rules             |
|  - Reasoning Workflow       |
+-------------+---------------+
              |
              v
+-----------------------------+
|         POM API             |
|  - Validates SQL            |
|  - Executes SQL on Oracle   |
|  - Returns JSON             |
+-------------+---------------+
              |
              v
+-----------------------------+
|        Oracle Database      |
+-----------------------------+
