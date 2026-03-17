┌──────────────────────────────────────────────────────────────┐
│                          User Browser                         │
│                (HTML UI served by Flask)                      │
└───────────────▲───────────────────────────────────────────────┘
                │ 1. User enters natural language query
                │
┌───────────────┴───────────────────────────────────────────────┐
│                         Flask Backend                          │
│  - Receives query                                              │
│  - Sends to AI agent                                           │
│  - Renders results                                             │
└───────────────▲───────────────────────────────────────────────┘
                │ 2. Send query to AI Agent
                │
┌───────────────┴───────────────────────────────────────────────┐
│                     AI Agent (Google ADK)                      │
│  - Gemini model                                                │
│  - SQL generator tool                                          │
│  - SQL safety validator                                        │
│  - POM API caller tool                                         │
│  - Workflow orchestration                                      │
└───────────────▲───────────────────────────────────────────────┘
                │ 3. Agent generates SQL
                │ 4. Agent calls POM API
                │
┌───────────────┴───────────────────────────────────────────────┐
│                           POM API                              │
│  - Validates SQL                                               │
│  - Executes SQL on Oracle                                      │
│  - Returns JSON                                                │
└───────────────▲───────────────────────────────────────────────┘
                │ 5. SQL execution
                │
┌───────────────┴───────────────────────────────────────────────┐
│                        Oracle Database                         │
└────────────────────────────────────────────────────────────────┘
