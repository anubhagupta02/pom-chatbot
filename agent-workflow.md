User Query
   |
   v
Gemini LLM → Generate SQL
   |
   v
SQL Validator → Only SELECT, no harmful ops
   |
   v
POM API Tool → Execute SQL
   |
   v
Response Formatter → JSON table
   |
   v
Flask → UI
